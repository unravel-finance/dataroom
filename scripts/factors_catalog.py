"""Load the single-factor portfolio catalog used for CSV/PDF export.

The narrative copy is mirrored verbatim from
`apps/alpha/config/portfolios.config.ts` in the unravel-router repo — that
file is the source of truth. Keep them in sync manually until we wire up
automated extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FACTORS_YAML = REPO_ROOT / "factsheet-content" / "factors.yaml"
SITE_BASE_URL = "https://unravel.finance"

# Book-a-call CTA — mirrors the `/booking` route used across the site
# (see nav.config.tsx in unravel-router, the source of truth for site links).
BOOKING_URL = f"{SITE_BASE_URL}/booking"

# Notebooks live at the repo root as factor_analysis_<id>.ipynb, but only for
# a subset of factors. When a factor-specific notebook isn't committed we fall
# back to the generic backtest-replication notebook, which works for any
# factor — so the factsheet's "replication notebook" link is never dead.
GITHUB_BLOB_BASE = "https://github.com/unravel-finance/api-guide/blob/main"
# CSV artefacts are referenced via raw GitHub URLs (the same convention the
# Unravel Alpha web app uses — see README "Sales Data-Room Pipeline").
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/unravel-finance/api-guide/main"
_GENERIC_NOTEBOOK = "replicate_portfolio_backtest.ipynb"


@dataclass(frozen=True)
class Factor:
    id: str
    name: str
    portfolio_id: str
    default_universe: str
    short_description: str
    long_description: str
    # Optional taxonomy / sales copy — drives the page 1 hero. Falls back to
    # safe defaults when absent so older catalog entries still render.
    category: str = ""
    badges: tuple[str, ...] = ()
    effect: str = ""

    @property
    def detail_url(self) -> str:
        return (
            f"{SITE_BASE_URL}/portfolio/{self.portfolio_id}"
            "?exchange=unconstrained"
        )

    @property
    def returns_csv_url(self) -> str:
        """Raw GitHub link to the published daily-returns CSV."""
        return f"{GITHUB_RAW_BASE}/data/returns/{self.id}.csv"

    @property
    def factor_data_csv_url(self) -> str:
        """Raw GitHub link to the published raw factor-data CSV."""
        return f"{GITHUB_RAW_BASE}/data/factors/{self.id}.csv"

    @property
    def has_factor_notebook(self) -> bool:
        """True when a factor-specific replication notebook is committed."""
        return (REPO_ROOT / f"factor_analysis_{self.id}.ipynb").exists()

    @property
    def notebook_url(self) -> str:
        """GitHub link to the replication notebook — the factor-specific one
        if it exists, otherwise the generic backtest-replication notebook."""
        name = (
            f"factor_analysis_{self.id}.ipynb"
            if self.has_factor_notebook
            else _GENERIC_NOTEBOOK
        )
        return f"{GITHUB_BLOB_BASE}/{name}"


def _short_for(entry: dict) -> str:
    text = entry.get("short_description") or entry.get("tagline") or ""
    return text.strip()


def load_factors() -> list[Factor]:
    raw = yaml.safe_load(FACTORS_YAML.read_text())
    return [
        Factor(
            id=entry["id"],
            name=entry["name"],
            portfolio_id=entry["portfolio_id"],
            default_universe=str(entry["default_universe"]),
            short_description=_short_for(entry),
            long_description=entry["long_description"].strip(),
            category=str(entry.get("category", "")).strip(),
            badges=tuple(
                str(b).strip() for b in (entry.get("badges") or []) if str(b).strip()
            ),
            effect=str(entry.get("effect", "")).strip().replace("\n", " "),
        )
        for entry in raw["factors"]
    ]


def find_factor(factor_id: str) -> Factor:
    for factor in load_factors():
        if factor.id == factor_id:
            return factor
    raise KeyError(f"Unknown factor id: {factor_id}")
