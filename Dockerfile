# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Africa/Abidjan

# Outils système + libs SIG (GDAL/PROJ/GEOS) + libpq (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gdal-bin libgdal-dev \
    libproj-dev proj-bin \
    libgeos-dev \
    libpq-dev \
    curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Facilite la compilation de certaines wheels GDAL si besoin
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Crée un user non-root
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Dépendances Python
# Assure-toi d'avoir psycopg/psycopg2, django-storages, boto3 dans requirements.txt
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Code de l'app
COPY . .

# Droits
RUN chown -R appuser:appuser /app
USER appuser

# Par défaut : Gunicorn (le docker-compose fera migrate/collectstatic avant)
CMD ["gunicorn", "terra360.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "90"]