import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from app_utils import DATABASE_PATH, require_authentication

# Import the current analysis and ETL functions.
try:
    from deep_analysis import (
        calculate_trade_balance,
        detect_price_anomalies,
        forecast_next_period_prices,
    )
    from fetch_un_comtrade_data import (
        fetch_monthly_comtrade,
        process_and_save_dataset,
    )

    MODULES_FOUND = True
except ImportError:
    MODULES_FOUND = False

# Page Config
st.set_page_config(
    page_title="Main Dashboard | Petrochemical Trade Analytics",
    page_icon="🏭📊",
    layout="wide",
)
require_authentication()

def load_db_records():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query("SELECT * FROM trade_records", conn)
        conn.close()
        if "trade_type" not in df.columns and "trade_flow" in df.columns:
            df["trade_type"] = df["trade_flow"]
        if "unit_price_usd" not in df.columns and "trade_unit_value_usd_mt" in df.columns:
            df["unit_price_usd"] = df["trade_unit_value_usd_mt"]
        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"])
        return df
    except Exception:
        return pd.DataFrame()


# Sidebar Configuration & Data Refresh Trigger
st.sidebar.title("⚙️ Data Controls")

if MODULES_FOUND:
    if st.sidebar.button("🔄 Trigger Live Pipeline Refresh"):
        with st.spinner("Executing ETL Scraper & Updating Database..."):
            raw_data = fetch_monthly_comtrade(start_year=2015, end_year=2025)
            if raw_data is not None:
                process_and_save_dataset(raw_data)
                st.sidebar.success("Database Updated Successfully!")
                st.rerun()
            else:
                st.sidebar.error("Could not fetch data from API endpoint.")

df_raw = load_db_records()

if df_raw.empty:
    st.error("No database records found in 'petro_trade.db'.")
    st.stop()

# Interactive Sidebar Filters
st.sidebar.title("🔍 Global Filters")

available_commodities = (
    df_raw["commodity_name"].dropna().unique().tolist()
    if "commodity_name" in df_raw.columns
    else []
)
selected_commodities = st.sidebar.multiselect(
    "Select Petrochemical Commodity",
    options=available_commodities,
    default=available_commodities,
)

available_years = sorted(df_raw["refYear"].dropna().astype(int).unique().tolist())
selected_years = st.sidebar.multiselect(
    "Reporting year",
    options=available_years,
    default=available_years,
)

df_filtered = df_raw[
    df_raw["commodity_name"].isin(selected_commodities)
    & df_raw["refYear"].isin(selected_years)
]

# Header
st.title("🏭  📊 Petrochemical Trade & Price Intelligence Dashboard")
st.caption(
    "Trade values are reported in USD. Country identifiers are UN numeric codes "
    "because country names are not supplied in the source records."
)
st.markdown("---")

# KPI Summary Section
col1, col2, col3, col4 = st.columns(4)

total_vol = df_filtered["trade_volume_mt"].sum() if not df_filtered.empty else 0
total_val = df_filtered["trade_value_usd"].sum() if not df_filtered.empty else 0

price_data = df_filtered.copy()
price_data["trade_volume_mt"] = pd.to_numeric(
    price_data["trade_volume_mt"], errors="coerce"
)
price_data["trade_value_usd"] = pd.to_numeric(
    price_data["trade_value_usd"], errors="coerce"
)
valid_price_rows = price_data[
    np.isfinite(price_data["trade_volume_mt"])
    & (price_data["trade_volume_mt"] > 0)
    & np.isfinite(price_data["trade_value_usd"])
    & (price_data["trade_value_usd"] >= 0)
]
avg_price = (
    valid_price_rows["trade_value_usd"].sum()
    / valid_price_rows["trade_volume_mt"].sum()
    if not valid_price_rows.empty
    else 0.0
)

col1.metric("Total Volume", f"{total_vol:,.2f} MT")
col2.metric("Total Value", f"${total_val/1e6:,.2f} Million")
col3.metric("Average Price", f"${avg_price:,.2f} / MT")
col4.metric("Active Records", f"{len(df_filtered):,}")
st.caption(
    f"Showing {len(selected_commodities)} commodities across "
    f"{len(selected_years)} reporting years."
)

