# depends on https://github.com/stefan-jansen/alphalens-reloaded
import alphalens
import pandas as pd


def factor_analysis(signal: pd.DataFrame, price: pd.DataFrame) -> None:
    factor_data = alphalens.utils.get_clean_factor_and_forward_returns(
        signal.stack(), price, quantiles=5, max_loss=0.5
    )
    alphalens.tears.create_full_tear_sheet(factor_data)
