"""Render a two-page PDF factsheet for each single-factor portfolio.

Workflow:
    1. Pull the portfolio returns (for page 1's performance chart).
    2. Pull the raw factor data + underlying prices for the AlphaLens analysis
       on page 2.
    3. Combine both pages into one PDF per factor under data/factsheets/.

CSVs are exported as a side-effect (export_data does the same thing but we
re-fetch here so generating PDFs doesn't depend on the CSV step being run
first — useful when iterating locally).

Usage:
    python -m scripts.generate_factsheets                  # all factors
    python -m scripts.generate_factsheets supply_velocity  # one factor
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from unravel_client import (
    get_portfolio_factors_historical,
    get_portfolio_returns,
    get_prices,
    get_tickers,
)

from scripts.factors_catalog import Factor, load_factors
from scripts.factsheet import metrics
from scripts.factsheet.al_utils import clean_factor_data
from scripts.factsheet.page_one import render_page_one
from scripts.factsheet.page_two import render_page_two

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTSHEETS_DIR = REPO_ROOT / "data" / "factsheets"


def _get_api_key() -> str:
    key = os.environ.get("UNRAVEL_API_KEY")
    if not key:
        raise RuntimeError("UNRAVEL_API_KEY environment variable is not set")
    return key


def _fetch_factor_inputs(
    factor: Factor, api_key: str
) -> tuple[pd.Series, pd.DataFrame, pd.DataFrame]:
    template_id = factor.portfolio_id.split(".")[0]

    returns = get_portfolio_returns(id=factor.portfolio_id, api_key=api_key)
    returns = returns.dropna()
    returns.index = pd.to_datetime(returns.index)

    tickers = get_tickers(
        id=template_id,
        api_key=api_key,
        universe_size=factor.default_universe,
        exchange=None,
    )
    factor_data = get_portfolio_factors_historical(
        id=template_id, tickers=tickers, api_key=api_key
    )
    factor_data.index = pd.to_datetime(factor_data.index)

    prices = get_prices(tickers=tickers, api_key=api_key)
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


def main(argv: list[str]) -> int:
    api_key = _get_api_key()
    factors = load_factors()
    if argv:
        wanted = set(argv)
        factors = [f for f in factors if f.id in wanted]
        missing = wanted - {f.id for f in factors}
        if missing:
            print(f"Unknown factor(s): {sorted(missing)}", file=sys.stderr)
            return 1

    failures: list[str] = []
    for factor in factors:
        try:
            render_factsheet(factor, api_key)
        except Exception as exc:  # noqa: BLE001 — keep going to other factors
            failures.append(factor.id)
            print(f"  ✗ {factor.id} failed: {exc}", file=sys.stderr)
            traceback.print_exc(limit=3)

    if failures:
        print(f"\nFailed: {failures}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
