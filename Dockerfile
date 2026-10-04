# ==============================================================================
# SatQuery AI — Production Multi-Modal Geospatial Intelligence Container
# ISRO Problem Statement SIH26167
# ==============================================================================

FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

WORKDIR /app

# Install system geospatial libraries (GDAL, PROJ, GEOS) and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and modules
COPY satquery/ /app/satquery/
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY demo_data/ /app/demo_data/
COPY pytest.ini /app/

# Create runtime non-root user and storage directories
RUN useradd -m -u 1000 satquery && \
    mkdir -p /app/storage/uploads /app/storage/aligned /app/storage/exports /app/storage/previews /app/backend/storage && \
    chown -R satquery:satquery /app

USER satquery

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