st.markdown("---")

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Price Trends & Forecast",
    "🌍 Country Volumes & Partners",
    "⚠️ Anomaly Detection",
    "⚖️ Country Trade Balance",
])

# TAB 1: PRICE TRENDS & FORECASTING
# with tab1:
#     st.subheader("Commodity Price Trends & Predictive Forecast")

#     trend_df = (
#         valid_price_rows.groupby(["trade_date", "commodity_name"], as_index=False)
#         .agg(
#             trade_volume_mt=("trade_volume_mt", "sum"),
#             trade_value_usd=("trade_value_usd", "sum"),
#         )
#     )
#     trend_df["unit_price_usd"] = (
#         trend_df["trade_value_usd"] / trend_df["trade_volume_mt"]
#     )

#     if not trend_df.empty:
#         fig_trend = px.line(
#             trend_df,
#             x="trade_date",
#             y="unit_price_usd",
#             color="commodity_name",
#             color_discrete_map={
#                 "Benzene": "#150ED5",
#                 "Propylene": "#F6EA0B",
#                 "Ethylene": "#A7F52A",
#             },
#             markers=True,
#             title="Monthly Unit Price Evolution ($/MT)",
#         )
#         fig_trend.update_layout(template="plotly_white", hovermode="x unified")
#         st.plotly_chart(fig_trend, use_container_width=True)
#         st.caption("Average unit price by reporting period and commodity.")
#         st.dataframe(
#             trend_df.rename(
#                 columns={
#                     "trade_date": "Reporting date",
#                     "commodity_name": "Commodity",
#                     "trade_volume_mt": "Volume (MT)",
#                     "trade_value_usd": "Value (USD)",
#                     "unit_price_usd": "Average price (USD/MT)",
#                 }
#             ).round(
#                 {
#                     "Volume (MT)": 2,
#                     "Value (USD)": 2,
#                     "Average price (USD/MT)": 2,
#                 }
#             ),
#             use_container_width=True,
#             hide_index=True,
#         )
#     else:
#         st.info("No valid price records match these filters.")

