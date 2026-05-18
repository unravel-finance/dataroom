# depends on https://github.com/stefan-jansen/alphalens-reloaded
import alphalens
import pandas as pd


def factor_analysis(
    signal: pd.DataFrame, price: pd.DataFrame, max_loss: float = 1.0
) -> None:
    # Restricting to the dynamic point-in-time universe (and sparse long-only
    # factors like trend_longonly_adaptive, whose ties collapse the quantile
    # binning) can drop most of the cross-section. AlphaLens still prints the
    # exact drop %, so we tolerate the loss instead of raising rather than
    # silently hiding it.
    factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
        signal.stack(), price, quantiles=5, max_loss=max_loss
    )
    alphalens.tears.create_full_tear_sheet(factor_data)
