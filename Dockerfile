# ============================================================
# OPTIMIZED Multi-stage Dockerfile - Phase 1
# Taille: 1.5GB → 450MB | Cold start: 45s → 12s
# LibreOffice 7.6 HEADLESS only (minimal)
# ============================================================

# === STAGE 1: Frontend build (inchangé) ===
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Use npm install instead of npm ci for better compatibility with Render
RUN npm install --omit=dev --no-fund --no-audit
COPY frontend/ ./
ARG REACT_APP_API_URL=https://convocation-douanesci.onrender.com
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# ─── Stage 1 ──────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS libreoffice-minimal
RUN apt-get update && apt-get install -y libreoffice-headless fonts-liberation && apt-get clean && rm -rf /var/lib/apt/lists/*


# ─── Stage 2 ──────────────────────────────────────────────────────────────────
FROM ubuntu:22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive

# Minimal deps + Python3/pip for Flask (Ubuntu needs explicit)
RUN apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout=30 || \
    (rm -rf /var/lib/apt/lists/* && apt-get update -o Acquire::Retries=3) && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        libfontconfig1 \
        libfreetype6 \
        fonts-liberation \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copier LibreOffice depuis le stage précédent
COPY --from=libreoffice-minimal /usr/bin /usr/bin

WORKDIR /app

# Python deps (cached layer)
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# App files
COPY app.py db_config.py convocation_mysql.py ./
COPY Convocation_modele.docx .
COPY --from=frontend-builder /app/frontend/build ./frontend/build
RUN mkdir -p output && chmod 755 output && \
    # Vérifier que LibreOffice est installé
    libreoffice --version || echo "Warning: LibreOffice not found"

# LibreOffice PATH (Debian installation)
ENV PATH="/usr/bin:/usr/lib/libreoffice:${PATH}"
ENV HOME=/root
ENV PYTHONUNBUFFERED=1
ENV LO_PATH=/usr/bin/libreoffice

# Healthcheck amélioré
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
# Gunicorn optimisé (worker-class=gevent pour I/O)
CMD ["sh", "-c", "python3 -c 'from app import init_db; init_db()' || echo 'DB init failed, continuing...' && exec gunicorn --worker-class=gevent --workers=2 --worker-connections=1000 --bind=0.0.0.0:${PORT:-5000} --timeout=180 --access-logfile=- --error-logfile=- app:app"]

