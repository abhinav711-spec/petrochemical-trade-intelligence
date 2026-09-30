import streamlit as st

from app_utils import load_trade_data


st.set_page_config(page_title="Home | Petro Trade Intelligence", page_icon="🏭", layout="wide")

data = load_trade_data()
st.title("Petrochemical Trade Intelligence")
st.caption("Explore global trade flows, price movements, and market signals from UN Comtrade data.")
st.divider()

if data.empty:
    st.warning("Trade data is not available yet. Add the project database to get started.")
else:
    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Trade records", f"{len(data):,}")
    metric_two.metric("Commodities", f"{data['commodity_name'].nunique():,}")
    year_values = data["refYear"].dropna()
    metric_three.metric(
        "Data coverage",
        f"{int(year_values.min())}–{int(year_values.max())}" if not year_values.empty else "Not available",
    )

st.subheader("Explore the workspace")
market_column, insights_column, account_column = st.columns(3)
with market_column:
    st.markdown("#### Market Analysis")
    st.write("Compare commodity prices over time and review moving-average forecasts.")
    if st.button("Open analysis", use_container_width=True):
        if st.session_state.get("authenticated_user"):
            st.switch_page("pages/3_Market_Analysis_and_Forecasting.py")
        else:
            st.switch_page("pages/2_Login_and_Registration.py")
with insights_column:
    st.markdown("#### Market Insights")
    st.write("Review trade partners, price anomalies, and country trade balances.")
    if st.button("View insights", use_container_width=True):
        if st.session_state.get("authenticated_user"):
            st.switch_page("pages/4_Market_Insights.py")
        else:
            st.switch_page("pages/2_Login_and_Registration.py")
with account_column:
    st.markdown("#### Your workspace")
    if st.session_state.get("authenticated_user"):
        st.success(f"Signed in as {st.session_state['authenticated_user']}")
        if st.button("Open Main Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/main_dashboard.py")
    else:
        st.write("Sign in or create a local account to access the analysis pages.")
        if st.button("Sign in or register", type="primary", use_container_width=True):
            st.switch_page("pages/2_Login_and_Registration.py")

st.divider()
st.caption("Source: project trade records. Country identifiers follow the source dataset.")