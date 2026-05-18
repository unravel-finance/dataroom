"""Shared helpers for the factor export / factsheet pipeline.

Keeps the API-key lookup, the ``argv`` → factor selection, and the
parallel-worker count in one place so ``export_data`` and
``generate_factsheets`` can't drift apart.
"""

from __future__ import annotations

import os

from scripts.factors_catalog import Factor, load_factors


def get_api_key() -> str:
    key = os.environ.get("UNRAVEL_API_KEY")
    if not key:
        raise RuntimeError("UNRAVEL_API_KEY environment variable is not set")
    return key


class UnknownFactors(KeyError):
    """Raised by :func:`select_factors` when argv names ids not in the catalog."""


def select_factors(argv: list[str]) -> list[Factor]:
    """Every catalog factor, or just the subset named in ``argv``.

    Raises :class:`UnknownFactors` (carrying the sorted unknown ids) when
    an argument doesn't match a catalog id.
    """
    factors = load_factors()
    if not argv:
        return factors
    wanted = set(argv)
    selected = [f for f in factors if f.id in wanted]
    missing = wanted - {f.id for f in selected}
    if missing:
        raise UnknownFactors(sorted(missing))
    return selected


def job_count(default: int = 4) -> int:
    """Parallel worker count for the per-factor loop.

    Defaults to a deliberately conservative value (the work is dominated by
    Unravel API round-trips, so this is mostly about not hammering the API)
    and is overridable via the ``FACTSHEET_JOBS`` environment variable.
    """
    raw = os.environ.get("FACTSHEET_JOBS", "").strip()
    if not raw:
        return default
    try:
        n = int(raw)
    except ValueError:
        return default
    return max(n, 1)
