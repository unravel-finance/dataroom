"""Single-factor portfolio catalog for the data-room CSV/PDF exports.

The narrative copy mirrors `apps/alpha/config/portfolios.config.ts` in the
unravel-router repo — that file is the source of truth; keep this in sync
manually until extraction is automated.

Defined as a typed Python list rather than a YAML side-file: this catalog is
engineer-maintained and only ever read by the export / factsheet scripts (the
CI workflow passes factor *ids*, never parses the catalog itself), so a YAML
parser + schema added indirection without buying anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
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
        return f"{GITHUB_RAW_BASE}/data/portfolio-40-returns/{self.id}.csv"

    @property
    def factor_data_csv_url(self) -> str:
        """Raw GitHub link to the published raw factor-data CSV."""
        return f"{GITHUB_RAW_BASE}/data/raw-factors/{self.id}.csv"

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


_FACTORS: list[Factor] = [
    Factor(
        id='altair',
        name='Altair',
        portfolio_id='altair.40',
        default_universe='40',
        category='Microstructure',
        badges=('Market-Neutral', 'Derivatives Metrics', 'Single-Factor'),
        short_description='Measures short-term liquidity dynamics, slippage and market order imbalances.',
        effect='Captures intraday liquidity dislocations: assets temporarily harder to transact in tend to mean-revert as flow normalises.',
        long_description=(
            'Altair is a short-term liquidity metric that captures intraday market\ndynamics. The data is collected in real time and aggregated from the most\nreputable exchanges.'
            "\n\n"
            'Altair is a high-turnover factor that benefits from smoothing to reduce\ntransaction costs.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='margin_risk',
        name='Margin Risk',
        portfolio_id='margin_risk.40',
        default_universe='40',
        category='Derivatives Positioning',
        badges=('Market-Neutral', 'Derivatives Metrics', 'Single-Factor'),
        short_description='Assets with higher at-risk-of-liquidation positions tend to underperform less leveraged assets.',
        effect='Crowded, highly-leveraged long positions get washed out by cascading liquidations — a structural drag that the factor systematically shorts.',
        long_description=(
            'The factor capitalises on the tendency of assets with higher\nat-risk-of-liquidation positions to underperform less leveraged assets.'
            "\n\n"
            'Margin Risk predicts positions vulnerable to forced closure at 1%, 2%, 5%\nand 10% deviations from the current price. Data is aggregated from the top\n10 most reputable exchanges.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='retail_flow',
        name='Retail Flow',
        portfolio_id='retail_flow.40',
        default_universe='40',
        short_description='Quantifies retail money flow, positioning, and activity and systematically takes contrarian positions.',
        long_description=(
            '"Retail Flow" cross-sectional factor is designed to measure and respond\nto retail investor activity.'
            "\n\n"
            'By analyzing individual executed trades sourced from exchanges, the\nstrategy identifies assets heavily influenced by retail participation.\nIt then takes systematically contrarian positions, seeking to exploit\npredictable patterns of overreaction and herding behavior.'
            "\n\n"
            'Order sizes and types are utilized to differentiate between retail and\ninstitutional activity.\nTo quantify trade imbalances on the filtered trades, five distinct\ntechniques are employed, their outputs are normalized and combined in\nan ensemble approach, without any optimization or parameter fitting.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded\nassets, identified on rolling basis - various techniques employed to\nkeep it both stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled\naccording to the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='mean_reversion_enhanced',
        name='Enhanced Mean Reversion',
        portfolio_id='mean_reversion_enhanced.40',
        default_universe='40',
        category='Statistical',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Basket-based mean reversion signal diversified across time frames and transformations with enhanced conditioning for robustness.',
        effect="Captures short-horizon reversal across multiple windows, conditioned on regime so the signal is muted when reversal isn't paying.",
        long_description=(
            'Enhanced Mean Reversion is a basket-based signal that combines diversified\nmean reversion transformations across multiple time frames, with enhanced\nconditioning to improve robustness.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='instantaneous_momentum',
        name='Instantaneous Momentum',
        portfolio_id='instantaneous_momentum.40',
        default_universe='40',
        category='Momentum',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Proprietary measure of momentum — assets with higher instantaneous momentum tend to outperform.',
        effect='Identifies assets that are accelerating right now (not over weeks), and rides the short-term continuation before it decays.',
        long_description=(
            'The factor capitalises on the tendency of assets with higher\ninstantaneous momentum to outperform assets with lower instantaneous\nmomentum.'
            "\n\n"
            'Its universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='polaris',
        name='Polaris',
        portfolio_id='polaris.40',
        default_universe='40',
        category='Momentum',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Proprietary measure of short-term, normalised momentum effects across crypto assets.',
        effect='A volatility-normalised momentum read — identifies assets whose drift is strong relative to their own noise floor.',
        long_description=(
            'Polaris is a proprietary market-neutral measure designed to identify\nshort-term, normalised momentum effects across crypto assets.'
            "\n\n"
            'Its universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The portfolio is rebalanced daily, with hourly updates provided, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='relative_illiquidity',
        name='Relative Illiquidity',
        portfolio_id='relative_illiquidity.40',
        default_universe='40',
        category='Liquidity',
        badges=('Market-Neutral', 'Derivatives Metrics', 'Single-Factor'),
        short_description='Captures the effect of assets with higher relative illiquidity tending to outperform.',
        effect='Harvests the illiquidity risk premium in mid/large-cap digital assets — assets that are harder to transact pay you to hold them.',
        long_description=(
            'The factor is designed to capitalise on the persistent effect of assets\nwith higher relative illiquidity tending to outperform, among the\nmid/large-cap digital assets.'
            "\n\n"
            'Relative illiquidity is calculated by taking the arithmetic mean of half a\ndozen relative liquidity metrics — ratios where the denominator is usually\nmarket capitalisation of the asset. Among them are volume, open interest,\norder book depth, spread, and four more. The metrics are aggregated across\nthe top 10 most reputable exchanges.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='supply_velocity',
        name='Supply Velocity',
        portfolio_id='supply_velocity.40',
        default_universe='40',
        category='Fundamental',
        badges=('Market-Neutral', 'Fundamental', 'Single-Factor'),
        short_description='Assets with lower inflation perform better than assets with higher inflation.',
        effect='Captures the link between token supply dynamics and price: inflationary tokens systematically underperform their disinflationary peers.',
        long_description=(
            'Supply Velocity measures changes in token supply dynamics. It captures\ninflationary and deflationary pressures across crypto assets, reflecting\nthe fundamental relationship between token supply and asset performance.'
            "\n\n"
            'It was inspired by the observation that supply inflation can lead to\nunderperformance, and that crypto is maturing into a more\nfundamental-driven market where tokenomics increasingly matter.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='momentum_enhanced',
        name='Enhanced Momentum',
        portfolio_id='momentum_enhanced.40',
        default_universe='40',
        category='Momentum',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Captures short-term momentum effects, measured by a wide range of proprietary methods.',
        effect='Blends three orthogonal short-term momentum reads (Instantaneous Momentum, Polaris, Momentum) — diversified momentum exposure with lower idiosyncratic noise.',
        long_description=(
            'Enhanced Momentum is designed to exploit cross-sectional price\ninefficiencies in the crypto market, measured by a collection of\nproprietary methods, capturing short-term momentum-related effects.'
            "\n\n"
            'It is a blend of:\n  - Instantaneous Momentum\n  - Polaris\n  - Momentum'
            "\n\n"
            'Where possible, it is recommended to use the individual components — they\ngive more control over the exposure.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='mean_reversion',
        name='Mean Reversion',
        portfolio_id='mean_reversion.40',
        default_universe='40',
        category='Statistical',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Basket-based mean reversion signal diversified across different windows to capture broad reversal dynamics.',
        effect='Systematically buys recent underperformers and sells outperformers across a diversified set of look-back windows.',
        long_description=(
            'Mean Reversion is a basket-based signal diversified across different\nwindows to capture reversal dynamics and statistical arbitrage\nopportunities in crypto assets.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='trend_longonly_adaptive',
        name='Trend Consensus Adaptive (Long-Only)',
        portfolio_id='trend_longonly_adaptive.40',
        default_universe='40',
        category='Trend / Long-Only',
        badges=('Long-Only', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Exploits the tendency of assets with positive trend consensus, when the overall market trend is positive.',
        effect='Long-only exposure to the strongest-trending assets, gated by a market-wide regime filter — gross exposure goes to zero in adverse markets.',
        long_description=(
            'Trend Consensus Adaptive is designed to exploit the asymmetric positive\nexpected returns of assets with positive trend consensus. It longs the top\nsextile (top 20%) of assets with the highest Trend Consensus, when the\noverall market trend is positive. It does not have any short exposure.'
            "\n\n"
            'Unlike other portfolios, Trend Consensus Adaptive is long-only and is\ndisplayed here with 100% target gross exposure.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='carry_enhanced',
        name='Enhanced Carry',
        portfolio_id='carry_enhanced.40',
        default_universe='40',
        category='Carry',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Captures cross-sectional funding premium across a wide range of exchanges, exploiting funding imbalances.',
        effect='Earns the funding-rate premium plus the statistical inefficiency that surrounds it, aggregated across 10 venues rather than a single exchange.',
        long_description=(
            'The market-neutral carry portfolio is designed to exploit funding\npremiums, in large part capturing the associated statistical\ninefficiencies — in addition to the funding payments themselves. The\nfactor is calculated by ingesting funding rates from the top 10 most\nreputable exchanges, avoiding reliance on any specific venue alone.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='instantaneous_volatility',
        name='Instantaneous Volatility',
        portfolio_id='instantaneous_volatility.40',
        default_universe='40',
        category='Volatility',
        badges=('Market-Neutral', 'Single-Factor'),
        short_description='Proprietary measure of volatility — assets with higher instantaneous volatility tend to outperform in certain market conditions.',
        effect='Identifies regimes where high-volatility names lead the tape and tilts cross-sectionally accordingly.',
        long_description=(
            'The factor capitalises on the tendency of assets with higher instantaneous\nvolatility to outperform less volatile assets in certain market\nconditions.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            "To balance each asset's risk contribution, positions are scaled according\nto the inverse of their rolling volatility."
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='open_interest_divergence',
        name='Open Interest Divergence',
        portfolio_id='open_interest_divergence.40',
        default_universe='40',
        category='Derivatives Positioning',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Quantifies open interest divergence and systematically takes positions, aiming to capitalise on behavioural inefficiencies.',
        effect='Reads the divergence between price action and open-interest dynamics to isolate positioning-driven moves that tend to revert.',
        long_description=(
            'The portfolio is designed to capitalise on the persistent relationship\nbetween open interest dynamics and future asset performance. It\nsystematically identifies and exploits divergence in open interest\npatterns across assets.'
            "\n\n"
            'The asset universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
    Factor(
        id='momentum',
        name='Momentum',
        portfolio_id='momentum.40',
        default_universe='40',
        category='Momentum',
        badges=('Market-Neutral', 'Survivorship-Bias Free', 'Single-Factor'),
        short_description='Captures short-term momentum opportunities, aiming for uncorrelated returns while minimising directional exposure.',
        effect="Classic cross-sectional momentum tailored to crypto's short half-life: longs the leaders, shorts the laggards, market-neutral.",
        long_description=(
            'The market-neutral momentum portfolio is designed to exploit\ncross-sectional price inefficiencies in the crypto market, capturing\nshort-term, asset-specific momentum signals. By maintaining balanced long\nand short exposures, it aims to deliver alpha while minimising sensitivity\nto broader market movements.'
            "\n\n"
            'Its universe consists of the most liquid and actively traded assets,\nidentified on a rolling basis — various techniques are employed to keep it\nboth stable and relevant, as well as survivorship-bias free.'
            "\n\n"
            'The factor is available (point-in-time) with hourly updates, 5 minutes\npast the hour (UTC).'
        ),
    ),
]

def load_factors() -> list[Factor]:
    return list(_FACTORS)


def find_factor(factor_id: str) -> Factor:
    for factor in _FACTORS:
        if factor.id == factor_id:
            return factor
    raise KeyError(f"Unknown factor id: {factor_id}")
