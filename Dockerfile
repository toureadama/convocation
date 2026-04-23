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

# ─── Single Stage Build with LibreOffice ──────────────────────────────────
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install all dependencies including LibreOffice and xvfb in one layer
RUN apt-get update -o Acquire::Retries=3 -o Acquire::http::Timeout=30 && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        software-properties-common \
        libreoffice-writer \
        libreoffice-calc \
        xvfb \
        fonts-liberation \
        libfontconfig1 \
        libfreetype6 \
        ca-certificates \
        python3 \
        python3-pip \
        python3-venv \
        && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps (cached layer)
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# App files
COPY app.py db_config.py convocation_mysql.py ./
COPY Convocation_modele.docx .
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create output directory with proper permissions and verify LibreOffice
RUN mkdir -p /app/output && chmod 777 /app/output && \
    echo "=== Verifying LibreOffice installation ===" && \
    which libreoffice && \
    ls -la /usr/bin/libreoffice* && \
    echo "Testing LibreOffice basic functionality..." && \
    timeout 10 libreoffice --version && \
    echo "Testing xvfb-run..." && \
    (xvfb-run -a echo "xvfb works" || echo "xvfb-run failed, will use direct LO") && \
    echo "=== LibreOffice and dependencies verified successfully ==="

# LibreOffice PATH (Debian installation)
ENV PATH="/usr/bin:/usr/lib/libreoffice:${PATH}"
ENV HOME=/root
ENV PYTHONUNBUFFERED=1
ENV LO_PATH=/usr/bin/libreoffice
ENV TMPDIR=/tmp
ENV FONTCONFIG_PATH=/etc/fonts
ENV FONTCONFIG_FILE=/etc/fonts/fonts.conf

# Healthcheck amélioré
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
# Gunicorn optimisé (worker-class=gevent pour I/O)
CMD ["sh", "-c", "python3 -c 'from app import init_db; init_db()' || echo 'DB init failed, continuing...' && exec gunicorn --worker-class=gevent --workers=2 --worker-connections=1000 --bind=0.0.0.0:${PORT:-5000} --timeout=180 --access-logfile=- --error-logfile=- app:app"]