#     if MODULES_FOUND:
#         st.markdown("#### 🔮 Moving Average Price Forecasts")
#         forecast_df = forecast_next_period_prices(df_filtered)
#         if not forecast_df.empty:
#             filtered_forecast = forecast_df[
#                 forecast_df["Commodity"].isin(selected_commodities)
#             ]
#             st.dataframe(filtered_forecast, use_container_width=True)
# TAB 1: PRICE TRENDS & FORECAST
with tab1:
    st.subheader("📈 Commodity Price Trends & Period Analysis")

    # Dynamic Time Granularity & Period Slicer Controls
    slice_col1, slice_col2 = st.columns([1, 2])

    with slice_col1:
        time_view = st.radio(
            "Select Time Granularity",
            options=["Monthly Trend", "Annual Average", "Crucial Economic Eras"],
            horizontal=False,
        )

    with slice_col2:
        selected_trend_years = st.multiselect(
            "Filter Tab 1 by year",
            options=available_years,
            default=selected_years,
            key="tab1_year_filter",
        )

    trend_source = df_filtered[
        df_filtered["refYear"].isin(selected_trend_years)
    ].copy()

    # Ensure trade_date is datetime
    if not trend_source.empty and "trade_date" in trend_source.columns:
        trend_source["trade_date"] = pd.to_datetime(trend_source["trade_date"])
        trend_source["year"] = trend_source["trade_date"].dt.year.astype(str)
        trend_source["year_month"] = trend_source[
            "trade_date"
        ].dt.to_period("M").astype(str)

    # Define Crucial Petrochemical Trade Periods & Assigned Colors
    def assign_crucial_period(date):
        if date < pd.Timestamp("2020-01-01"):
            return "Pre-COVID Baseline (2015-2019)"
        elif pd.Timestamp("2020-01-01") <= date <= pd.Timestamp("2021-12-31"):
            return "COVID Supply Chain Shock (2020-2021)"
        elif pd.Timestamp("2022-01-01") <= date <= pd.Timestamp("2023-12-31"):
            return "Energy Crisis & Inflation Peak (2022-2023)"
        else:
            return "Post-Crisis Normalization (2024-2025)"

    color_discrete_map = {
        "Pre-COVID Baseline (2015-2019)": "#2b5c8f",  # Deep Blue
        "COVID Supply Chain Shock (2020-2021)": "#d9534f",  # Warning Red
        "Energy Crisis & Inflation Peak (2022-2023)": "#f0ad4e",  # Amber/Orange
        "Post-Crisis Normalization (2024-2025)": "#5cb85c",  # Green
    }

    # Filter out invalid prices
    price_col = (
        "trade_unit_value_usd_mt"
        if "trade_unit_value_usd_mt" in df_filtered.columns
        else "unit_price_usd"
    )
    valid_trend_df = trend_source[trend_source[price_col] > 0].copy()

    if not valid_trend_df.empty:
        # 1. MONTHLY VIEW
        if time_view == "Monthly Trend":
            monthly_df = (
                valid_trend_df.groupby(["trade_date", "commodity_name"])[
                    price_col
                ]
                .mean()
                .reset_index()
            )

            fig = px.line(
                monthly_df,
                x="trade_date",
                y=price_col,
                color="commodity_name",
                markers=True,
                title="Monthly Average Trade Unit Value ($/MT)",
                labels={
                    price_col: "Trade Unit Value ($/MT)",
                    "trade_date": "Date",
                },
            )

        # 2. ANNUAL VIEW
        elif time_view == "Annual Average":
            annual_df = (
                valid_trend_df.groupby(["year", "commodity_name"])[price_col]
                .mean()
                .reset_index()
            )

            fig = px.bar(
                annual_df,
                x="year",
                y=price_col,
                color="commodity_name",
                barmode="group",
                title="Annual Average Price Comparison ($/MT)",
                labels={
                    price_col: "Avg Trade Unit Value ($/MT)",
                    "year": "Year",
                },
            )

        # 3. CRUCIAL ECONOMIC ERAS VIEW
        else:
            valid_trend_df["crucial_period"] = valid_trend_df[
                "trade_date"
            ].apply(assign_crucial_period)
            era_df = (
                valid_trend_df.groupby([
                    "trade_date",
                    "commodity_name",
                    "crucial_period",
                ])[price_col]
                .mean()
                .reset_index()
            )

            fig = px.scatter(
                era_df,
                x="trade_date",
                y=price_col,
                color="crucial_period",
                size=price_col,
                symbol="commodity_name",
                color_discrete_map=color_discrete_map,
                title="Trade Price Distribution Across Crucial Economic Periods",
                labels={
                    price_col: "Trade Unit Value ($/MT)",
                    "trade_date": "Timeline",
                    "crucial_period": "Economic Period",
                },
            )
            fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="DarkSlateGrey")))

        fig.update_layout(hovermode="x unified", legend_title_text="Series")
        st.plotly_chart(fig, use_container_width=True)

    # Forecast Section
    if MODULES_FOUND:
        st.markdown("---")
        st.markdown("#### 🔮 Moving Average Price Forecasts")
        forecast_df = forecast_next_period_prices(trend_source)
        if not forecast_df.empty and selected_commodities:
            filtered_forecast = forecast_df[
                forecast_df["Commodity"].isin(selected_commodities)
            ]
            st.dataframe(filtered_forecast, use_container_width=True)

