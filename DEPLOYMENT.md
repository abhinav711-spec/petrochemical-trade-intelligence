# Run and deploy

## Local

Double-click `run_dashboard.bat`. Keep its console window open while using the app:

http://localhost:8501

The dashboard and ETL scripts now resolve `petro_trade.db` relative to their own files, so they can also be launched from another working directory.

## Stable hosted URL

For a URL that remains available when your PC is off, deploy the project with Streamlit Community Cloud:

1. Push the project source and `petro_trade_seed.db`. This seed contains `trade_records` but no local `app_users` table. Do not push `.venv/`, `app_users.db`, or your original `petro_trade.db`.
2. In Streamlit Community Cloud, create an app from that repository and select `streamlit_app.py` as the main file.
3. Use the app's `*.streamlit.app` URL as the permanent link. It remains the same across app restarts and redeployments.

The database is bundled with the app, so commit and push the updated `petro_trade.db` whenever you refresh it locally. A refresh triggered inside the hosted app writes only to its temporary instance and may be lost when that instance restarts. The free hosting tier may also sleep after inactivity, causing a cold start, but the URL remains unchanged.

Accounts created through Login & Registration are stored in the app's local SQLite database. On hosted instances, local database writes may be temporary and are not a substitute for production authentication or persistent user storage.