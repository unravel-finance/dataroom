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
        return f"{SITE_BASE_URL}/portfolio/{self.portfolio_id}"


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
