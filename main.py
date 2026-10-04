"""
SatQuery AI — Unified Root Launcher.
Launches the FastAPI backend and serves the interactive frontend at http://localhost:8000.
"""

import sys
from pathlib import Path
import uvicorn

# Reconfigure stdout for utf-8 if needed on Windows
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Ensure root directory and backend directory are in sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == "__main__":
    print("============================================================")
    print("        [+] SatQuery AI -- Starting Local Server            ")
    print("============================================================")
    print("  [*] Web Dashboard : http://localhost:8000")
    print("  [*] Swagger Docs  : http://localhost:8000/docs")
    print("  [*] Health Status : http://localhost:8000/api/health")
    print("============================================================")
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
