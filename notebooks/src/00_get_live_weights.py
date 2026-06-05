# %% [markdown]
# > **Universe & leverage:** Unravel cross-sectional portfolios run on the **Top 40 market-cap universe** at **200% gross exposure** (100% long / 100% short, market-neutral). Adaptive variants scale gross exposure down (toward zero) in adverse market conditions.

# %%
import sys
from pathlib import Path

_root = Path.cwd()
while not (_root / "notebooks" / "analysis").is_dir() and _root != _root.parent:
    _root = _root.parent
for _p in (_root, _root / "notebooks"):
    sys.path.insert(0, str(_p))

from unravel_client import get_live_weights

from analysis.utils import get_env

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "momentum_enhanced.20"

live_weights = get_live_weights(id=portfolio, api_key=UNRAVEL_API_KEY)
print(live_weights)
