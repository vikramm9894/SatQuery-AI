# SatQuery AI — Deployment & Operations Guide

**Platform:** SatQuery AI (ISRO SIH26167)  
**Supported Deployments:** Docker Compose, Kubernetes, Bare Metal Linux/Windows

---

## 1. Quickstart with Docker Compose

### Prerequisites
- Docker Engine >= 24.0
- Docker Compose >= 2.20

### Steps
1. Clone the repository and navigate to root:
   ```bash
   git clone https://github.com/vikramm9894/SatQuery-AI.git
   cd SatQuery-AI
   ```
2. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Build and start containers:
   ```bash
   docker compose up --build -d
   ```
4. Verify running services:
   ```bash
   docker compose ps
   ```
   - **Frontend UI:** `http://localhost:3000`
   - **Backend API Docs:** `http://localhost:8000/docs`
   - **Healthcheck:** `curl http://localhost:8000/api/health`

---

## 2. Bare-Metal Local Development

### System Requirements
- Python 3.10, 3.11, or 3.12
- GDAL C-libraries (`libgdal-dev` on Ubuntu, GDAL wheel on Windows)

### Linux (Ubuntu/Debian) Setup
```bash
sudo apt-get update
sudo apt-get install -y gdal-bin libgdal-dev libproj-dev libgeos-dev build-essential

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Run FastAPI backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Windows Setup (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Launch using startup script
.\run.ps1
```

---

## 3. Hardware Acceleration & GPU Configuration
SatQuery AI automatically detects CUDA hardware and enables GPU acceleration:
- `ALLOW_GPU=true`: Enables CUDA for PyTorch and ONNX Runtime.
- If GPU is unavailable, the platform seamlessly defaults to quantized CPU inference without degrading analytical accuracy.

---

## 4. Production Security Recommendations
- **Reverse Proxy:** Always place Nginx or Traefik in front of the Uvicorn application to handle SSL/TLS termination.
- **Persistent Storage:** Mount a high-throughput SSD or Cloud Object Storage volume (S3/MinIO) to `/app/storage`.
- **Session Eviction:** Schedule periodic storage eviction (`POST /api/maintenance/cleanup`) to prune stale temporary rasters past the sliding TTL window.
