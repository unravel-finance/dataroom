"""Multi-factor portfolio catalog for the data-room CSV/PDF exports.

Mirrors the multi-factor entries in apps/alpha/config/portfolios.config.ts in
unravel-router (the source of truth); keep in sync manually.

Shape mirrors scripts/factors_catalog.Factor so the shared factsheet
renderer in scripts/factsheet/page_one.py can treat both uniformly — the
``is_multi_factor`` flag flips the construction-method copy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.factors_catalog import (
    GITHUB_BLOB_BASE,
    GITHUB_RAW_BASE,
    SITE_BASE_URL,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

# The shared portfolio-construction notebook every multi-factor factsheet
# links to from page 2 (the equivalent of each single-factor's
# factor_analysis_<id>.ipynb).
_PORTFOLIO_NOTEBOOK = "notebooks/00_multi_factor_portfolio_construction.ipynb"


@dataclass(frozen=True)
class Portfolio:
    """A multi-factor portfolio with a public landing page + dataroom artefacts."""

    id: str
    name: str
    portfolio_id: str
    default_universe: str
    short_description: str
    long_description: str
    components: tuple[str, ...]
    badges: tuple[str, ...] = ()
    effect: str = ""
    is_adaptive: bool = False

    # --- shared interface with Factor (used by the page_one renderer) ----

    is_multi_factor: bool = True

    @property
    def detail_url(self) -> str:
        return (
            f"{SITE_BASE_URL}/portfolio/{self.portfolio_id}"
            "?exchange=unconstrained"
        )

    @property
    def returns_csv_url(self) -> str:
        return f"{GITHUB_RAW_BASE}/data/portfolio-40-returns/{self.id}.csv"

    @property
    def notebook_url(self) -> str:
        return f"{GITHUB_BLOB_BASE}/{_PORTFOLIO_NOTEBOOK}"

    @property
    def has_factor_notebook(self) -> bool:
        # No per-portfolio AlphaLens notebook — the page-2 CTA in the
        # shared renderer falls back to the generic construction notebook.
        return False


_PORTFOLIOS: list[Portfolio] = [
    Portfolio(
        id='spectra',
        name='Spectra',
        portfolio_id='spectra.40',
        default_universe='40',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Multi-Factor'),
        components=(
            'Enhanced Momentum',
            'Enhanced Carry',
            'Retail Flow',
            'Margin Risk',
            'Altair',
            'Mean Reversion',
        ),
        short_description=(
            'Combines six cross-sectional, orthogonal factors, optimised for '
            'market-neutral risk-adjusted performance.'
        ),
        effect=(
            'A diversified multi-factor blend: combining orthogonal alpha '
            'sources mutes single-factor regime risk and lifts the overall '
            'information ratio.'
        ),
        long_description=(
            'Spectra is a market-neutral portfolio that combines six orthogonal\nfactors: Enhanced Momentum, Enhanced Carry, Retail Flow, Margin Risk,\nAltair and Mean Reversion.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep\nit both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Portfolio(
        id='spectra_adaptive',
        name='Spectra Adaptive',
        portfolio_id='spectra_adaptive.40',
        default_universe='40',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Multi-Factor'),
        is_adaptive=True,
        components=(
            'Enhanced Momentum',
            'Enhanced Carry',
            'Retail Flow',
            'Margin Risk',
            'Altair',
            'Mean Reversion',
        ),
        short_description=(
            'Combines six cross-sectional, orthogonal factors — while reducing '
            'exposure dynamically in adverse market conditions.'
        ),
        effect=(
            'The diversified Spectra blend with an adaptive overlay that '
            'dials gross exposure down (sometimes to near-zero) when '
            'market conditions turn hostile.'
        ),
        long_description=(
            'Spectra Adaptive is a market-neutral portfolio that combines the same six\northogonal factors as Spectra (Enhanced Momentum, Enhanced Carry, Retail\nFlow, Margin Risk, Altair and Mean Reversion).'
            "\n\n"
            "The Adaptive overlay reduces the portfolio's gross exposure when the\nmarket conditions are adverse. This may result in prolonged periods of\nvery small (<10%) gross exposure."
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep\nit both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Portfolio(
        id='spectra_highturnover',
        name='Spectra High-Turnover',
        portfolio_id='spectra_highturnover.40',
        default_universe='40',
        badges=(
            'Market-Neutral',
            'Survivorship-Bias Free',
            'Multi-Factor',
            'High-Turnover',
        ),
        components=(
            'Enhanced Momentum',
            'Enhanced Carry',
            'Retail Flow',
            'Margin Risk',
            'Altair',
            'Mean Reversion',
        ),
        short_description=(
            'Combines six cross-sectional, orthogonal factors, optimised for '
            'market-neutral risk-adjusted performance & high turnover.'
        ),
        effect=(
            'The Spectra blend tuned for a higher-turnover regime — extracts '
            'more of the short-horizon alpha at the cost of higher gross '
            'trading volume.'
        ),
        long_description=(
            'Spectra High-Turnover is a market-neutral portfolio, optimised for higher\nturnover, that combines six orthogonal factors: Enhanced Momentum,\nEnhanced Carry, Retail Flow, Margin Risk, Altair and Mean Reversion.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep\nit both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Portfolio(
        id='foundational',
        name='Foundational Factors',
        portfolio_id='foundational.40',
        default_universe='40',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Multi-Factor'),
        components=('Momentum', 'Mean Reversion', 'Enhanced Carry'),
        short_description=(
            'Combines cross-sectional momentum, mean reversion and carry '
            'factors, optimised for market-neutral risk-adjusted performance.'
        ),
        effect=(
            'A compact three-factor core (momentum, mean reversion, carry) — '
            'each axis captures a structurally different source of '
            'cross-sectional return, so their blend is largely uncorrelated.'
        ),
        long_description=(
            'Foundational Factors integrates three orthogonal factors: momentum,\nmean reversion and enhanced carry. The momentum component captures assets\nwith strong, persistent price trends; the mean reversion component\ncaptures assets with medium-term mean reversion effects; and the carry\nstrategy seeks to profit from funding rates and related statistical price\ndistortions.'
            "\n\n"
            'All have been inspired by the academic literature, with proprietary\nenhancements.'
            "\n\n"
            'Together, these factors create a diversified return stream designed to\noutperform in a range of market conditions.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep\nit both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Portfolio(
        id='foundational_adaptive',
        name='Foundational Adaptive',
        portfolio_id='foundational_adaptive.40',
        default_universe='40',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Multi-Factor'),
        is_adaptive=True,
        components=('Momentum', 'Mean Reversion', 'Enhanced Carry'),
        short_description=(
            'Combines cross-sectional momentum, mean reversion and carry '
            'factors — while reducing exposure dynamically in adverse market '
            'conditions.'
        ),
        effect=(
            'The Foundational three-factor core with an adaptive overlay that '
            'cuts gross exposure when the market backdrop turns adverse.'
        ),
        long_description=(
            'Foundational Adaptive integrates three orthogonal factors: momentum,\nmean reversion and enhanced carry. The momentum component captures assets\nwith strong, persistent price trends; the mean reversion component\ncaptures assets with medium-term mean reversion effects; and the carry\nstrategy seeks to profit from funding rates and related statistical price\ndistortions.'
            "\n\n"
            "The Adaptive overlay reduces the portfolio's gross exposure when market\nconditions are adverse. This may result in prolonged periods of very\nsmall (<10%) gross exposure."
            "\n\n"
            'All have been inspired by the academic literature, with proprietary\nenhancements.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep\nit both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
]


def load_portfolios() -> list[Portfolio]:
    return list(_PORTFOLIOS)


def find_portfolio(portfolio_id: str) -> Portfolio:
    for portfolio in _PORTFOLIOS:
        if portfolio.id == portfolio_id:
            return portfolio
    raise KeyError(f"Unknown portfolio id: {portfolio_id}")
