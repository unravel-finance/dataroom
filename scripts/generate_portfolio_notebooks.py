"""Generate per-portfolio replication notebooks.

Usage:
    python -m scripts.generate_portfolio_notebooks             # all
    python -m scripts.generate_portfolio_notebooks spectra     # one
    python -m scripts.generate_portfolio_notebooks --execute   # also run

For each portfolio in ``scripts.portfolios_catalog``, this script:

1. Picks the right template:
   * **non-adaptive** → ``notebooks/00_multi_factor_portfolio_construction.ipynb``
     (multi-factor blend + backtest, parametrised by ``factors``)
   * **adaptive** → ``notebooks/00_adaptive-portfolios.ipynb``
     (fetches the live, pre-blended weights for the *base* (non-adaptive)
     portfolio, multiplies them by ``crypto_trend_consensus``, backtests
     both — reproduces the Adaptive variant)
2. Substitutes the parametrised cell so the notebook reproduces *that
   specific* live Unravel portfolio.
3. Updates the intro markdown (factor list, when applicable).
4. Writes ``notebooks/portfolio_replication_<id>.ipynb``.
5. (Optional, with ``--execute``) re-runs the notebook so committed
   outputs match the substituted parameters.

Mirrors ``scripts.generate_factor_notebooks`` in spirit (per-asset
notebooks, README table updates, optional execution) but works at the
.ipynb level instead of jupytext-from-.py — the template carries
markdown + image cells we don't want to round-trip through .py.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts._common import (
    UnknownPortfolios,
    get_api_key,
    job_count,
    select_portfolios,
)
from scripts.portfolios_catalog import Portfolio, load_portfolios

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
MULTI_FACTOR_TEMPLATE_NB = (
    NOTEBOOKS_DIR / "00_multi_factor_portfolio_construction.ipynb"
)
ADAPTIVE_TEMPLATE_NB = NOTEBOOKS_DIR / "00_adaptive-portfolios.ipynb"

_GENERATED_BANNER_MD = (
    "> ⚙️ **Auto-generated** — this notebook was produced by "
    "`scripts/generate_portfolio_notebooks.py` from `{template}`. "
    "The parameters below are the live composition of the {name} "
    "portfolio (`{portfolio_id}`) on unravel.finance. Edit the "
    "parameters cell to customise; rerun the script to regenerate "
    "from the template."
)

# Regex over a single code-cell's joined source. Captures the literal
# ``factors = [ … ]`` assignment so we can swap the list contents while
# keeping surrounding code untouched.
_FACTORS_BLOCK_RE = re.compile(
    r"factors\s*=\s*\[[^\]]*\]",
    re.DOTALL,
)

# Matches the "Fetching historical (raw) factor data" intro: the
# "consists of N proprietary cross-sectional factors:" sentence plus the
# bulleted factor list right after it. The bullets follow Markdown link
# syntax pointing at unravel.finance/portfolio/<id>; we substitute the
# whole block (heading sentence + bullets) per portfolio.
_FACTOR_LIST_RE = re.compile(
    r"The portfolio consists of \d+ proprietary cross-sectional factors:\n"
    r"((?:- \[[^\]]+\]\([^)]+\)\n?)+)",
)


def _factors_assignment(portfolio: Portfolio) -> str:
    """Render the ``factors = [...]`` list as the template formats it
    (one id per line, trailing comma) so the diff stays minimal."""
    body = "".join(f'    "{fid}",\n' for fid in portfolio.component_ids)
    return f"factors = [\n{body}]"


def _factor_list_markdown(portfolio: Portfolio) -> str:
    """Build the "consists of N factors: [bullets]" block for the
    portfolio's actual components. Resolves IDs to names via
    factors_catalog so the bullet labels match the live site."""
    from scripts.factors_catalog import find_factor

    factors = [find_factor(fid) for fid in portfolio.component_ids]
    bullets = "\n".join(
        f"- [{f.name}](https://unravel.finance/portfolio/{f.portfolio_id})"
        for f in factors
    )
    return (
        f"The portfolio consists of {len(factors)} proprietary "
        f"cross-sectional factors:\n{bullets}\n"
    )


def _src_to_string(source) -> str:
    return "".join(source) if isinstance(source, list) else source


def _string_to_src(text: str) -> list[str]:
    """Notebook JSON convention: source is a list of strings, each
    line including its trailing newline (last line may omit it)."""
    if not text:
        return []
    parts = text.splitlines(keepends=True)
    return parts


def _substitute_factors(cell: dict, portfolio: Portfolio) -> bool:
    """If the cell defines ``factors = [...]``, swap it for the
    portfolio's. Returns True if it did."""
    if cell.get("cell_type") != "code":
        return False
    src_text = _src_to_string(cell.get("source", ""))
    if "factors = [" not in src_text:
        return False
    new_src = _FACTORS_BLOCK_RE.sub(_factors_assignment(portfolio), src_text, count=1)
    cell["source"] = _string_to_src(new_src)
    return True


