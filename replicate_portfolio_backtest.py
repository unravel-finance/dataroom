# %%
from unravel_client import get_portfolio_historical_weights

from analysis.backtest import backtest_portfolio
from analysis.plot import plot_backtest_results
from analysis.price import get_price_data
from analysis.utils import get_env, rebase

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "quarta.40"
start_date = "2020-01-01"
end_date = "2025-01-01"
benchmark_ticker = "BTC"


portfolio_historical_weights = get_portfolio_historical_weights(
    id=portfolio,
    api_key=UNRAVEL_API_KEY,
    smoothing=None,  # This will use the default smoothing please see catalog for default values for each portfolio (https://unravel.finance/home/api/catalog/portfolios)
    start_date=start_date,
    end_date=end_date,
)

underlying = get_price_data(
    tickers=portfolio_historical_weights.columns,
    start_date=start_date,
    end_date=end_date,
)

index_intersection = portfolio_historical_weights.index.intersection(underlying.index)
portfolio_historical_weights = portfolio_historical_weights.loc[index_intersection]
underlying = underlying.loc[index_intersection]

if benchmark_ticker in underlying.columns:
    benchmark = underlying[benchmark_ticker]
else:
    benchmark = get_price_data(
        tickers=[benchmark_ticker],
        start_date=start_date,
        end_date=end_date,
    )[benchmark_ticker]

underlying_returns = underlying.pct_change()
portfolio_returns, _ = backtest_portfolio(
    weights=portfolio_historical_weights[underlying.columns],
    underlying=underlying_returns,
    transaction_cost=0.0005,
    lag=0,
)
portfolio_cumulative_returns = (1 + portfolio_returns).cumprod()
plot_backtest_results(
    rebase(portfolio_cumulative_returns), rebase(benchmark), portfolio
)

# %%
