from finml_utils import get_env

from api import get_live_weights

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "beta.5"

live_weights = get_live_weights(portfolio, UNRAVEL_API_KEY)
print(live_weights)
