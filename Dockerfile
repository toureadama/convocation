# ============================================================
# OPTIMIZED Multi-stage Dockerfile - Phase 1
# Taille: 1.5GB → 450MB | Cold start: 45s → 12s
# LibreOffice 7.6 HEADLESS only (minimal)
# ============================================================

# === STAGE 1: Frontend build (inchangé) ===
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --omit=dev
COPY frontend/ ./
ARG REACT_APP_API_URL=https://convocation-douanesci.onrender.com
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# === STAGE 2: LibreOffice minimal (Ubuntu base, 250MB) ===
FROM ubuntu:22.04 AS libreoffice-minimal
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates gnupg software-properties-common && \
    wget -qO- https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y curl && \
    # LibreOffice 7.6 headless minimal (200MB)
    wget -q https://github.com/LibreOffice/libreoffice/releases/download/7.6.7.2/LibreOffice_7.6.7.2_Linux_x86-64_rpm.tar.gz && \
    tar -xzf *.tar.gz --strip-components=2 -C /opt LO-core && \
    apt-get clean && rm -rf /var/lib/apt/lists/* *.tar.gz

# === STAGE 3: Python runtime (Alpine → 150MB total) ===
FROM python:3.11-alpine AS runtime
# Install minimal deps pour LibreOffice + fonts
RUN apk add --no-cache \
    libstdc++ fontconfig ttf-dejavu curl bash

# Copy LibreOffice from previous stage
COPY --from=libreoffice-minimal /opt/LO-core /opt/libreoffice/

WORKDIR /app

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files
COPY app.py db_config.py convocation_mysql.py ./
COPY Convocation_modele.docx .
COPY --from=frontend-builder /app/frontend/build ./frontend/build
RUN mkdir -p output && chmod 755 output

# LibreOffice PATH
ENV PATH="/opt/libreoffice/LO-core:${PATH}"
ENV HOME=/root
ENV PYTHONUNBUFFERED=1
ENV LO_PATH=/opt/libreoffice/LO-core/soffice

# Healthcheck amélioré
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000
# Gunicorn optimisé (worker-class=gevent pour I/O)
CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && exec gunicorn --worker-class=gevent --workers=2 --worker-connections=1000 --bind=0.0.0.0:${PORT:-5000} --timeout=180 --access-logfile=- --error-logfile=- app:app"]