def _substitute_factor_list_markdown(cell: dict, portfolio: Portfolio) -> bool:
    """If the markdown cell carries the template's hardcoded
    "consists of N factors: [bullets]" block, rewrite it with the
    portfolio's actual components. Without this the rendered intro
    above the factor-fetching cell describes whatever portfolio the
    template was last edited against, not the one this notebook
    actually backtests."""
    if cell.get("cell_type") != "markdown":
        return False
    src_text = _src_to_string(cell.get("source", ""))
    if "The portfolio consists of" not in src_text:
        return False
    new_src, n = _FACTOR_LIST_RE.subn(
        _factor_list_markdown(portfolio),
        src_text,
        count=1,
    )
    if n == 0:
        return False
    cell["source"] = _string_to_src(new_src)
    return True


def _clear_outputs(nb: dict) -> None:
    """Strip cached outputs from every code cell. The template carries
    the execution outputs of whichever portfolio it was last run
    against (currently a Spectra-ish 4-factor composition), so without
    this step every generated notebook would render the *template's*
    backtest plots — the equity curve, the heatmap, the IC — regardless
    of which factors it actually substituted in. ``--execute`` refills
    them with the right outputs; otherwise the cells render empty,
    which is the truthful state for a notebook that hasn't run yet."""
    for cell in nb["cells"]:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None


# Adaptive notebooks parametrise a single `factor = "..."` assignment
# that's concatenated with ".40" to form the portfolio id passed to
# `get_portfolio_historical_weights`. We swap the literal so the
# generated notebook fetches the *base* (non-adaptive) sibling's
# pre-blended weights and overlays `crypto_trend_consensus` — which IS
# the Adaptive construction.
_ADAPTIVE_FACTOR_RE = re.compile(r'factor\s*=\s*"[^"]*"')


def _adaptive_base_id(portfolio: Portfolio) -> str:
    """Return the id of the non-adaptive sibling whose weights the
    adaptive template should fetch (e.g. ``spectra_adaptive`` →
    ``spectra``). The adaptive variants in the catalog are all named
    ``<base>_adaptive`` — this enforces that invariant rather than
    silently picking up a malformed id."""
    if not portfolio.id.endswith("_adaptive"):
        raise RuntimeError(
            f"Adaptive portfolio id {portfolio.id!r} does not follow the "
            "expected `<base>_adaptive` convention — adaptive template "
            "parametrisation needs the base id to substitute."
        )
    return portfolio.id[: -len("_adaptive")]


def _substitute_adaptive_factor(cell: dict, base_id: str) -> bool:
    """For adaptive template: swap the parameters cell's
    ``factor = "..."`` literal with the non-adaptive base id. Returns
    True if substituted."""
    if cell.get("cell_type") != "code":
        return False
    src_text = _src_to_string(cell.get("source", ""))
    if "factor =" not in src_text and "factor=" not in src_text:
        return False
    new_src, n = _ADAPTIVE_FACTOR_RE.subn(
        f'factor = "{base_id}"', src_text, count=1
    )
    if n == 0:
        return False
    cell["source"] = _string_to_src(new_src)
    return True


