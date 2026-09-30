from pathlib import Path
import runpy


dashboard_path = Path(__file__).resolve().parents[1] / "dashboard.py"
runpy.run_path(str(dashboard_path))