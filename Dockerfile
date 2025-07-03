# 🐍 Multi-stage build pour optimiser la taille de l'image
FROM python:3.9-slim AS builder

# Variables d'environnement pour optimiser Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installation des dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création d'un utilisateur non-root
RUN useradd --create-home --shell /bin/bash app

# Basculer vers l'utilisateur app pour installer les dépendances
USER app
WORKDIR /home/app

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 🚀 Image de production
FROM python:3.9-slim AS production

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/app/.local/bin:$PATH" \
    ENVIRONMENT=production \
    PORT=8000

# Installation des outils système minimaux
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Création de l'utilisateur app
RUN useradd --create-home --shell /bin/bash app

# Copie des dépendances Python depuis le builder
COPY --from=builder /home/app/.local /home/app/.local

# Création des répertoires nécessaires
WORKDIR /app
RUN chown app:app /app

# Passage à l'utilisateur non-root
USER app

# Copie du code source
COPY --chown=app:app app/ ./app/
COPY --chown=app:app .env* ./

# Exposition du port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Labels pour les métadonnées
LABEL maintainer="Universe API Team" \
      version="2.0.0" \
      description="Universe API - AI-powered health and wellness platform"

# Point d'entrée
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 