def _inject_banner(nb: dict, portfolio: Portfolio, template_name: str) -> None:
    """Insert a 'this is auto-generated' markdown banner directly after
    the cover/intro cell, so it's the first thing readers see."""
    banner_cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": _string_to_src(
            _GENERATED_BANNER_MD.format(
                name=portfolio.name,
                portfolio_id=portfolio.portfolio_id,
                template=template_name,
            )
        ),
    }
    nb["cells"].insert(1, banner_cell)


def _render_multi_factor(portfolio: Portfolio) -> dict:
    """Multi-factor construction path: swap the ``factors = [...]``
    cell and the "consists of N factors" markdown block."""
    nb = json.loads(MULTI_FACTOR_TEMPLATE_NB.read_text())
    factors_swapped = False
    markdown_swapped = False
    for cell in nb["cells"]:
        if not factors_swapped and _substitute_factors(cell, portfolio):
            factors_swapped = True
        if not markdown_swapped and _substitute_factor_list_markdown(
            cell, portfolio
        ):
            markdown_swapped = True
        if factors_swapped and markdown_swapped:
            break
    if not factors_swapped:
        raise RuntimeError(
            "Multi-factor template's `factors = [...]` cell not found — "
            "has the construction notebook changed shape?"
        )
    if not markdown_swapped:
        print(
            "  ! factor-list markdown block not found — intro copy may not "
            "match the portfolio's composition"
        )
    return nb


def _render_adaptive(portfolio: Portfolio) -> dict:
    """Adaptive path: load 00_adaptive-portfolios.ipynb and swap the
    `factor = "..."` parameter so it points at the non-adaptive base
    (e.g. ``spectra`` for ``spectra_adaptive``). The template's
    existing logic — fetch historical weights, fetch overlay, multiply,
    backtest with-and-without — then reproduces the Adaptive variant."""
    nb = json.loads(ADAPTIVE_TEMPLATE_NB.read_text())
    base_id = _adaptive_base_id(portfolio)
    factor_swapped = False
    for cell in nb["cells"]:
        if _substitute_adaptive_factor(cell, base_id):
            factor_swapped = True
            break
    if not factor_swapped:
        raise RuntimeError(
            "Adaptive template's `factor = \"...\"` parameter cell not "
            "found — has 00_adaptive-portfolios.ipynb changed shape?"
        )
    return nb


def render_notebook(portfolio: Portfolio) -> Path:
    """Materialise the per-portfolio notebook on disk. Returns the
    output path. Dispatches between the multi-factor construction
    template (non-adaptive) and the adaptive-portfolios template
    (adaptive) based on ``portfolio.is_adaptive``."""
    if portfolio.is_adaptive:
        if not ADAPTIVE_TEMPLATE_NB.exists():
            raise FileNotFoundError(
                f"Adaptive template missing: "
                f"{ADAPTIVE_TEMPLATE_NB.relative_to(REPO_ROOT)}"
            )
        nb = _render_adaptive(portfolio)
        template_name = ADAPTIVE_TEMPLATE_NB.name
    else:
        if not MULTI_FACTOR_TEMPLATE_NB.exists():
            raise FileNotFoundError(
                f"Multi-factor template missing: "
                f"{MULTI_FACTOR_TEMPLATE_NB.relative_to(REPO_ROOT)}"
            )
        nb = _render_multi_factor(portfolio)
        template_name = MULTI_FACTOR_TEMPLATE_NB.name

    _clear_outputs(nb)
    _inject_banner(nb, portfolio, template_name)

    out = NOTEBOOKS_DIR / f"portfolio_replication_{portfolio.id}.ipynb"
    out.write_text(json.dumps(nb, indent=1) + "\n")
    print(f"  wrote {out.relative_to(REPO_ROOT)}")
    return out


# ---- README portfolio-table update ------------------------------------------

README = REPO_ROOT / "README.md"
_TABLE_BEGIN = "<!-- BEGIN PORTFOLIO TABLE"
_TABLE_END = "<!-- END PORTFOLIO TABLE -->"


