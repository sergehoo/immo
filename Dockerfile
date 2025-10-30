# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Africa/Abidjan

# --- Outils système + dépendances géospatiales ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin libgdal-dev \
    libproj-dev proj-bin \
    libgeos-dev \
    libpq-dev \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# --- Crée un utilisateur non-root unique ---
RUN adduser --disabled-password --gecos '' app
WORKDIR /app

# --- Installation des dépendances Python ---
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Copie du code source ---
COPY . .

# --- Prépare le dossier staticfiles ---
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R app:app /app && \
    chmod -R 755 /app/staticfiles /app/media

USER app

# --- Commande par défaut (le docker-compose exécutera migrate/collectstatic avant) ---
CMD ["gunicorn", "terra360.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "90"]