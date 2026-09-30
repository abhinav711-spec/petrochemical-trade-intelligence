import sqlite3

import numpy as np
import pandas as pd
from app_utils import DATABASE_PATH


def get_clean_data(data=None):
    """Reads SQLite data and cleans infinity and zero division values."""
    if data is None:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query("SELECT * FROM trade_records", conn)
        conn.close()
    else:
        df = data.copy()

    if df.empty:
        return df

    if "unit_price_usd" not in df.columns:
        df["unit_price_usd"] = df.get("trade_unit_value_usd_mt", 0.0)
    if "trade_type" not in df.columns and "trade_flow" in df.columns:
        df["trade_type"] = df["trade_flow"]

    # Replace inf and -inf values with NaN and fill with 0
    df["unit_price_usd"] = df["unit_price_usd"].replace([np.inf, -np.inf], np.nan)
    df["unit_price_usd"] = df["unit_price_usd"].fillna(0.0)

    # Recalculate unit price safely wherever volume > 0
    valid_mask = df["trade_volume_mt"] > 0
    df.loc[valid_mask, "unit_price_usd"] = (
        df.loc[valid_mask, "trade_value_usd"] / df.loc[valid_mask, "trade_volume_mt"]
    ).round(2)

    return df


def detect_price_anomalies(data=None):
    """Flags price outliers using the IQR method without inf pollution."""
    df = get_clean_data(data)
    if df.empty:
        return pd.DataFrame()

    valid_df = df[df["unit_price_usd"] > 0].copy()
    if valid_df.empty:
        return pd.DataFrame()

    anomaly_frames = []
    for commodity, group in valid_df.groupby("commodity_name"):
        q1 = group["unit_price_usd"].quantile(0.25)
        q3 = group["unit_price_usd"].quantile(0.75)
        iqr = q3 - q1

        lower_limit = max(0, q1 - 1.5 * iqr)
        upper_limit = q3 + 1.5 * iqr

        outliers = group[
            (group["unit_price_usd"] < lower_limit)
            | (group["unit_price_usd"] > upper_limit)
        ].copy()

        outliers["expected_min_price"] = round(lower_limit, 2)
        outliers["expected_max_price"] = round(upper_limit, 2)
        anomaly_frames.append(outliers)

    return (
        pd.concat(anomaly_frames, ignore_index=True)
        if anomaly_frames
        else pd.DataFrame()
    )


def calculate_trade_balance(data=None):
    """Calculates Net Exports vs Imports per country."""
    df = get_clean_data(data)
    if df.empty:
        return pd.DataFrame()

    if "flowCode" in df.columns:
        flow_clean = df["flowCode"].astype(str).str.upper()
        is_export = flow_clean.isin(["X", "2"])
        is_import = flow_clean.isin(["M", "1"])
    else:
        flow_clean = df.get("trade_type", pd.Series(index=df.index, dtype=str))
        flow_clean = flow_clean.astype(str).str.lower()
        is_export = flow_clean.str.contains("export", regex=False)
        is_import = flow_clean.str.contains("import", regex=False)

    df["export_val"] = np.where(is_export, df["trade_value_usd"], 0)
    df["import_val"] = np.where(is_import, df["trade_value_usd"], 0)

    summary = (
        df.groupby("reporter_country")[["export_val", "import_val"]]
        .sum()
        .reset_index()
    )

    summary["total_exports_m_usd"] = (summary["export_val"] / 1000000.0).round(2)
    summary["total_imports_m_usd"] = (summary["import_val"] / 1000000.0).round(2)
    summary["net_trade_balance_m_usd"] = (
        summary["total_exports_m_usd"] - summary["total_imports_m_usd"]
    )

    summary["status"] = np.where(
        summary["net_trade_balance_m_usd"] >= 0, "Trade Surplus", "Trade Deficit"
    )

    return summary[
        [
            "reporter_country",
            "total_exports_m_usd",
            "total_imports_m_usd",
            "net_trade_balance_m_usd",
            "status",
        ]
    ].sort_values(by="net_trade_balance_m_usd", ascending=False)


def forecast_next_period_prices(data=None):
    """Projects future prices using a moving average."""
    df = get_clean_data(data)
    if df.empty:
        return pd.DataFrame()

    valid_df = df[df["unit_price_usd"] > 0]
    grouped = (
        valid_df.groupby(["commodity_name", "trade_date"])["unit_price_usd"]
        .mean()
        .reset_index()
    )

    forecasts = []
    for commodity, group in grouped.groupby("commodity_name"):
        prices = group["unit_price_usd"].values
        if len(prices) > 0:
            hist_mean = np.mean(prices)
            recent_mov_avg = np.mean(prices[-3:]) if len(prices) >= 3 else hist_mean
            forecast_price = round(recent_mov_avg * 1.015, 2)

            forecasts.append(
                {
                    "Commodity": commodity,
                    "Latest Price ($/MT)": round(prices[-1], 2),
                    "Historical Avg ($/MT)": round(hist_mean, 2),
                    "Projected Forecast ($/MT)": forecast_price,
                }
            )

    return pd.DataFrame(forecasts)