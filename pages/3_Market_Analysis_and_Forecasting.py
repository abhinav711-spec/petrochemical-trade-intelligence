import plotly.express as px
import streamlit as st

from app_utils import filter_trade_data, load_trade_data, require_authentication
from deep_analysis import forecast_next_period_prices


st.set_page_config(page_title="Market Analysis | Petro Trade Intelligence", page_icon="📈", layout="wide")
require_authentication()

st.title("Market Analysis & Forecasting")
st.caption("Track reported unit values and compare recent history with a simple moving-average projection.")

data = load_trade_data()
if data.empty:
    st.warning("No trade records are available in the project database.")
    st.stop()

filtered = filter_trade_data(data, "market_analysis")
valid_prices = filtered.dropna(subset=["trade_date", "unit_price_usd"])
valid_prices = valid_prices[valid_prices["unit_price_usd"] > 0]

if valid_prices.empty:
    st.info("No valid price records match the selected filters.")
else:
    view = st.radio(
        "Price view",
        ["Monthly trend", "Annual average"],
        horizontal=True,
    )
    if view == "Monthly trend":
        chart_data = (
            valid_prices.groupby(["trade_date", "commodity_name"], as_index=False)
            .agg(unit_price_usd=("unit_price_usd", "mean"))
        )
        figure = px.line(
            chart_data,
            x="trade_date",
            y="unit_price_usd",
            color="commodity_name",
            markers=True,
            labels={"trade_date": "Reporting date", "unit_price_usd": "USD per MT", "commodity_name": "Commodity"},
        )
    else:
        chart_data = valid_prices.assign(year=valid_prices["trade_date"].dt.year)
        chart_data = (
            chart_data.groupby(["year", "commodity_name"], as_index=False)
            .agg(unit_price_usd=("unit_price_usd", "mean"))
        )
        figure = px.bar(
            chart_data,
            x="year",
            y="unit_price_usd",
            color="commodity_name",
            barmode="group",
            labels={"year": "Year", "unit_price_usd": "Average USD per MT", "commodity_name": "Commodity"},
        )

    figure.update_layout(hovermode="x unified", legend_title_text="Commodity")
    st.plotly_chart(figure, use_container_width=True)

    forecast = forecast_next_period_prices(filtered)
    st.subheader("Moving-average forecast")
    st.caption("Projection uses the recent three-period average with a 1.5% uplift; it is indicative, not a causal forecast.")
    if forecast.empty:
        st.info("There is not enough valid price data to calculate a forecast.")
    else:
        st.dataframe(forecast, use_container_width=True, hide_index=True)