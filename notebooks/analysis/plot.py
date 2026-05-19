import matplotlib.pyplot as plt
import pandas as pd

from .utils import to_drawdown


def plot_backtest_results(
    cumulative_returns: pd.Series,
    benchmark: pd.Series,
    portfolio: str,
    figsize=(12, 10),
):
    """
    Plot backtest results with performance chart and signal.

    Args:
        results (pd.DataFrame): DataFrame containing backtest results with
                               'cumulative_returns', 'price_rebased', and 'signal' columns
        figsize (tuple): Figure size as (width, height) in inches
    """
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=figsize, gridspec_kw={"height_ratios": [2, 1]}
    )

    ax1.plot(
        cumulative_returns.index,
        cumulative_returns,
        label="Strategy Returns",
        color="darkBlue",
    )
    ax1.plot(
        benchmark.index,
        benchmark,
        label=f"Benchmark ({benchmark.name})",
        color="gray",
    )
    ax1.set_title("Performance of Portfolio", fontsize=14)
    ax1.legend()
    ax1.grid(True, axis="y", linestyle="--")

    ax2.plot(
        cumulative_returns.index,
        to_drawdown(cumulative_returns),
        label="Drawdown Portfolio",
        color="red",
    )
    ax2.plot(
        benchmark.index,
        to_drawdown(benchmark),
        label="Drawdown Benchmark",
        color="gray",
    )
    ax2.set_title(f"Portfolio {portfolio}")
    ax2.legend()
    ax2.grid(True, axis="y", linestyle="--")

    plt.tight_layout()
    plt.show()

    return fig, (ax1, ax2)
