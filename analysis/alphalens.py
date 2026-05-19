# depends on https://github.com/stefan-jansen/alphalens-reloaded
import alphalens
import pandas as pd


def factor_analysis(
    signal: pd.DataFrame, price: pd.DataFrame, max_loss: float = 1.0
) -> None:
    # max_loss is AlphaLens' guard that raises when too much of the factor is
    # dropped in forward-return alignment + quantile binning. Restricting to
    # the dynamic universe legitimately drops a lot (90%+ for sparse long-only
    # factors like trend_longonly_adaptive), so default to 1.0 (never raise);
    # AlphaLens still prints the exact drop %, so the loss stays visible.
    factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
        signal.stack(), price, quantiles=5, max_loss=max_loss
    )
    alphalens.tears.create_full_tear_sheet(factor_data)
