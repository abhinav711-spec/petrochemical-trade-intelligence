import plotly.express as px
import streamlit as st

from app_utils import filter_trade_data, load_trade_data, require_authentication
from deep_analysis import calculate_trade_balance, detect_price_anomalies


st.set_page_config(page_title="Market Insights | Petro Trade Intelligence", page_icon="🌍", layout="wide")
require_authentication()

st.title("Market Insights")
st.caption("A filtered view of trade partners, unusual prices, and country-level trade positions.")

data = load_trade_data()
if data.empty:
    st.warning("No trade records are available in the project database.")
    st.stop()

filtered = filter_trade_data(data, "market_insights")
total_value = filtered["trade_value_usd"].sum()
total_volume = filtered["trade_volume_mt"].sum()
metric_one, metric_two, metric_three = st.columns(3)
metric_one.metric("Trade value", f"${total_value / 1_000_000:,.2f}M")
metric_two.metric("Trade volume", f"{total_volume:,.0f} MT")
metric_three.metric("Records in view", f"{len(filtered):,}")

partner_tab, anomaly_tab, balance_tab = st.tabs(["Trade partners", "Price anomalies", "Trade balance"])

with partner_tab:
    st.subheader("Leading trade partners")
    if "partner_country" not in filtered.columns or filtered.empty:
        st.info("No partner records match the current filters.")
    else:
        top_partners = (
            filtered.groupby("partner_country", as_index=False)["trade_value_usd"]
            .sum()
            .nlargest(10, "trade_value_usd")
        )
        figure = px.bar(
            top_partners.sort_values("trade_value_usd"),
            x="trade_value_usd",
            y="partner_country",
            orientation="h",
            labels={"trade_value_usd": "Trade value (USD)", "partner_country": "Partner UN code"},
        )
        st.plotly_chart(figure, use_container_width=True)
        st.caption("Partner identifiers are UN numeric codes from the source records.")
        st.dataframe(
            top_partners.rename(columns={"partner_country": "Partner UN code", "trade_value_usd": "Trade value (USD)"}),
            use_container_width=True,
            hide_index=True,
        )

with anomaly_tab:
    st.subheader("Unusual reported prices")
    anomalies = detect_price_anomalies(filtered)
    if anomalies.empty:
        st.info("No price anomalies were detected in this selection.")
    else:
        st.warning(f"{len(anomalies):,} records fall outside their commodity's expected price range.")
        columns = [
            column for column in [
                "refYear", "commodity_name", "reporter_country", "partner_country",
                "trade_type", "unit_price_usd", "expected_min_price", "expected_max_price",
            ] if column in anomalies.columns
        ]
        st.dataframe(
            anomalies[columns].rename(columns={
                "refYear": "Year",
                "commodity_name": "Commodity",
                "reporter_country": "Reporter UN code",
                "partner_country": "Partner UN code",
                "trade_type": "Flow",
                "unit_price_usd": "Observed USD/MT",
                "expected_min_price": "Expected minimum",
                "expected_max_price": "Expected maximum",
            }).round(2),
            use_container_width=True,
            hide_index=True,
        )

with balance_tab:
    st.subheader("Country trade balance")
    balance = calculate_trade_balance(filtered)
    if balance.empty:
        st.info("No trade balance records could be calculated for this selection.")
    else:
        figure = px.bar(
            balance.sort_values("net_trade_balance_m_usd"),
            x="net_trade_balance_m_usd",
            y="reporter_country",
            color="status",
            orientation="h",
            color_discrete_map={"Trade Surplus": "#16856b", "Trade Deficit": "#c95045"},
            labels={
                "net_trade_balance_m_usd": "Net balance (million USD)",
                "reporter_country": "Reporter UN code",
                "status": "Position",
            },
        )
        st.plotly_chart(figure, use_container_width=True)
        st.caption("Balance is exports minus imports. Country identifiers are UN numeric codes.")
        st.dataframe(balance, use_container_width=True, hide_index=True)