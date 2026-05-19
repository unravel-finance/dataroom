"""Render a two-page PDF factsheet for each single-factor portfolio.

Usage:
    python -m scripts.generate_factsheets                  # all factors
    python -m scripts.generate_factsheets supply_velocity  # one factor
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
    get_historical_universe,
    get_portfolio_factors_historical,
    get_portfolio_returns,
    get_prices,
)

from scripts._common import (  # noqa: E402
    UnknownFactors,
    get_api_key,
    job_count,
    select_factors,
)
from scripts.factors_catalog import Factor  # noqa: E402
from scripts.factsheet import metrics  # noqa: E402
from scripts.factsheet.al_utils import clean_factor_data  # noqa: E402
from scripts.factsheet.page_one import render_page_one  # noqa: E402
from scripts.factsheet.page_two import render_page_two  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTSHEETS_DIR = REPO_ROOT / "factsheets"
# Per-factor page-2 (AlphaLens) thumbnail, referenced by the web app's
# "Factor Analysis" resource card.
PREVIEWS_DIR = REPO_ROOT / "previews"


def _fetch_factor_inputs(
    factor: Factor, api_key: str
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Fetch returns + factor data + prices, masked to the rolling Top-N
    universe (point-in-time, no look-ahead)."""
    template_id = factor.portfolio_id.split(".")[0]

    returns = get_portfolio_returns(id=factor.portfolio_id, api_key=api_key)
    returns = returns.dropna()
    returns.index = pd.to_datetime(returns.index)
    start_date = returns.index.min().strftime("%Y-%m-%d")
    end_date = returns.index.max().strftime("%Y-%m-%d")

    universe = get_historical_universe(
        size=factor.default_universe,
        start_date=start_date,
        end_date=end_date,
        api_key=api_key,
    )
    universe.index = pd.to_datetime(universe.index)
    tickers = list(universe.columns)

    factor_data = get_portfolio_factors_historical(
        id=template_id,
        tickers=tickers,
        api_key=api_key,
        start_date=start_date,
        end_date=end_date,
    )
    factor_data.index = pd.to_datetime(factor_data.index)
    factor_data = factor_data.where(
        universe.reindex(
            index=factor_data.index, columns=factor_data.columns
        ).astype("boolean")
    )

    prices = get_prices(
        tickers=tickers,
        api_key=api_key,
        start_date=start_date,
        end_date=end_date,
    )
    prices.index = pd.to_datetime(prices.index)
    return returns, factor_data, prices


def render_factsheet(factor: Factor, api_key: str) -> Path:
    print(f"[{factor.id}] {factor.name}")
    returns, factor_data, prices = _fetch_factor_inputs(factor, api_key)
    stats = metrics.compute_stats(returns)
    # Clean once, shared by both pages. Best-effort: page 1 skips its
    # top-right bars and page 2 falls back to its own error path.
    try:
        clean = clean_factor_data(factor_data, prices)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! clean_factor_data failed: {exc}")
        clean = None

    FACTSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    out = FACTSHEETS_DIR / f"{factor.id}.pdf"

    with PdfPages(out) as pdf:
        page1 = render_page_one(factor, returns, stats, clean)
        pdf.savefig(page1)
        plt.close(page1)

        page2 = render_page_two(factor, factor_data, prices)
        pdf.savefig(page2)
        # Page 2 (the AlphaLens analysis) doubles as the web resource-card
        # thumbnail — always factor-specific.
        page2.savefig(PREVIEWS_DIR / f"{factor.id}.png", dpi=150)
        plt.close(page2)

    print(f"  ✓ wrote {out.relative_to(REPO_ROOT)}")
    return out


def _render_safe(factor: Factor, api_key: str) -> tuple[str, str | None]:
    """Process-pool worker: render one factsheet, never raise."""
    try:
        render_factsheet(factor, api_key)
        return factor.id, None
    except Exception as exc:  # noqa: BLE001 — reported by the parent
        return factor.id, "".join(
            traceback.format_exception_only(type(exc), exc)
        ).strip()


def main(argv: list[str]) -> int:
    api_key = get_api_key()
    try:
        factors = select_factors(argv)
    except UnknownFactors as exc:
        print(f"Unknown factor(s): {exc.args[0]}", file=sys.stderr)
        return 1

    # Process-based (loky), NOT threads: pyplot's state machine isn't
    # thread-safe. Each worker renders one factsheet in its own interpreter.
    workers = min(job_count(), len(factors)) or 1
    if workers <= 1:
        results = [_render_safe(f, api_key) for f in factors]
    else:
        results = Parallel(n_jobs=workers, backend="loky")(
            delayed(_render_safe)(f, api_key) for f in factors
        )

    failures = []
    for factor_id, err in results:
        if err:
            failures.append(factor_id)
            print(f"  ✗ {factor_id} failed: {err}", file=sys.stderr)

    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
