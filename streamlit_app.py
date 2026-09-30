import streamlit as st


pages = [
    st.Page("pages/1_Home.py", title="Home", icon=":material/home:", default=True),
    st.Page(
        "pages/2_Login_and_Registration.py",
        title="Login & Registration",
        icon=":material/login:",
    ),
    st.Page("pages/main_dashboard.py", title="Main Dashboard", icon=":material/dashboard:"),
    st.Page(
        "pages/3_Market_Analysis_and_Forecasting.py",
        title="Market Analysis & Forecasting",
        icon=":material/monitoring:",
    ),
    st.Page("pages/4_Market_Insights.py", title="Market Insights", icon=":material/insights:"),
]

st.navigation(pages).run()