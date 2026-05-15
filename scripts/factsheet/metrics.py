"""Performance statistics for a daily-returns time series."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

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


def _equity(returns: pd.Series) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).cumprod()


def equity_curve(returns: pd.Series) -> pd.Series:
    return _equity(returns)


def drawdown(returns: pd.Series) -> pd.Series:
    eq = _equity(returns)
    return eq / eq.cummax() - 1.0


def monthly_returns(returns: pd.Series) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).resample("ME").prod() - 1.0


def compute_stats(returns: pd.Series) -> Stats:
    r = returns.dropna()
    if r.empty:
        raise ValueError("Returns series is empty")

    eq = _equity(r)
    years = (r.index[-1] - r.index[0]).days / 365.25
    total_return = float(eq.iloc[-1] - 1.0)
    cagr = float(eq.iloc[-1] ** (1 / years) - 1.0) if years > 0 else float("nan")

    daily_vol = float(r.std())
    annual_vol = daily_vol * np.sqrt(TRADING_DAYS)
    mean_r = float(r.mean())
    sharpe = (mean_r / daily_vol) * np.sqrt(TRADING_DAYS) if daily_vol > 0 else float("nan")

    downside = r[r < 0]
    downside_vol = float(downside.std()) if not downside.empty else float("nan")
    sortino = (
        (mean_r / downside_vol) * np.sqrt(TRADING_DAYS)
        if downside_vol and downside_vol > 0
        else float("nan")
    )

    dd = drawdown(r)
    max_dd = float(dd.min())
    calmar = (cagr / abs(max_dd)) if max_dd < 0 else float("nan")

    hit_rate = float((r > 0).mean())

    m = monthly_returns(r)
    best_month = float(m.max()) if not m.empty else float("nan")
    worst_month = float(m.min()) if not m.empty else float("nan")

    return Stats(
        start=r.index[0].date(),
        end=r.index[-1].date(),
        years=years,
        total_return=total_return,
        cagr=cagr,
        annual_vol=annual_vol,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_dd,
        calmar=calmar,
        hit_rate=hit_rate,
        best_month=best_month,
        worst_month=worst_month,
    )


def fmt_pct(x: float, digits: int = 1) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x * 100:.{digits}f}%"


def fmt_signed_pct(x: float, digits: int = 1) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x * 100:+.{digits}f}%"


def fmt_ratio(x: float, digits: int = 2) -> str:
    if x is None or np.isnan(x):
        return "—"
    return f"{x:.{digits}f}"
