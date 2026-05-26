"""Render a two-page PDF factsheet for each multi-factor portfolio.

Usage:
    python -m scripts.generate_portfolio_factsheets             # all portfolios
    python -m scripts.generate_portfolio_factsheets spectra     # one portfolio

Shares page 1 with the single-factor pipeline (the page_one renderer
branches on ``asset.is_multi_factor``); page 2 is portfolio-specific
(drawdown, monthly returns heatmap, rolling Sharpe, rolling gross
exposure) — see ``scripts.factsheet.page_two_portfolio``.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Headless backend — MUST be set before any pyplot import (incl. transitive
# via scripts.factsheet.*) so the joblib workers stay non-interactive.
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from joblib import Parallel, delayed  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from unravel_client import (  # noqa: E402
    get_portfolio_historical_weights,
    get_portfolio_returns,
)

from scripts._common import (  # noqa: E402
    UnknownPortfolios,
    get_api_key,
    job_count,
    select_portfolios,
)
from scripts.factsheet import metrics  # noqa: E402
from scripts.factsheet.page_one import render_page_one  # noqa: E402
from scripts.factsheet.page_two_portfolio import (  # noqa: E402
    charts_bbox,
    render_page_two,
)
from scripts.portfolios_catalog import Portfolio  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTSHEETS_DIR = REPO_ROOT / "factsheets"
# Per-portfolio page-2 thumbnail — matches the convention used by the
# single-factor pipeline so the web "Portfolio Analysis" card can render
# the same way regardless of asset type.
PREVIEWS_DIR = REPO_ROOT / "notebooks" / "preview"
README = REPO_ROOT / "README.md"
_TABLE_BEGIN = "<!-- BEGIN PORTFOLIO TABLE"
_TABLE_END = "<!-- END PORTFOLIO TABLE -->"


def _portfolio_table(portfolios: list[Portfolio]) -> str:
    rows = "\n".join(
        f"| [{p.name}]({p.detail_url}) "
        f"| [PDF](factsheets/{p.id}.pdf) "
        f"| [CSV]({p.returns_csv_url}) |"
        for p in portfolios
    )
    return (
        "| Portfolio | Factsheet | Portfolio returns |\n"
        "| --- | --- | --- |\n"
        f"{rows}"
    )


def update_root_readme(portfolios: list[Portfolio]) -> None:
    """Replace the README's portfolio table block in-place. No-op if the
    markers aren't present (allows the README to drop the table without
    breaking the generator)."""
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


def _fetch_portfolio_inputs(
    portfolio: Portfolio, api_key: str
) -> tuple[pd.Series, pd.DataFrame | None]:
    """Fetch returns + (best-effort) historical weights for the live portfolio.

    Weights are best-effort: a fetch failure still produces a factsheet,
    page 2's rolling-exposure panel just degrades to "Weights unavailable"."""
    returns = get_portfolio_returns(id=portfolio.portfolio_id, api_key=api_key)
    returns = returns.dropna()
    returns.index = pd.to_datetime(returns.index)

    start_date = returns.index.min().strftime("%Y-%m-%d")
    end_date = returns.index.max().strftime("%Y-%m-%d")

    weights: pd.DataFrame | None
    try:
        weights = get_portfolio_historical_weights(
            id=portfolio.portfolio_id,
            api_key=api_key,
            smoothing=None,
            start_date=start_date,
            end_date=end_date,
        )
        weights.index = pd.to_datetime(weights.index)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! historical weights fetch failed: {exc}")
        weights = None
    return returns, weights


def render_factsheet(portfolio: Portfolio, api_key: str) -> Path:
    print(f"[{portfolio.id}] {portfolio.name}")
    returns, weights = _fetch_portfolio_inputs(portfolio, api_key)
    stats = metrics.compute_stats(returns)

    FACTSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    out = FACTSHEETS_DIR / f"{portfolio.id}.pdf"

    with PdfPages(out) as pdf:
        # Page 1: shared renderer; pass clean=None to skip the AlphaLens
        # top-right quantile bars (irrelevant for multi-factor portfolios).
        page1 = render_page_one(portfolio, returns, stats, clean=None)
        pdf.savefig(page1)
        plt.close(page1)

        page2 = render_page_two(portfolio, returns, weights)
        pdf.savefig(page2)
        # Page 2 doubles as the web resource-card thumbnail — crop to just
        # the chart cluster so its aspect ratio matches the notebook-derived
        # cards beside it.
        crop = charts_bbox(page2)
        page2.savefig(
            PREVIEWS_DIR / f"{portfolio.id}.png",
            dpi=150,
            bbox_inches=crop if crop is not None else None,
        )
        plt.close(page2)

    print(f"  ✓ wrote {out.relative_to(REPO_ROOT)}")
    return out


def _render_safe(portfolio: Portfolio, api_key: str) -> tuple[str, str | None]:
    """Process-pool worker: render one factsheet, never raise."""
    try:
        render_factsheet(portfolio, api_key)
        return portfolio.id, None
    except Exception as exc:  # noqa: BLE001 — reported by the parent
        return portfolio.id, "".join(
            traceback.format_exception_only(type(exc), exc)
        ).strip()


def main(argv: list[str]) -> int:
    api_key = get_api_key()
    try:
        portfolios = select_portfolios(argv)
    except UnknownPortfolios as exc:
        print(f"Unknown portfolio(s): {exc.args[0]}", file=sys.stderr)
        return 1

    # Process-based (loky), NOT threads: pyplot's state machine isn't
    # thread-safe. Each worker renders one factsheet in its own interpreter.
    workers = min(job_count(), len(portfolios)) or 1
    if workers <= 1:
        results = [_render_safe(p, api_key) for p in portfolios]
    else:
        results = Parallel(n_jobs=workers, backend="loky")(
            delayed(_render_safe)(p, api_key) for p in portfolios
        )

    failures = []
    for portfolio_id, err in results:
        if err:
            failures.append(portfolio_id)
            print(f"  ✗ {portfolio_id} failed: {err}", file=sys.stderr)

    # README table always reflects the full catalog (regardless of any
    # per-portfolio subset passed on argv) so it stays authoritative.
    from scripts.portfolios_catalog import load_portfolios
    update_root_readme(load_portfolios())

    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
