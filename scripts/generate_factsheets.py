"""Render a two-page PDF factsheet for each single-factor portfolio.

Workflow:
    1. Pull the portfolio returns (for page 1's performance chart).
    2. Pull the raw factor data + underlying prices for the AlphaLens analysis
       on page 2.
    3. Combine both pages into one PDF per factor under factsheets/.

CSVs are exported as a side-effect (export_data does the same thing but we
re-fetch here so generating PDFs doesn't depend on the CSV step being run
first — useful when iterating locally).

Usage:
    python -m scripts.generate_factsheets                  # all factors
    python -m scripts.generate_factsheets supply_velocity  # one factor
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Headless, thread-/process-safe backend. MUST be set before any pyplot
# import (including the transitive ones via scripts.factsheet.*), otherwise
# the joblib workers can pick up an interactive backend.
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


def _fetch_factor_inputs(
    factor: Factor, api_key: str
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    """Fetch the inputs for the factsheet.

    The page-2 AlphaLens analysis (and the page-1 signal-quality bars) are
    run on the *rolling* Top-N universe — i.e. only the assets that were
    actually in the Top-N membership on each date, reconstructed
    point-in-time to avoid look-ahead bias. The raw, full-universe factor
    data is still exported to CSV separately by scripts.export_data, so the
    data-room CSV keeps the large universe.
    """
    template_id = factor.portfolio_id.split(".")[0]

    returns = get_portfolio_returns(id=factor.portfolio_id, api_key=api_key)
    returns = returns.dropna()
    returns.index = pd.to_datetime(returns.index)
    start_date = returns.index.min().strftime("%Y-%m-%d")
    end_date = returns.index.max().strftime("%Y-%m-%d")

    # Rolling Top-N universe membership: date × ticker, truthy where the
    # asset was a member on that date.
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
    # Mask to the rolling universe — values for assets outside the Top-N on
    # a given date become NaN and are dropped by AlphaLens.
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
    # Clean once, share with both pages — page 1 uses it for the top-right
    # signal-quality bar chart, page 2 uses it for the full AlphaLens panel
    # grid. Best-effort: if AlphaLens preparation fails the top-right bars
    # are skipped silently and page 2 falls back to its own error path.
    try:
        clean = clean_factor_data(factor_data, prices)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! clean_factor_data failed: {exc}")
        clean = None

    FACTSHEETS_DIR.mkdir(parents=True, exist_ok=True)
    out = FACTSHEETS_DIR / f"{factor.id}.pdf"

    with PdfPages(out) as pdf:
        page1 = render_page_one(factor, returns, stats, clean)
        pdf.savefig(page1)
        plt.close(page1)

        page2 = render_page_two(factor, factor_data, prices)
        pdf.savefig(page2)
        plt.close(page2)

    print(f"  ✓ wrote {out.relative_to(REPO_ROOT)}")
    return out


def _render_safe(factor: Factor, api_key: str) -> tuple[str, str | None]:
    """Process-pool worker: render one factsheet, never raise.

    Returns ``(factor_id, error_or_None)`` so the parent can aggregate
    failures the way the old sequential loop did.
    """
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

    # Process-based (loky) parallelism, NOT threads: matplotlib's pyplot
    # state machine (theme.new_page() → plt.figure()) is not thread-safe.
    # Each worker renders one factsheet in its own interpreter.
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
