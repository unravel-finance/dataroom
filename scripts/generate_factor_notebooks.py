"""Generate (and optionally execute) the factor notebooks from the catalog.

    python -m scripts.generate_factor_notebooks            # write + convert
    python -m scripts.generate_factor_notebooks --execute  # also run them
    python -m scripts.generate_factor_notebooks altair     # one factor

``--execute`` needs ``UNRAVEL_API_KEY`` (wired from repo secrets in CI).
"""

from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.factors_catalog import Factor, load_factors

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
SRC_DIR = NOTEBOOKS_DIR / "src"
# 00_ prefix sorts the cross-factor overview above every factor_analysis_*.
CORRELATION_STEM = "00_factor_returns_correlation"

# Resolves `import analysis` / `scripts.factors_catalog` from wherever the
# notebook runs (notebooks/ under Jupyter, repo root under nbconvert).
_PATH_BOOTSTRAP = '''import sys
from pathlib import Path

_repo_root = Path.cwd()
while not (_repo_root / "analysis").is_dir() and _repo_root != _repo_root.parent:
    _repo_root = _repo_root.parent
sys.path.insert(0, str(_repo_root))
'''

_GENERATED_BANNER = (
    "# AUTO-GENERATED from scripts/factors_catalog.py by\n"
    "# scripts/generate_factor_notebooks.py -- do not edit by hand.\n"
)

_FACTOR_TEMPLATE = '''# %%
{banner}
{bootstrap}
from unravel_client import (
    get_historical_universe,
    get_portfolio_factors_historical,
    get_prices,
    get_tickers,
)

from analysis.alphalens import factor_analysis
from analysis.utils import get_env

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")

# {name} -- portfolio {portfolio_id}
portfolio = "{id}"
universe_size = "{universe}"

available_tickers = get_tickers(
    id=portfolio,
    api_key=UNRAVEL_API_KEY,
    universe_size=universe_size,
    exchange=None,
)
historical_factors = get_portfolio_factors_historical(
    id=portfolio, tickers=available_tickers, api_key=UNRAVEL_API_KEY
)
underlying = get_prices(tickers=available_tickers, api_key=UNRAVEL_API_KEY)

# Mask the raw factor with the dynamic point-in-time universe (a boolean
# dates x tickers matrix) so AlphaLens scores only the universe we trade,
# not every ticker that was ever tradeable.
universe = get_historical_universe(
    size=universe_size,
    api_key=UNRAVEL_API_KEY,
    start_date=str(historical_factors.index.min().date()),
    end_date=str(historical_factors.index.max().date()),
)
membership = (
    universe.reindex(index=historical_factors.index)
    .ffill()
    .reindex(columns=historical_factors.columns)
    .fillna(False)
    .astype(bool)
)
restricted_factors = historical_factors.where(membership)

columns_intersection = restricted_factors.columns.intersection(underlying.columns)
factor_analysis(restricted_factors[columns_intersection], underlying)

# %%
'''

_CORRELATION_TEMPLATE = '''# %%
{banner}
{bootstrap}
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from unravel_client import get_portfolio_returns

from analysis.utils import get_env
from scripts.factors_catalog import load_factors

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")

portfolios = [factor.portfolio_id for factor in load_factors()]

returns_df = pd.DataFrame(
    {{
        portfolio: get_portfolio_returns(id=portfolio, api_key=UNRAVEL_API_KEY)
        for portfolio in portfolios
    }}
)

# %%

correlation_matrix = returns_df.corr()

plt.figure(figsize=(16, 13))
sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap="coolwarm",
    center=0,
    square=True,
    fmt=".2f",
    cbar_kws={{"shrink": 0.8}},
)
plt.title("Cross-Sectional Returns Correlation Matrix")
plt.tight_layout()
plt.show()

# %%
'''


def _write(path: Path, content: str) -> None:
    path.write_text(content)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def _readme(factors: list[Factor]) -> str:
    rows = "\n".join(
        f"| [{f.name}](factor_analysis_{f.id}.ipynb) "
        f"| {f.category or '—'} "
        f"| {f.short_description} |"
        for f in factors
    )
    return (
        "<!-- AUTO-GENERATED from scripts/factors_catalog.py -- do not edit. -->\n\n"
        "# Factor Analysis Notebooks\n\n"
        "AlphaLens factor analysis for every Unravel single-factor portfolio, "
        "run on the **dynamic, point-in-time universe** (not every ticker ever "
        "tradeable). Open any notebook below — GitHub renders them inline.\n\n"
        f"### [Cross-factor returns correlation]({CORRELATION_STEM}.ipynb)\n\n"
        "Correlation heatmap across every portfolio's returns — start here for "
        "the big picture.\n\n"
        "### Per-factor analysis\n\n"
        "| Factor | Category | What it captures |\n"
        "| --- | --- | --- |\n"
        f"{rows}\n\n"
        "---\n\n"
        "_The jupytext sources live in [`src/`](src/); the notebooks here are "
        "generated and executed by the **Generate Notebooks** CI workflow._\n"
    )


