# 🚨 Pipeline Troubleshooting Guide

## Status actuel : Pipeline EN COURS ⚡
- **URL** : https://github.com/Axelmi1/Universe-API/actions/runs/16039768531
- **Démarré** : 2025-07-03 01:54:48 UTC
- **Statut** : `in_progress`

## 🔍 Erreurs probables et solutions

### 1. 🔐 **Secrets manquants** (très probable)

#### ❌ Erreur attendue :
```
Error: Secret DOCKERHUB_USERNAME is not set
Error: Secret DOCKERHUB_TOKEN is not set
```

#### ✅ Solution immédiate :
```
1. Va sur : https://github.com/Axelmi1/Universe-API/settings/secrets/actions
2. Clique "New repository secret"
3. Ajoute ces secrets :

MASTER_API_KEY = test-key
DOCKERHUB_USERNAME = ton-username-dockerhub
DOCKERHUB_TOKEN = ton-token-dockerhub (voir Docker Hub → Account Settings → Security)
```

### 2. 🐳 **Build Docker qui échoue**

#### ❌ Erreurs possibles :
```
Error: permission denied while trying to connect to Docker
Error: failed to solve: dockerfile parse error
```

#### ✅ Solutions :
- **Permission** : GitHub Actions gère Docker automatiquement, pas d'action requise
- **Parse error** : Notre Dockerfile a été testé localement, devrait passer

### 3. 🧪 **Tests qui échouent**

#### ❌ Erreurs possibles :
```
FAILED tests/test_fitness.py::TestFitnessWorkout::test_workout_success
ImportError: No module named 'app'
```

#### ✅ Solutions :
- **Import** : Le workflow installe toutes les dépendances via `requirements.txt`
- **Environment** : Les variables d'environnement sont configurées dans le workflow

### 4. 📡 **Deploy qui échoue** (normal pour l'instant)

#### ❌ Erreur attendue :
```
Error: SSH_KEY secret is not set
Error: PRODUCTION_SERVER secret is not set
```

#### ✅ Solution (optionnelle pour ce test) :
```
# Tu peux désactiver le deploy pour ce test en ajoutant dans ci.yml :
if: false  # Sous le job deploy
```

## 🎯 Success Criteria

### ✅ **Pipeline réussi si :**
1. **Job `tests`** : ✅ (tous les tests passent)
2. **Job `build`** : ✅ ou ⚠️ (si secrets Docker manquants)
3. **Job `integration`** : ✅ (tests avec mocks)
4. **Job `deploy`** : ❌ ou ⚠️ (normal si secrets SSH manquants)
5. **Job `notify`** : ⚠️ (normal si SLACK_WEBHOOK_URL manquant)

### 🏆 **Objectif minimum :**
- **`tests` + `integration` = ✅** = Pipeline fonctionnel !
- Les autres jobs peuvent échouer à cause des secrets manquants

## 🔧 Actions immédiates

### **Option A : Laisser tourner et observer**
- Regarde les jobs tests et integration
- S'ils passent → Pipeline validé ! 🎉

### **Option B : Ajouter les secrets Docker maintenant**
```bash
# 1. Crée un token Docker Hub
# 2. Ajoute DOCKERHUB_USERNAME et DOCKERHUB_TOKEN
# 3. Re-run le workflow failed jobs
```

### **Option C : Simplifier le workflow pour ce test**
```yaml
# Dans .github/workflows/ci.yml, commenter temporairement :
# - deploy (ligne ~80)
# - notify (ligne ~100)
```

## 📊 Monitoring en temps réel

```bash
# Commande pour surveiller (répéter toutes les 30s)
curl -s "https://api.github.com/repos/Axelmi1/Universe-API/actions/runs/16039768531" | grep -E '"status"|"conclusion"'
```

## 🎉 Une fois terminé

### ✅ Si succès :
1. Badge du pipeline sera vert
2. Image Docker sera disponible (si secrets Docker configurés)
3. Pipeline opérationnel pour tous les futurs pushes

### ❌ Si échec partiel :
1. Analyse les logs des jobs échoués
2. Ajoute les secrets manquants
3. Re-run les jobs échoués
4. Ajuste la configuration si nécessaire

---

**Prochaine étape :** Va surveiller le pipeline en direct ! 👀
**URL** : https://github.com/Axelmi1/Universe-API/actions/runs/16039768531 