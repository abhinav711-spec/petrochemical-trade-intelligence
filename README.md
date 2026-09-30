# Petrochemical Trade Intelligence

Streamlit multipage app for exploring petrochemical trade records, prices, forecasts, and market insights.

## Requirements

- Python 3.10 or newer
- Git access to this private repository

The repository includes `petro_trade_seed.db`, a copy of the trade dataset without local account records. The original `petro_trade.db`, virtual environments, and locally created account databases are not tracked.

## Setup and run

Clone the repository using an account that has been invited to it:

```bash
git clone https://github.com/abhinav711-spec/petrochemical-trade-intelligence.git
cd petrochemical-trade-intelligence
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Windows users can also double-click `run_dashboard.bat` after installing the dependencies.

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. Sign up through Login & Registration to access the analysis pages. Locally created accounts are stored in an ignored SQLite file on that machine.

## Data refresh

The included seed lets a fresh clone run immediately. The dashboard also has a live data refresh control; refreshed data is stored in a local SQLite database and is not automatically synchronized between team members.