def write_scripts(factors: list[Factor]) -> list[Path]:
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for factor in factors:
        path = SRC_DIR / f"factor_analysis_{factor.id}.py"
        _write(
            path,
            _FACTOR_TEMPLATE.format(
                banner=_GENERATED_BANNER.rstrip(),
                bootstrap=_PATH_BOOTSTRAP,
                name=factor.name,
                portfolio_id=factor.portfolio_id,
                id=factor.id,
                universe=factor.default_universe,
            ),
        )
        written.append(path)

    # The correlation notebook and README index always cover the full
    # catalog, regardless of any per-factor subset passed on argv.
    corr_path = SRC_DIR / f"{CORRELATION_STEM}.py"
    _write(
        corr_path,
        _CORRELATION_TEMPLATE.format(
            banner=_GENERATED_BANNER.rstrip(),
            bootstrap=_PATH_BOOTSTRAP,
        ),
    )
    written.append(corr_path)

    _write(NOTEBOOKS_DIR / "README.md", _readme(load_factors()))
    return written


def prune_stale(keep: set[str]) -> None:
    """Delete managed notebooks no longer in the catalog (e.g. blacklisted),
    so a full regen is authoritative. Only touches files we generate."""
    managed = list(NOTEBOOKS_DIR.glob("factor_analysis_*.ipynb"))
    managed += list(SRC_DIR.glob("factor_analysis_*.py"))
    managed += [NOTEBOOKS_DIR / f"{CORRELATION_STEM}.ipynb"]
    managed += [SRC_DIR / f"{CORRELATION_STEM}.py"]
    for path in managed:
        if path.exists() and path.stem not in keep:
            path.unlink()
            print(f"  pruned {path.relative_to(REPO_ROOT)}")


# Gitignored; uploaded as a CI artefact so it never lands in notebooks/.
CI_ARTIFACTS = REPO_ROOT / "ci-artifacts"
LOGS_DIR = CI_ARTIFACTS / "execution_logs"
REPORT = CI_ARTIFACTS / "execution_report.md"


def _job_count(default: int = 4) -> int:
    raw = os.environ.get("NOTEBOOK_JOBS", "").strip()
    if not raw:
        return default
    try:
        return max(int(raw), 1)
    except ValueError:
        return default


def _run(cmd: list[str]) -> tuple[bool, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")


def process(py_file: Path, do_execute: bool) -> tuple[str, bool, str]:
    """Convert (and optionally execute) one notebook. Never raises; output is
    aggregated into the report so a failing CI run stays diagnosable."""
    stem = py_file.stem
    ipynb = NOTEBOOKS_DIR / f"{stem}.ipynb"

    ok, output = _run(
        ["jupytext", "--to", "notebook", "--output", str(ipynb), str(py_file)]
    )
    if not ok:
        return stem, False, output
    if not do_execute:
        print(f"  converted {ipynb.name}")
        return stem, True, ""

    print(f"  converting + executing {ipynb.name} ...")
    ok, output = _run(
        [
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            # jupytext does not embed a kernelspec, so pin one explicitly.
            "--ExecutePreprocessor.kernel_name=python3",
            "--ExecutePreprocessor.timeout=1800",
            str(ipynb),
        ]
    )
    if not ok:
        (LOGS_DIR / f"{stem}.log").write_text(output)
        print(f"  FAILED {stem} -- see ci-artifacts/execution_logs/{stem}.log")
    else:
        print(f"  OK {stem}")
    return stem, ok, output


def main(argv: list[str]) -> None:
    do_execute = "--execute" in argv
    wanted = [a for a in argv if not a.startswith("--")]

    factors = load_factors()
    if wanted:
        selected = [f for f in factors if f.id in set(wanted)]
        missing = set(wanted) - {f.id for f in selected}
        if missing:
            raise SystemExit(f"Unknown factor ids: {sorted(missing)}")
        factors = selected

    print(f"Generating notebooks for {len(factors)} factor(s):")
    scripts = write_scripts(factors)

    if not wanted:  # full regen is authoritative -- drop anything stale
        prune_stale({p.stem for p in scripts})

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    jobs = min(_job_count(), len(scripts))
    verb = "Converting + executing" if do_execute else "Converting"
    print(f"{verb} {len(scripts)} notebook(s) with {jobs} worker(s):")

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        results = list(pool.map(lambda p: process(p, do_execute), scripts))

    failures = [
        (stem, "\n".join(out.strip().splitlines()[-60:]))
        for stem, ok, out in sorted(results)
        if not ok
    ]

    if do_execute:
        lines = [
            "# Notebook execution report",
            "",
            f"Total: {len(results)} | "
            f"Passed: {len(results) - len(failures)} | "
            f"Failed: {len(failures)}",
            "",
        ]
        for name, tail in failures:
            lines += [f"## {name}", "", "```", tail, "```", ""]
        REPORT.write_text("\n".join(lines) + "\n")
        print(f"Wrote {REPORT.relative_to(REPO_ROOT)}")

    if failures:
        raise SystemExit(
            f"{len(failures)} notebook(s) failed: {[n for n, _ in failures]}"
        )

    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
