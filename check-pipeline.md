# 🔍 Pipeline CI/CD - Guide de Vérification

## ✅ Étapes de validation post-push

### 1. **GitHub Actions Dashboard**
```
👉 Va sur: https://github.com/Axelmi1/Universe-API/actions
```

**Cherche le workflow :**
- **Nom** : `CI/CD Pipeline`
- **Trigger** : `push` sur `main`
- **Commit** : `🚀 feat: Complete CI/CD pipeline implementation`

### 2. **Jobs à vérifier (en parallèle)**

| Job | Étapes attendues | Durée estimée |
|-----|------------------|---------------|
| `tests` | setup, install, pytest, coverage | ~2-3 min |
| `build` | setup, docker build, push | ~3-5 min |
| `integration` | setup, tests avec mocks | ~2-3 min |
| `deploy` | SSH, pull, restart | ~1-2 min |
| `notify` | Slack notification | ~30s |

### 3. **Indicateurs de succès**

#### ✅ **Tests Job**
```
✓ Set up Python 3.9
✓ Cache dependencies  
✓ Install dependencies
✓ Run tests with coverage
✓ Upload coverage report
```

#### ✅ **Build Job**  
```
✓ Set up Docker Buildx
✓ Log in to Docker Hub
✓ Build and push Docker image
✓ Image tagged: universe-api:sha-abc123
```

#### ✅ **Deploy Job**
```
✓ Deploy to production
✓ Health check passed
✓ Service running on port 8000
```

### 4. **Vérifications manuelles**

#### **A. Image Docker Hub**
```bash
# Vérifier que l'image a été poussée
curl -s "https://hub.docker.com/v2/repositories/YOUR_USERNAME/universe-api/tags/" | jq '.results[0].name'
```

#### **B. Health Check Local**
```bash
# Si deployment local activé
curl http://localhost:8000/health
# → {"status":"healthy","timestamp":...}
```

#### **C. Tests manuels des endpoints publics**
```bash
# Test metadata sans API key
curl "http://localhost:8000/api/v1/metadata/fitness/fitness-levels"
curl "http://localhost:8000/api/v1/metadata/nutrition/dietary-preferences"
curl "http://localhost:8000/api/v1/metadata/tips/fitness-levels"
```

### 5. **Tests Nightly (optionnel)**

```
👉 Va sur: https://github.com/Axelmi1/Universe-API/actions
👉 Workflows → "Nightly Tests"
👉 Run workflow → Run manually
```

**Attendu :**
- Tests avec vraie API OpenAI
- Génération de rapport HTML
- Upload des artifacts

### 6. **Métriques de performance**

| Métrique | Objectif | Statut |
|----------|----------|--------|
| Build time | < 5 min | ⏱️ |
| Test coverage | > 90% | 📊 |
| Docker image size | < 500MB | 💾 |
| Health check | < 500ms | ⚡ |

### 7. **Dépannage rapide**

#### **Si échec des tests :**
```bash
# Relancer localement
source venv/bin/activate
ENVIRONMENT=test MASTER_API_KEY=test-key python -m pytest tests/ -v
```

#### **Si échec du build Docker :**
```bash
# Test local
docker build -t universe-api:debug .
docker run --rm -p 8000:8000 -e MASTER_API_KEY=test-key universe-api:debug
```

#### **Si échec du déploiement :**
- Vérifier les secrets GitHub (SSH_KEY, PRODUCTION_SERVER)
- Vérifier les permissions SSH
- Vérifier que Docker est installé sur le serveur

---

## 🎯 **Validation finale**

**Le pipeline est opérationnel si :**
- ✅ Tous les jobs GitHub Actions sont verts
- ✅ L'image Docker est disponible sur le registry  
- ✅ Les endpoints répondent correctement
- ✅ Les tests passent en local ET dans le CI
- ✅ La couverture de tests est satisfaisante

**Prochaines étapes :**
1. Configurer les secrets GitHub pour le déploiement
2. Tester le workflow nightly
3. Configurer les notifications Slack
4. Ajouter des badges au README

---

*Pipeline validé le : `date +"%Y-%m-%d %H:%M"`*
*Version : Universe API v2.0.0* 