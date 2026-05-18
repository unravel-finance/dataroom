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


# --- windowed performance / risk tables (page 1) -----------------------------

# (label, calendar-day lookback). None = since inception.
_RETURN_WINDOWS: list[tuple[str, int | None]] = [
    ("1M", 30),
    ("3M", 91),
    ("1Y", 365),
    ("3Y", 365 * 3),
    ("5Y", 365 * 5),
    ("SI", None),
]
_RISK_WINDOWS: list[tuple[str, int]] = [
    ("1M", 30),
    ("3M", 91),
    ("1Y", 365),
    ("3Y", 365 * 3),
]


def _window_slice(returns: pd.Series, days: int | None) -> pd.Series:
    if days is None:
        return returns
    cutoff = returns.index[-1] - pd.Timedelta(days=days)
    return returns.loc[returns.index > cutoff]


def gross_return_by_window(returns: pd.Series) -> dict[str, float]:
    """Compound (gross) return over each trailing window. NaN when the
    history is shorter than the window."""
    r = returns.dropna()
    span_days = (r.index[-1] - r.index[0]).days
    out: dict[str, float] = {}
    for label, days in _RETURN_WINDOWS:
        if days is not None and days > span_days + 1:
            out[label] = float("nan")
            continue
        w = _window_slice(r, days)
        out[label] = float((1.0 + w).prod() - 1.0) if not w.empty else float("nan")
    return out


def annual_returns(returns: pd.Series) -> dict[str, float]:
    """Calendar-year compound returns; the last (partial) year is labelled
    YTD."""
    r = returns.dropna()
    yearly = (1.0 + r).groupby(r.index.year).prod() - 1.0
    out: dict[str, float] = {}
    last_year = r.index[-1].year
    for year, val in yearly.items():
        out["YTD" if year == last_year else str(year)] = float(val)
    return out


def realized_vol_by_window(returns: pd.Series) -> dict[str, float]:
    """Annualised realised volatility over each trailing window."""
    r = returns.dropna()
    span_days = (r.index[-1] - r.index[0]).days
    out: dict[str, float] = {}
    for label, days in _RISK_WINDOWS:
        if days > span_days + 1:
            out[label] = float("nan")
            continue
        w = _window_slice(r, days)
        out[label] = (
            float(w.std() * np.sqrt(TRADING_DAYS)) if len(w) > 2 else float("nan")
        )
    return out


def return_to_risk_by_window(returns: pd.Series) -> dict[str, float]:
    """Gross return over a window divided by that window's realised vol —
    the same construction Kaiko's factsheets use."""
    gr = gross_return_by_window(returns)
    vol = realized_vol_by_window(returns)
    out: dict[str, float] = {}
    for label, _ in _RISK_WINDOWS:
        g, v = gr.get(label), vol.get(label)
        out[label] = (
            g / v if g is not None and v not in (None, 0) and not np.isnan(v) else float("nan")
        )
    return out


def max_drawdown_with_date(returns: pd.Series) -> tuple[float, date | None]:
    """Max drawdown and the date the trough was hit."""
    r = returns.dropna()
    dd = qs.to_drawdown_series(r)
    if dd.empty:
        return float("nan"), None
    trough = dd.idxmin()
    return float(dd.min()), trough.date()


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
