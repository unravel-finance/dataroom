# %%

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from unravel_client import get_portfolio_returns

from analysis.utils import get_env

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")

portfolios = [
    "polaris.40",
    "carry_enhanced.40",
    "retail_flow.40",
    "altair.40",
    "margin_risk.40",
    "relative_illiquidity.40",
    "mean_reversion.40",
    "mean_reversion_enhanced.40",
    "margin_risk.40",
]

returns_df = pd.DataFrame(
    {
        portfolio: get_portfolio_returns(id=portfolio, api_key=UNRAVEL_API_KEY)
        for portfolio in portfolios
    }
)

# %%

correlation_matrix = returns_df.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap="coolwarm",
    center=0,
    square=True,
    fmt=".3f",
    cbar_kws={"shrink": 0.8},
)
plt.title("Cross-Sectional Returns Correlation Matrix")
plt.tight_layout()
plt.show()

# %%