def _portfolio_table(portfolios: list[Portfolio]) -> str:
    rows = "\n".join(
        f"| [{p.name}]({p.detail_url}) "
        f"| [PDF](factsheets/{p.id}.pdf) "
        f"| [notebook](notebooks/portfolio_replication_{p.id}.ipynb) "
        f"| [CSV]({p.returns_csv_url}) |"
        for p in portfolios
    )
    return (
        "| Portfolio | Factsheet | Notebook | Portfolio returns |\n"
        "| --- | --- | --- | --- |\n"
        f"{rows}"
    )


def update_root_readme(portfolios: list[Portfolio]) -> None:
    """Replace the README's portfolio-table block in-place. No-op when
    the markers aren't present (lets the README drop the table without
    breaking this generator)."""
    if not README.exists():
        return
    text = README.read_text()
    try:
        begin_eol = text.index("\n", text.index(_TABLE_BEGIN)) + 1
        end = text.index(_TABLE_END, begin_eol)
    except ValueError:
        return
    README.write_text(
        text[:begin_eol] + _portfolio_table(portfolios) + "\n" + text[end:]
    )
    print("  updated README.md portfolio table")


# ---- optional execution -----------------------------------------------------

CI_ARTIFACTS = REPO_ROOT / "ci-artifacts"
LOGS_DIR = CI_ARTIFACTS / "execution_logs"


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def _execute_in_place(ipynb: Path) -> tuple[bool, str]:
    """Re-run the notebook in-place so committed outputs reflect the
    substituted parameters. Heavy (calls the Unravel API + renders
    matplotlib), so it's gated behind ``--execute``."""
    return _run(
        [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            "--ExecutePreprocessor.kernel_name=python3",
            "--ExecutePreprocessor.timeout=1800",
            str(ipynb),
        ]
    )


def process(portfolio: Portfolio, do_execute: bool) -> tuple[str, bool, str]:
    """Render (and optionally execute) one portfolio's notebook. Never
    raises — failures are aggregated into the CI report."""
    try:
        ipynb = render_notebook(portfolio)
    except Exception as exc:  # noqa: BLE001
        return portfolio.id, False, f"render failed: {exc}"
    if not do_execute:
        return portfolio.id, True, ""

    print(f"  executing {ipynb.name} ...")
    ok, output = _execute_in_place(ipynb)
    if not ok:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        (LOGS_DIR / f"portfolio_replication_{portfolio.id}.log").write_text(output)
        print(
            f"  FAILED {portfolio.id} — see ci-artifacts/execution_logs/"
            f"portfolio_replication_{portfolio.id}.log"
        )
    else:
        print(f"  OK {portfolio.id}")
    return portfolio.id, ok, output


# ---- pruning ----------------------------------------------------------------


def prune_stale(keep: set[str]) -> None:
    """Drop any portfolio_replication_*.ipynb whose id is no longer in
    the catalog. Only touches files we generate."""
    managed = list(NOTEBOOKS_DIR.glob("portfolio_replication_*.ipynb"))
    keep_stems = {f"portfolio_replication_{i}" for i in keep}
    for path in managed:
        if path.stem not in keep_stems:
            path.unlink()
            print(f"  pruned {path.relative_to(REPO_ROOT)}")


def main(argv: list[str]) -> int:
    do_execute = "--execute" in argv
    wanted = [a for a in argv if not a.startswith("--")]

    try:
        portfolios = select_portfolios(wanted)
    except UnknownPortfolios as exc:
        print(f"Unknown portfolio(s): {exc.args[0]}", file=sys.stderr)
        return 1

    if do_execute:
        # Fail fast if the API key is missing — execution would only
        # die later in jupyter nbconvert with a noisier traceback.
        get_api_key()

    print(f"Generating notebooks for {len(portfolios)} portfolio(s):")
    if not wanted:
        prune_stale({p.id for p in portfolios})

    workers = min(job_count(), len(portfolios)) or 1
    if workers <= 1 or not do_execute:
        # Rendering is fast and threads add no value; only worth a pool
        # when execution is happening too.
        results = [process(p, do_execute) for p in portfolios]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda p: process(p, do_execute), portfolios))

    # README table always reflects the full catalog.
    update_root_readme(load_portfolios())

    failures = [pid for pid, ok, _ in results if not ok]
    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
