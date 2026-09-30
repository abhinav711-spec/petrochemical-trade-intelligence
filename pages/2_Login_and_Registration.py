import streamlit as st

from app_utils import authenticate_user, register_user


st.set_page_config(page_title="Login | Petro Trade Intelligence", page_icon="🔐", layout="centered")
st.title("Welcome back")
st.caption("Sign in to access the project dashboard and market analysis.")

if st.session_state.get("authenticated_user"):
    st.success(f"Signed in as {st.session_state['authenticated_user']}")
    if st.button("Sign out"):
        del st.session_state["authenticated_user"]
        st.rerun()
    if st.button("Continue to Main Dashboard", type="primary"):
        st.switch_page("pages/main_dashboard.py")
else:
    login_tab, register_tab = st.tabs(["Login", "Create account"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email", placeholder="name@example.com")
            login_password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

        if login_submitted:
            if authenticate_user(login_email, login_password):
                st.session_state["authenticated_user"] = login_email.strip().lower()
                st.success("Signed in successfully.")
                st.switch_page("pages/main_dashboard.py")
            else:
                st.error("Email or password was not recognized.")

    with register_tab:
        with st.form("registration_form"):
            register_email = st.text_input("Email address", placeholder="name@example.com")
            register_password = st.text_input("Password", type="password", help="Use at least 8 characters.")
            confirm_password = st.text_input("Confirm password", type="password")
            register_submitted = st.form_submit_button("Create account", use_container_width=True)

        if register_submitted:
            if register_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                created, message = register_user(register_email, register_password)
                if created:
                    st.success(message)
                else:
                    st.error(message)

st.divider()
st.caption("Accounts are stored locally in this project's SQLite database.")