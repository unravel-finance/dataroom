<!-- AUTO-GENERATED from factors_catalog.py -- do not edit. -->

# Factor Analysis Notebooks

AlphaLens factor analysis for every Unravel single-factor portfolio, run on the **dynamic, point-in-time universe** (not every ticker ever tradeable). Open any notebook below — GitHub renders them inline.

### [Cross-factor returns correlation](00_factor_returns_correlation.ipynb)

Correlation heatmap across every portfolio's returns — start here for the big picture.

### Per-factor analysis

| Factor | Category | What it captures |
| --- | --- | --- |
| [Altair](factor_analysis_altair.ipynb) | Microstructure | Measures short-term liquidity dynamics, slippage and market order imbalances. |
| [Margin Risk](factor_analysis_margin_risk.ipynb) | Derivatives Positioning | Assets with higher at-risk-of-liquidation positions tend to underperform less leveraged assets. |
| [Retail Flow](factor_analysis_retail_flow.ipynb) | — | Quantifies retail money flow, positioning, and activity and systematically takes contrarian positions. |
| [Enhanced Mean Reversion](factor_analysis_mean_reversion_enhanced.ipynb) | Statistical | Basket-based mean reversion signal diversified across time frames and transformations with enhanced conditioning for robustness. |
| [Instantaneous Momentum](factor_analysis_instantaneous_momentum.ipynb) | Momentum | Proprietary measure of momentum — assets with higher instantaneous momentum tend to outperform. |
| [Polaris](factor_analysis_polaris.ipynb) | Momentum | Proprietary measure of short-term, normalised momentum effects across crypto assets. |
| [Relative Illiquidity](factor_analysis_relative_illiquidity.ipynb) | Liquidity | Captures the effect of assets with higher relative illiquidity tending to outperform. |
| [Supply Velocity](factor_analysis_supply_velocity.ipynb) | Fundamental | Assets with lower inflation perform better than assets with higher inflation. |
| [Enhanced Momentum](factor_analysis_momentum_enhanced.ipynb) | Momentum | Captures short-term momentum effects, measured by a wide range of proprietary methods. |
| [Mean Reversion](factor_analysis_mean_reversion.ipynb) | Statistical | Basket-based mean reversion signal diversified across different windows to capture broad reversal dynamics. |
| [Trend Consensus Adaptive (Long-Only)](factor_analysis_trend_longonly_adaptive.ipynb) | Trend / Long-Only | Exploits the tendency of assets with positive trend consensus, when the overall market trend is positive. |
| [Enhanced Carry](factor_analysis_carry_enhanced.ipynb) | Carry | Captures cross-sectional funding premium across a wide range of exchanges, exploiting funding imbalances. |
| [Instantaneous Volatility](factor_analysis_instantaneous_volatility.ipynb) | Volatility | Proprietary measure of volatility — assets with higher instantaneous volatility tend to outperform in certain market conditions. |
| [Open Interest Divergence](factor_analysis_open_interest_divergence.ipynb) | Derivatives Positioning | Quantifies open interest divergence and systematically takes positions, aiming to capitalise on behavioural inefficiencies. |
| [Momentum](factor_analysis_momentum.ipynb) | Momentum | Captures short-term momentum opportunities, aiming for uncorrelated returns while minimising directional exposure. |

---

_The jupytext sources live in [`src/`](src/); the notebooks here are generated and executed by the **Generate Notebooks** CI workflow._
