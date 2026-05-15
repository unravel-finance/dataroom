"""Performance statistics for a daily-returns time series.

All metric math is delegated to `finml_utils.quantstats.stats` so we don't
reinvent canonical calculations. `periods=365` everywhere because crypto
trades every calendar day (the upstream default is 252 trading days).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from finml_utils.quantstats import stats as qs

TRADING_DAYS = 365  # crypto trades 7 days a week


@dataclass(frozen=True)
class Stats:
    start: date
    end: date
    years: float
    total_return: float
    cagr: float
    annual_vol: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    hit_rate: float
    best_month: float
    worst_month: float


def equity_curve(returns: pd.Series) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).cumprod()


def drawdown(returns: pd.Series) -> pd.Series:
    return qs.to_drawdown_series(returns)


def monthly_returns(returns: pd.Series) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).resample("ME").prod() - 1.0


def compute_stats(returns: pd.Series) -> Stats:
    r = returns.dropna()
    if r.empty:
        raise ValueError("Returns series is empty")

    cagr = float(qs.cagr(r, periods=TRADING_DAYS))
    max_dd = float(qs.max_drawdown(r))
    # qs.calmar uses its default periods=252 internally; recompute with our
    # crypto period instead so the ratio is consistent with our CAGR figure.
    calmar = cagr / abs(max_dd) if max_dd < 0 else float("nan")

    return Stats(
        start=r.index[0].date(),
        end=r.index[-1].date(),
        years=(r.index[-1] - r.index[0]).days / 365.25,
        total_return=float(qs.comp(r)),
        cagr=cagr,
        annual_vol=float(qs.volatility(r, periods=TRADING_DAYS)),
        sharpe=float(qs.sharpe(r, periods=TRADING_DAYS)),
        sortino=float(qs.sortino(r, periods=TRADING_DAYS)),
        max_drawdown=max_dd,
        calmar=calmar,
        hit_rate=float(qs.win_rate(r, compounded=False)),
        best_month=float(qs.best(r, aggregate="ME")),
        worst_month=float(qs.worst(r, aggregate="ME")),
    )


def fmt_pct(x: float, digits: int = 1) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x * 100:.{digits}f}%".replace("-", "−")


def fmt_signed_pct(x: float, digits: int = 1) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x * 100:+.{digits}f}%".replace("-", "−")


def fmt_ratio(x: float, digits: int = 2) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x:.{digits}f}".replace("-", "−")
