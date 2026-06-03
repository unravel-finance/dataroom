"""Shared helpers for the export / factsheet pipeline."""

from __future__ import annotations

import os

from scripts.factors_catalog import Factor, load_factors
from scripts.portfolios_catalog import Portfolio, load_portfolios


def get_api_key() -> str:
    key = os.environ.get("UNRAVEL_API_KEY")
    if not key:
        raise RuntimeError("UNRAVEL_API_KEY environment variable is not set")
    return key


class UnknownFactors(KeyError):
    """Raised by select_factors() when argv names ids not in the catalog."""


class UnknownPortfolios(KeyError):
    """Raised by select_portfolios() when argv names ids not in the catalog."""


def select_factors(argv: list[str]) -> list[Factor]:
    """Every catalog factor, or just the subset named in argv."""
    factors = load_factors()
    if not argv:
        return factors
    wanted = set(argv)
    selected = [f for f in factors if f.id in wanted]
    missing = wanted - {f.id for f in selected}
    if missing:
        raise UnknownFactors(sorted(missing))
    return selected


def select_portfolios(argv: list[str]) -> list[Portfolio]:
    """Every catalog multi-factor portfolio, or just the subset named in argv."""
    portfolios = load_portfolios()
    if not argv:
        return portfolios
    wanted = set(argv)
    selected = [p for p in portfolios if p.id in wanted]
    missing = wanted - {p.id for p in selected}
    if missing:
        raise UnknownPortfolios(sorted(missing))
    return selected


def job_count(default: int = 4) -> int:
    """Parallel worker count (override via FACTSHEET_JOBS). Conservative
    default — the work is dominated by Unravel API round-trips."""
    raw = os.environ.get("FACTSHEET_JOBS", "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return max(n, 1)
