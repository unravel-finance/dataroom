# %%
# AUTO-GENERATED from scripts/factors_catalog.py by
# scripts/generate_factor_notebooks.py -- do not edit by hand.
import sys
from pathlib import Path

_root = Path.cwd()
while not (_root / "notebooks" / "analysis").is_dir() and _root != _root.parent:
    _root = _root.parent
for _p in (_root, _root / "notebooks"):
    sys.path.insert(0, str(_p))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from unravel_client import get_portfolio_returns

from analysis.utils import get_env
from scripts.factors_catalog import load_factors

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")

portfolios = [factor.portfolio_id for factor in load_factors()]

returns_df = pd.DataFrame(
    {
        portfolio: get_portfolio_returns(id=portfolio, api_key=UNRAVEL_API_KEY)
        for portfolio in portfolios
    }
)

# %%

correlation_matrix = returns_df.corr()

plt.figure(figsize=(16, 13))
sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap="coolwarm",
    center=0,
    square=True,
    fmt=".2f",
    cbar_kws={"shrink": 0.8},
)
plt.title("Cross-Sectional Returns Correlation Matrix")
plt.tight_layout()
plt.show()

# %%
