"""Export per-portfolio returns CSVs (multi-factor portfolios) from the Unravel API.

Usage:
    python -m scripts.export_portfolio_returns               # all portfolios
    python -m scripts.export_portfolio_returns spectra       # one portfolio
    python -m scripts.export_portfolio_returns spectra foundational

Portfolio returns land in the same directory as single-factor returns
(``data/portfolio-40-returns/``); the multi-factor entries are keyed by
their portfolio id (e.g. ``spectra.csv``, ``foundational.csv``).

Multi-factor portfolios have no raw factor data — the alpha is composed
of constituent factor signals — so this script only exports the returns
series. The single-factor pipeline (``scripts.export_data``) is the one
that exports raw factor data.
"""

from __future__ import annotations

import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from unravel_client import get_portfolio_returns

from scripts._common import (
    UnknownPortfolios,
    get_api_key,
    job_count,
    select_portfolios,
)
from scripts.portfolios_catalog import Portfolio

REPO_ROOT = Path(__file__).resolve().parent.parent
RETURNS_DIR = REPO_ROOT / "data" / "portfolio-40-returns"


def export_returns(portfolio: Portfolio, api_key: str) -> Path:
    """Save the unconstrained .40 portfolio's daily returns as a CSV."""
    returns: pd.Series = get_portfolio_returns(
        id=portfolio.portfolio_id, api_key=api_key
    )
    returns = returns.dropna()
    returns.index.name = "date"
    returns.name = "return"

    RETURNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RETURNS_DIR / f"{portfolio.id}.csv"
    returns.to_csv(out, float_format="%.8f")
    print(f"  ✓ returns → {out.relative_to(REPO_ROOT)} ({len(returns)} rows)")
    return out


def main(argv: list[str]) -> int:
    api_key = get_api_key()
    try:
        portfolios = select_portfolios(argv)
    except UnknownPortfolios as exc:
        print(f"Unknown portfolio(s): {exc.args[0]}", file=sys.stderr)
        return 1

    workers = min(job_count(), len(portfolios)) or 1
    failures: list[str] = []

    def _run(portfolio: Portfolio) -> None:
        try:
            print(f"[{portfolio.id}] {portfolio.name}")
            export_returns(portfolio, api_key)
        except Exception as exc:  # noqa: BLE001 — keep going to other portfolios
            failures.append(portfolio.id)
            print(f"  ✗ {portfolio.id} failed: {exc}", file=sys.stderr)
            traceback.print_exc(limit=2)

    if workers <= 1:
        for portfolio in portfolios:
            _run(portfolio)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_run, p) for p in portfolios]
            for fut in as_completed(futures):
                fut.result()

    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
