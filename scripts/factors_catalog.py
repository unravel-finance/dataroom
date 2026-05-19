"""Re-export of the root :mod:`factors_catalog`.

Keeps the ``scripts.factors_catalog`` import path working (the path the
F6ZSG factsheet pipeline uses) without duplicating the catalog.
"""

from __future__ import annotations

from factors_catalog import (
    BOOKING_URL,
    GITHUB_BLOB_BASE,
    GITHUB_RAW_BASE,
    SITE_BASE_URL,
    Factor,
    find_factor,
    load_factors,
)

__all__ = [
    "BOOKING_URL",
    "GITHUB_BLOB_BASE",
    "GITHUB_RAW_BASE",
    "SITE_BASE_URL",
    "Factor",
    "find_factor",
    "load_factors",
]
