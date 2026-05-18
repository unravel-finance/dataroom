"""Export per-factor CSVs (portfolio returns + raw factor data) from the Unravel API.

Outputs:
    data/portfolio-40-returns/<factor_id>.csv  — daily returns of the unconstrained (.40) portfolio
    data/raw-factors/<factor_id>.csv           — historical raw factor data (per-ticker)

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
from unravel_client import (
    get_portfolio_factors_historical,
    get_portfolio_returns,
    get_tickers,
)

from scripts._common import UnknownFactors, get_api_key, job_count, select_factors
from scripts.factors_catalog import Factor

REPO_ROOT = Path(__file__).resolve().parent.parent
RETURNS_DIR = REPO_ROOT / "data" / "portfolio-40-returns"
FACTORS_DIR = REPO_ROOT / "data" / "raw-factors"

# The most recent factor values are a live, paid signal — never publish them.
# We embargo the trailing 30 calendar days from the open raw-factor export.
EMBARGO_DAYS = 30


def _embargo_recent(factor_data: pd.DataFrame) -> pd.DataFrame:
    """Drop the trailing EMBARGO_DAYS of rows so the raw export never leaks
    the most recent (still-live) factor signal."""
    idx = pd.to_datetime(factor_data.index)
    tz = getattr(idx, "tz", None)
    cutoff = pd.Timestamp.now(tz=tz).normalize() - pd.Timedelta(days=EMBARGO_DAYS)
    mask = idx <= cutoff
    kept = factor_data.loc[mask]
    dropped = int((~mask).sum())
    if dropped:
        print(
            f"  · embargo: dropped last {dropped} row(s) newer than "
            f"{cutoff.date()} (≤ {EMBARGO_DAYS}d)"
        )
    if not kept.empty:
        max_kept = pd.to_datetime(kept.index).max()
        assert max_kept <= cutoff, (
            f"embargo check failed: latest exported {max_kept} > {cutoff}"
        )
    return kept


def export_returns(factor: Factor, api_key: str) -> Path:
    """Save the unconstrained .40 portfolio's daily returns as a CSV."""
    returns: pd.Series = get_portfolio_returns(
        id=factor.portfolio_id, api_key=api_key
    )
    returns = returns.dropna()
    returns.index.name = "date"
    returns.name = "return"

    RETURNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RETURNS_DIR / f"{factor.id}.csv"
    returns.to_csv(out, float_format="%.8f")
    print(f"  ✓ returns → {out.relative_to(REPO_ROOT)} ({len(returns)} rows)")
    return out


def export_factor_data(factor: Factor, api_key: str) -> Path:
    """Save the raw historical factor data (per-ticker time series) as a CSV.

    Exported on the *full, unconstrained* universe (every ticker the factor
    spans), not the Top-N portfolio universe — the data-room CSV is meant to
    show the complete factor, while the factsheet's AlphaLens analysis pins
    to the rolling Top-N separately.
    """
    tickers = get_tickers(
        id=factor.portfolio_id.split(".")[0],
        api_key=api_key,
        universe_size="full",
        exchange=None,
    )
    factor_data: pd.DataFrame = get_portfolio_factors_historical(
        id=factor.portfolio_id.split(".")[0],
        tickers=tickers,
        api_key=api_key,
    )
    factor_data.index.name = "date"
    factor_data = _embargo_recent(factor_data)
    # float32 + 4-significant-digit %g keeps the CSV compact; this precision
    # is well within float32's noise floor for factor values and leaves
    # rank/quantile analysis unaffected.
    factor_data = factor_data.astype("float32")

    FACTORS_DIR.mkdir(parents=True, exist_ok=True)
    out = FACTORS_DIR / f"{factor.id}.csv"
    factor_data.to_csv(out, float_format="%.4g")
    print(
        f"  ✓ factor data → {out.relative_to(REPO_ROOT)} "
        f"({len(factor_data)} rows × {factor_data.shape[1]} tickers)"
    )
    return out


def export_factor(factor: Factor, api_key: str) -> None:
    print(f"[{factor.id}] {factor.name}")
    export_returns(factor, api_key)
    export_factor_data(factor, api_key)


def main(argv: list[str]) -> int:
    api_key = get_api_key()
    try:
        factors = select_factors(argv)
    except UnknownFactors as exc:
        print(f"Unknown factor(s): {exc.args[0]}", file=sys.stderr)
        return 1

    # The per-factor work is dominated by Unravel API round-trips, so a
    # thread pool gives a near-linear wall-clock speedup. (No matplotlib
    # here, so threads are safe — unlike generate_factsheets.)
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
                fut.result()  # _run swallows; this only re-raises bugs in _run

    if failures:
        print(f"\nFailed: {sorted(failures)}", file=sys.stderr)
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
