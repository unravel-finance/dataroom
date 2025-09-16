# %%
from unravel_client import get_live_weights

from analysis.utils import get_env

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "momentum_enhanced.20"

live_weights = get_live_weights(id=portfolio, api_key=UNRAVEL_API_KEY)
print(live_weights)
