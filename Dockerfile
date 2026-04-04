# ============================================================
# Dockerfile pour l'application Flask Convocation Douanes CI
# LibreOffice est requis pour docx2pdf (conversion DOCX → PDF)
# ============================================================

FROM python:3.11-slim

# Installer LibreOffice + dépendances système
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    default-jre-headless \
    fonts-liberation \
    fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Créer le dossier output (persistance limitée sur Render Free)
RUN mkdir -p output

# Variable pour LibreOffice headless (évite les erreurs X11)
ENV PYTHONUNBUFFERED=1
ENV HOME=/root

# Port exposé (Render injecte PORT automatiquement)
EXPOSE 5000

# Initialiser la DB puis lancer Gunicorn
CMD ["sh", "-c", "python -c 'from app import init_db; init_db()' && gunicorn --workers=2 --bind=0.0.0.0:$PORT --timeout=120 app:app"]
