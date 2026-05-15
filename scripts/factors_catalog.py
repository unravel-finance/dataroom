"""Load the single-factor portfolio catalog used for CSV/PDF export."""

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
    tagline: str
    effect: str
    long_description: str

    @property
    def detail_url(self) -> str:
        """Public detail page on unravel.finance for this portfolio variant."""
        return f"{SITE_BASE_URL}/portfolio/{self.portfolio_id}"


def _tagline_for(entry: dict) -> str:
    """Tagline is the new field — fall back to legacy short_description."""
    text = entry.get("tagline") or entry.get("short_description") or ""
    return text.strip()


def load_factors() -> list[Factor]:
    raw = yaml.safe_load(FACTORS_YAML.read_text())
    return [
        Factor(
            id=entry["id"],
            name=entry["name"],
            portfolio_id=entry["portfolio_id"],
            default_universe=str(entry["default_universe"]),
            tagline=_tagline_for(entry),
            effect=entry["effect"].strip(),
            long_description=entry["long_description"].strip(),
        )
        for entry in raw["factors"]
    ]


def find_factor(factor_id: str) -> Factor:
    for factor in load_factors():
        if factor.id == factor_id:
            return factor
    raise KeyError(f"Unknown factor id: {factor_id}")
