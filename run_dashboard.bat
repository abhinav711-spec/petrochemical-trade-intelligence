@echo off
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo Project virtual environment not found at .venv\Scripts\python.exe
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
pause