"""Export per-factor portfolio-return CSVs from the Unravel API.

Usage:
    python -m scripts.export_data                 # all factors
    python -m scripts.export_data altair          # one factor
    python -m scripts.export_data altair momentum # several
"""

from __future__ import annotations

import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from unravel_client import get_portfolio_returns

from scripts._common import (
    UnknownFactors,
    drop_incomplete_last_day,
    get_api_key,
    job_count,
    select_factors,
)
from scripts.factors_catalog import Factor

REPO_ROOT = Path(__file__).resolve().parent.parent
RETURNS_DIR = REPO_ROOT / "data" / "portfolio-40-returns"


def export_returns(factor: Factor, api_key: str) -> Path:
    """Save the unconstrained .40 portfolio's daily returns as a CSV."""
    returns: pd.Series = get_portfolio_returns(
        id=factor.portfolio_id, api_key=api_key
    )
    returns = returns.dropna()
    returns = drop_incomplete_last_day(returns)
    returns.index.name = "date"
    returns.name = "return"

    RETURNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RETURNS_DIR / f"{factor.id}.csv"
    returns.to_csv(out, float_format="%.8f")
    print(f"  ✓ returns → {out.relative_to(REPO_ROOT)} ({len(returns)} rows)")
    return out


def export_factor(factor: Factor, api_key: str) -> None:
    print(f"[{factor.id}] {factor.name}")
    export_returns(factor, api_key)


def main(argv: list[str]) -> int:
    api_key = get_api_key()
    try:
        factors = select_factors(argv)
    except UnknownFactors as exc:
        print(f"Unknown factor(s): {exc.args[0]}", file=sys.stderr)
        return 1

    # API-bound work — a thread pool is safe here (no matplotlib).
    workers = min(job_count(), len(factors)) or 1
    failures: list[str] = []

    def _run(factor: Factor) -> None:
        try:
            export_factor(factor, api_key)
        except Exception as exc:  # noqa: BLE001 — keep going to other factors
            failures.append(factor.id)
            print(f"  ✗ {factor.id} failed: {exc}", file=sys.stderr)
            traceback.print_exc(limit=2)

    if workers <= 1:
        for factor in factors:
            _run(factor)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_run, f) for f in factors]
            for fut in as_completed(futures):
                fut.result()

    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
