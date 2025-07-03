#!/bin/bash

# 🚀 Script de déploiement Universe API
# Usage: ./scripts/deploy.sh [environment] [version]

set -euo pipefail

# 🎨 Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 📝 Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 🔧 Configuration
ENVIRONMENT=${1:-production}
VERSION=${2:-latest}
APP_NAME="universe-api"
DOCKER_IMAGE="universe-api:${VERSION}"
CONTAINER_NAME="${APP_NAME}-${ENVIRONMENT}"

# 📍 Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier que l'image existe
    if [[ "$VERSION" != "latest" ]] && ! docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
        log_error "L'image Docker $DOCKER_IMAGE n'existe pas"
        exit 1
    fi
    
    log_success "Prérequis validés"
}

# 🛑 Arrêt du conteneur existant
stop_existing_container() {
    log_info "Arrêt du conteneur existant..."
    
    if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
        log_success "Conteneur existant arrêté et supprimé"
    else
        log_info "Aucun conteneur existant trouvé"
    fi
}

# 🏗️ Build de l'image (si version latest)
build_image() {
    if [[ "$VERSION" == "latest" ]]; then
        log_info "Construction de l'image Docker..."
        docker build -t "$DOCKER_IMAGE" .
        log_success "Image construite avec succès"
    fi
}

# 🚀 Déploiement
deploy() {
    log_info "Déploiement de l'application..."
    
    # Variables d'environnement selon l'environnement
    case $ENVIRONMENT in
        "production")
            ENV_FILE=".env.production"
            PORT="8000"
            RESTART_POLICY="always"
            ;;
        "staging")
            ENV_FILE=".env.staging"
            PORT="8001"
            RESTART_POLICY="unless-stopped"
            ;;
        "development")
            ENV_FILE=".env"
            PORT="8002"
            RESTART_POLICY="no"
            ;;
        *)
            log_error "Environnement non supporté: $ENVIRONMENT"
            exit 1
            ;;
    esac
    
    # Vérification du fichier d'environnement
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning "Fichier d'environnement $ENV_FILE non trouvé, utilisation de .env"
        ENV_FILE=".env"
    fi
    
    # Démarrage du nouveau conteneur
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart "$RESTART_POLICY" \
        -p "$PORT:8000" \
        --env-file "$ENV_FILE" \
        -e ENVIRONMENT="$ENVIRONMENT" \
        --health-cmd="curl -f http://localhost:8000/health || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-retries=3 \
        --health-start-period=40s \
        "$DOCKER_IMAGE"
    
    log_success "Conteneur déployé avec succès"
    log_info "Application accessible sur http://localhost:$PORT"
}

# 🔍 Vérification du déploiement
verify_deployment() {
    log_info "Vérification du déploiement..."
    
    # Attendre que l'application démarre
    sleep 10
    
    # Obtenir le port du conteneur
    PORT=$(docker port "$CONTAINER_NAME" 8000/tcp | cut -d':' -f2)
    
    # Test de santé
    if curl -f "http://localhost:$PORT/health" &> /dev/null; then
        log_success "Application déployée et fonctionnelle ✅"
        log_info "URL de l'API: http://localhost:$PORT"
        log_info "Documentation: http://localhost:$PORT/docs"
    else
        log_error "Échec de la vérification de santé ❌"
        log_info "Logs du conteneur:"
        docker logs "$CONTAINER_NAME" --tail 20
        exit 1
    fi
}

# 📊 Affichage des informations de déploiement
show_deployment_info() {
    log_info "=== Informations de déploiement ==="
    echo "Environnement: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo "Image: $DOCKER_IMAGE"
    echo "Conteneur: $CONTAINER_NAME"
    echo "Status: $(docker inspect -f '{{.State.Status}}' "$CONTAINER_NAME")"
    echo "Santé: $(docker inspect -f '{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo 'N/A')"
    echo "================================================"
}

# 🎯 Fonction principale
main() {
    log_info "🚀 Démarrage du déploiement Universe API"
    log_info "Environnement: $ENVIRONMENT | Version: $VERSION"
    
    check_prerequisites
    stop_existing_container
    build_image
    deploy
    verify_deployment
    show_deployment_info
    
    log_success "🎉 Déploiement terminé avec succès!"
}

# Gestion des signaux
trap 'log_error "Déploiement interrompu"; exit 1' INT TERM

# Exécution du script principal
main "$@" 