# TAB 2: TOP COUNTRIES & PARTNERS
with tab2:
    st.subheader("Trade Volumes and Global Partner Distributions")

    left_col, right_col = st.columns(2)

    with left_col:
        top_reporters = (
            df_filtered.groupby("reporter_country")["trade_volume_mt"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        fig_reporters = px.bar(
            top_reporters,
            x="trade_volume_mt",
            y="reporter_country",
            orientation="h",
            title="Top 10 Reporting Nations by Volume (MT)",
            color="trade_volume_mt",
        )
        fig_reporters.update_layout(yaxis={"categoryorder": "total ascending"})
        fig_reporters.update_layout(template="plotly_white")
        st.plotly_chart(fig_reporters, use_container_width=True)
        st.caption("Reporter IDs are UN numeric codes; values are trade volume in MT.")
        st.dataframe(
            top_reporters.rename(
                columns={"reporter_country": "Reporter UN code", "trade_volume_mt": "Volume (MT)"}
            ).round({"Volume (MT)": 2}),
            use_container_width=True,
            hide_index=True,
        )

    with right_col:
        top_partners = (
            df_filtered.groupby("partner_country")["trade_value_usd"]
            .sum()
            .nlargest(10)
            .reset_index()
        )
        fig_partners = go.Figure()
        total_partner_value = top_partners["trade_value_usd"].sum()
        partner_colors = [
            "#007C91", "#E45756", "#F2B134", "#3B6FB6", "#59A14F",
            "#B279A2", "#FF7F0E", "#17BECF", "#8C564B", "#7A9E2E",
        ]

        if total_partner_value > 0:
            start_angle = 90.0
            for partner_index, partner in top_partners.iterrows():
                partner_name = str(partner["partner_country"])
                trade_value = float(partner["trade_value_usd"])
                share = trade_value / total_partner_value
                angle_span = share * 360.0
                angle_gap = min(1.2, angle_span * 0.1)
                angles = np.radians(
                    np.linspace(
                        start_angle - angle_gap,
                        start_angle - angle_span + angle_gap,
                        max(9, int(angle_span / 5.0) + 1),
                    )
                )
                middle_angle = np.radians(start_angle - angle_span / 2.0)
                offset_x = 0.035 * np.cos(middle_angle)
                offset_y = 0.035 * np.sin(middle_angle)
                radius = 1.0
                thickness = 0.18
                segment_count = len(angles)
                bottom_start = segment_count + 2

                top_vertices = np.column_stack((
                    offset_x + radius * np.cos(angles),
                    offset_y + radius * np.sin(angles),
                    np.full(segment_count, thickness),
                ))
                bottom_vertices = np.column_stack((
                    offset_x + radius * np.cos(angles),
                    offset_y + radius * np.sin(angles),
                    np.zeros(segment_count),
                ))
                vertices = np.vstack((
                    [offset_x, offset_y, thickness],
                    top_vertices,
                    [offset_x, offset_y, 0.0],
                    bottom_vertices,
                ))

                face_i = []
                face_j = []
                face_k = []
                for segment_index in range(segment_count - 1):
                    face_i.extend((0, segment_count + 1))
                    face_j.extend((segment_index + 1, bottom_start + segment_index + 1))
                    face_k.extend((segment_index + 2, bottom_start + segment_index))

                    top_a = segment_index + 1
                    top_b = segment_index + 2
                    bottom_a = bottom_start + segment_index
                    bottom_b = bottom_start + segment_index + 1
                    face_i.extend((top_a, top_b))
                    face_j.extend((bottom_a, bottom_a))
                    face_k.extend((top_b, bottom_b))

                bottom_center = segment_count + 1
                last_top = segment_count
                last_bottom = bottom_start + segment_count - 1
                face_i.extend((0, 1, 0, last_top))
                face_j.extend((bottom_center, bottom_center, bottom_center, bottom_center))
                face_k.extend((1, bottom_start, last_top, last_bottom))

                fig_partners.add_trace(go.Mesh3d(
                    x=vertices[:, 0],
                    y=vertices[:, 1],
                    z=vertices[:, 2],
                    i=face_i,
                    j=face_j,
                    k=face_k,
                    color=partner_colors[partner_index % len(partner_colors)],
                    name=f"{partner_name} ({share:.1%})",
                    showlegend=True,
                    flatshading=True,
                    lighting=dict(
                        ambient=0.45,
                        diffuse=0.8,
                        specular=0.35,
                        roughness=0.55,
                    ),
                    lightposition=dict(x=100, y=150, z=250),
                    hovertemplate=(
                        f"<b>{partner_name}</b><br>Trade value: ${trade_value:,.0f}"
                        f"<br>Share: {share:.1%}<extra></extra>"
                    ),
                ))
                start_angle -= angle_span

            fig_partners.update_layout(
                title="Top 10 Partner Share by Trade Value ($)",
                template="plotly_white",
                height=430,
                margin=dict(l=0, r=0, t=55, b=10),
                legend=dict(
                    x=0.7,
                    y=0.5,
                    xanchor="left",
                    yanchor="middle",
                    font=dict(size=10),
                ),
                scene=dict(
                    domain=dict(x=[0, 0.68], y=[0, 1]),
                    aspectmode="manual",
                    aspectratio=dict(x=1, y=1, z=0.32),
                    camera=dict(eye=dict(x=1.45, y=-1.55, z=1.25)),
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    zaxis=dict(visible=False),
                    bgcolor="rgba(0,0,0,0)",
                ),
            )
            st.plotly_chart(fig_partners, use_container_width=True)
        else:
            st.info("No partner trade values are available for these filters.")
        st.caption("Partner IDs are UN numeric codes; share is based on trade value.")
        st.dataframe(
            top_partners.rename(
                columns={"partner_country": "Partner UN code", "trade_value_usd": "Trade value (USD)"}
            ).round({"Trade value (USD)": 2}),
            use_container_width=True,
            hide_index=True,
        )

# TAB 3: ANOMALY DETECTION
with tab3:
    st.subheader("Flagged Customs Reporting Outliers")
    if MODULES_FOUND:
        anom_df = detect_price_anomalies(df_filtered)
        if not anom_df.empty:
            st.warning(f"Detected {len(anom_df):,} price anomalies in the filtered records.")
            st.caption(
                "An anomaly is a unit price outside its commodity's 1.5× IQR range. "
                "Use the table to compare observed price with the expected range."
            )
            anomaly_columns = [
                column for column in [
                    "refYear", "commodity_name", "reporter_country", "partner_country",
                    "trade_type", "trade_volume_mt", "trade_value_usd", "unit_price_usd",
                    "expected_min_price", "expected_max_price",
                ] if column in anom_df.columns
            ]
            st.dataframe(
                anom_df[anomaly_columns].rename(
                    columns={
                        "refYear": "Year",
                        "commodity_name": "Commodity",
                        "reporter_country": "Reporter UN code",
                        "partner_country": "Partner UN code",
                        "trade_type": "Flow",
                        "trade_volume_mt": "Volume (MT)",
                        "trade_value_usd": "Value (USD)",
                        "unit_price_usd": "Observed price (USD/MT)",
                        "expected_min_price": "Expected minimum (USD/MT)",
                        "expected_max_price": "Expected maximum (USD/MT)",
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No price anomalies detected for current selection.")

# TAB 4: TRADE BALANCE
with tab4:
    st.subheader("Global Net Trade Deficit / Surplus")
    if MODULES_FOUND:
        balance_df = calculate_trade_balance(df_filtered)
        if not balance_df.empty:
            st.caption(
                "Balance = exports minus imports. Country identifiers are UN numeric codes; "
                "amounts are shown in millions of USD."
            )
            fig_balance = px.bar(
                balance_df,
                x="net_trade_balance_m_usd",
                y="reporter_country",
                color="status",
                orientation="h",
                title="Net Trade Balance by Reporter",
                labels={
                    "net_trade_balance_m_usd": "Net balance (million USD)",
                    "reporter_country": "Reporter UN code",
                    "status": "Position",
                },
                color_discrete_map={"Trade Surplus": "#16856b", "Trade Deficit": "#c95045"},
            )
            fig_balance.update_layout(
                template="plotly_white",
                yaxis={"categoryorder": "total ascending"},
            )
            st.plotly_chart(fig_balance, use_container_width=True)
            st.dataframe(
                balance_df.rename(
                    columns={
                        "reporter_country": "Reporter UN code",
                        "total_exports_m_usd": "Exports (million USD)",
                        "total_imports_m_usd": "Imports (million USD)",
                        "net_trade_balance_m_usd": "Net balance (million USD)",
                        "status": "Position",
                    }
                ).round(2),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No trade balance records computed.")

# Data Export
st.markdown("---")
with st.expander("📄 Export Filtered Dataset"):
    st.dataframe(df_filtered, use_container_width=True)
    csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Filtered Data (CSV)",
        csv_bytes,
        "petro_trade_export.csv",
        "text/csv",
    )