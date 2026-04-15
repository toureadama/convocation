# ============================================================
# Dockerfile pour l'application Flask Convocation Douanes CI
# LibreOffice est requis pour la conversion DOCX → PDF
# ============================================================

FROM python:3.11-slim

# Installer LibreOffice + dépendances système
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    default-jre-headless \
    fonts-liberation \
    fonts-dejavu \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer Node.js pour build frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le backend
COPY app.py db_config.py convocation_mysql.py ./
COPY Convocation_modele.docx .

# Build frontend (pass API URL as build arg)
COPY frontend ./frontend
ARG REACT_APP_API_URL=https://convocation-douanesci.onrender.com
RUN cd frontend && npm install && REACT_APP_API_URL=${REACT_APP_API_URL} npm run build

# Créer le dossier output (persistance limitée sur Render Free)
RUN mkdir -p output

# Variable pour LibreOffice headless (évite les erreurs X11)
ENV PYTHONUNBUFFERED=1
ENV HOME=/root

# Port exposé (Render injecte PORT automatiquement)
EXPOSE 5000

# Initialiser la DB puis lancer Gunicorn
CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && gunicorn --workers=2 --bind=0.0.0.0:$PORT --timeout=120 app:app"]
