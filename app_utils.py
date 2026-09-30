import hashlib
import hmac
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


PROJECT_DIRECTORY = Path(__file__).resolve().parent
LOCAL_DATABASE_PATH = PROJECT_DIRECTORY / "petro_trade.db"
SEED_DATABASE_PATH = PROJECT_DIRECTORY / "petro_trade_seed.db"
DATABASE_PATH = LOCAL_DATABASE_PATH if LOCAL_DATABASE_PATH.exists() else SEED_DATABASE_PATH
USER_DATABASE_PATH = (
    LOCAL_DATABASE_PATH
    if LOCAL_DATABASE_PATH.exists()
    else PROJECT_DIRECTORY / "app_users.db"
)
PASSWORD_ITERATIONS = 240_000


def load_trade_data():
    try:
        with closing(sqlite3.connect(DATABASE_PATH)) as connection:
            data = pd.read_sql_query("SELECT * FROM trade_records", connection)
    except sqlite3.Error:
        return pd.DataFrame()

    if data.empty:
        return data

    if "trade_type" not in data.columns and "trade_flow" in data.columns:
        data["trade_type"] = data["trade_flow"]
    if "trade_date" in data.columns:
        data["trade_date"] = pd.to_datetime(data["trade_date"], errors="coerce")

    volume = pd.to_numeric(data.get("trade_volume_mt"), errors="coerce")
    value = pd.to_numeric(data.get("trade_value_usd"), errors="coerce")
    data["unit_price_usd"] = np.where(volume > 0, value / volume, np.nan)
    data["unit_price_usd"] = data["unit_price_usd"].replace([np.inf, -np.inf], np.nan)
    data["refYear"] = pd.to_numeric(data.get("refYear"), errors="coerce")
    return data


def filter_trade_data(data, key_prefix):
    filtered = data.copy()
    left, right = st.columns(2)

    if "commodity_name" in data.columns:
        commodities = sorted(data["commodity_name"].dropna().astype(str).unique())
        with left:
            selected_commodities = st.multiselect(
                "Commodity",
                commodities,
                default=commodities,
                key=f"{key_prefix}_commodities",
            )
        filtered = filtered[filtered["commodity_name"].isin(selected_commodities)]

    if "refYear" in data.columns:
        years = sorted(data["refYear"].dropna().astype(int).unique().tolist())
        with right:
            selected_years = st.multiselect(
                "Reporting year",
                years,
                default=years,
                key=f"{key_prefix}_years",
            )
        filtered = filtered[filtered["refYear"].isin(selected_years)]

    return filtered


def require_authentication():
    if not st.session_state.get("authenticated_user"):
        st.info("Please sign in to view this project page.")
        if st.button("Go to Login", type="primary"):
            st.switch_page("pages/2_Login_and_Registration.py")
        st.stop()


def register_user(email, password):
    email = email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return False, "Enter a valid email address."
    if len(password) < 8:
        return False, "Use a password with at least 8 characters."

    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    ).hex()

    try:
        with closing(sqlite3.connect(USER_DATABASE_PATH)) as connection:
            with connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS app_users (
                        email TEXT PRIMARY KEY,
                        salt TEXT NOT NULL,
                        password_hash TEXT NOT NULL
                    )"""
                )
                connection.execute(
                    "INSERT INTO app_users (email, salt, password_hash) VALUES (?, ?, ?)",
                    (email, salt.hex(), password_hash),
                )
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    except sqlite3.Error:
        return False, "Could not save the account to the local database."

    return True, "Account created. You can now sign in."


def authenticate_user(email, password):
    email = email.strip().lower()
    try:
        with closing(sqlite3.connect(USER_DATABASE_PATH)) as connection:
            row = connection.execute(
                "SELECT salt, password_hash FROM app_users WHERE email = ?",
                (email,),
            ).fetchone()
    except sqlite3.Error:
        return False

    if row is None:
        return False

    salt, stored_hash = row
    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()
    return hmac.compare_digest(candidate_hash, stored_hash)