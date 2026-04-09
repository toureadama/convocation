# 📋 GUIDE DE DÉPLOIEMENT - CONVOCATION DOUANES CI

## 🎯 RÉSUMÉ EXÉCUTIF

**État actuel :** Application prête pour le déploiement ✅

**Services Render existants :**
- **Backend (Flask API)** : https://convocation-douanesci.onrender.com
- **Frontend (React)** : https://convocation-a762.onrender.com
- **Base de données** : MySQL sur Aiven Cloud (mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com:15107)

---

## 🔧 CORRECTIONS APPLIQUÉES

### 1. **app.py** (Ligne 680)
- ✅ **CORRIGÉ** : Syntax error - ligne tronquée dupliquée
- **Avant** : `return jsonify({'error':`
- **Après** : `return jsonify({'error': 'Internal server error'}), 500`

### 2. **frontend/package.json**
- ✅ **CORRIGÉ** : Espace en trop dans l'URL du proxy
- **Avant** : `"proxy": " https://convocation-douanesci.onrender.com"`
- **Après** : `"proxy": "https://convocation-douanesci.onrender.com"`

### 3. **frontend/.env**
- ✅ **CORRIGÉ** : Espace en trop dans l'URL de l'API
- **Avant** : `REACT_APP_API_URL= https://convocation-douanesci.onrender.com`
- **Après** : `REACT_APP_API_URL=https://convocation-douanesci.onrender.com`

---

## 📦 FICHIERS MODIFIÉS

| Fichier | Correction | Impact |
|---------|-----------|--------|
| `app.py` | Syntax error ligne 680 | Backend ne démarrait pas |
| `frontend/package.json` | Espace dans URL proxy | Erreurs de connexion frontend → backend |
| `frontend/.env` | Espace dans URL API | Variables d'environnement incorrectes |

---

## 🚀 PROCESSUS DE DÉPLOIEMENT

### **MÉTHODE 1 : AUTO-DEPLOY (Recommandé)**

Si l'auto-deploy est activé sur Render, le déploiement est **automatique** après un push.

#### Étape 1 : Vérifier les modifications
```bash
# Voir les fichiers modifiés
git status

# Voir les changements
git diff
```

#### Étape 2 : Commiter les corrections
```bash
git add app.py frontend/package.json frontend/.env
git commit -m "fix: corriger syntax error app.py et espaces URLs frontend"
```

#### Étape 3 : Push vers GitHub
```bash
git push origin main
```

#### Étape 4 : Surveiller le déploiement
1. Aller sur https://dashboard.render.com
2. Cliquer sur le service **douanesci-backend**
3. Onglet **Logs** → surveiller le déploiement
4. Répéter pour le service **convocation-a762** (frontend)

#### Étape 5 : Vérifier le déploiement
```bash
# Test backend
curl https://convocation-douanesci.onrender.com/health

# Test frontend
# Ouvrir dans le navigateur : https://convocation-a762.onrender.com
```

---

### **MÉTHODE 2 : DÉPLOIEMENT MANUEL**

Si l'auto-deploy est **désactivé** :

#### Étape 1 : Commiter les modifications
```bash
git add .
git commit -m "fix: corriger syntax error app.py et espaces URLs frontend"
git push origin main
```

#### Étape 2 : Déclencher le déploiement manuel

**Backend :**
1. Dashboard Render → **douanesci-backend**
2. Cliquer **"Manual Deploy"**
3. Sélectionner **"Deploy latest commit"**
4. Branche : `main`

**Frontend :**
1. Dashboard Render → **convocation-a762**
2. Cliquer **"Manual Deploy"**
3. Sélectionner **"Deploy latest commit"**
4. Branche : `main`

---

## ⚙️ CONFIGURATION RENDER

### **Backend (Service Web)**

**Type :** Docker  
**Dockerfile :** `./Dockerfile`  
**Région :** Frankfurt  
**Plan :** Starter (512MB RAM)

**Variables d'environnement requises :**
```
DB_HOST=mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com
DB_PORT=15107
DB_USER=avnadmin
DB_PASSWORD=*** (secret)
DB_NAME=douanesci_convocation
JWT_SECRET_KEY=*** (secret)
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000
```

**Health Check :** `/health`  
**Commande de démarrage :**
```bash
python -c 'from app import init_db; init_db()' && gunicorn --workers=2 --bind=0.0.0.0:$PORT --timeout=120 app:app
```

---

### **Frontend (Site Statique)**

**Build Command :** `npm run build`  
**Publish Directory :** `build`  
**Région :** Frankfurt

**Variables d'environnement requises :**
```
REACT_APP_API_URL=https://convocation-douanesci.onrender.com
```

---

## ✅ CHECKLIST PRÉ-DÉPLOIEMENT

- [x] Correction syntaxique app.py
- [x] Correction URLs frontend (package.json, .env)
- [x] Tests locaux réussis (si possible)
- [x] Variables d'environnement Render configurées
- [x] Git à jour avec les dernières modifications
- [x] Branch : main
- [ ] Commit effectué
- [ ] Push effectué
- [ ] Déploiement backend réussi
- [ ] Déploiement frontend réussi
- [ ] Health check backend OK
- [ ] Test frontend OK

---

## 🧪 TESTS POST-DÉPLOIEMENT

### 1. **Test Backend**
```bash
# Health check
curl https://convocation-douanesci.onrender.com/health

# Expected: {"status":"OK","db":"MySQL douanesci_convocation"}
```

### 2. **Test Login**
```bash
curl -X POST https://convocation-douanesci.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"admin123"}'

# Expected: {"token":"...","user":{...}}
```

### 3. **Test Frontend**
- Ouvrir : https://convocation-a762.onrender.com
- Vérifier que la page de login s'affiche
- Tester la connexion avec admin/admin123

---

## 🚨 DÉPANNAGE

### **Backend ne démarre pas**

**Problème :** Health check failed  
**Solutions :**
1. Vérifier les logs Render → Dashboard → Logs
2. Vérifier les variables d'environnement DB
3. Tester la connexion MySQL depuis Render

**Logs courants :**
```
MySQL Error: Access denied → Vérifier DB_USER/DB_PASSWORD
ModuleNotFoundError → Vérifier requirements.txt
Port already in use → Vérifier variable PORT
```

---

### **Frontend ne voit pas le backend**

**Problème :** Erreurs CORS ou API inaccessible  
**Solutions :**
1. Vider le cache navigateur : `Ctrl + F5` ou `Cmd + Shift + R`
2. Vérifier `REACT_APP_API_URL` dans Render Dashboard
3. Rebuilder le frontend : Dashboard → Manual Deploy → Clear build cache

---

### **Build échoué**

**Problème :** npm install ou build error  
**Solutions :**
```bash
# Tester le build en local
cd frontend
npm install
npm run build

# Vérifier package.json
# S'assurer que toutes les dépendances sont listées
```

---

### **Base de données inaccessible**

**Problème :** MySQL connection timeout  
**Solutions :**
1. Vérifier que Aiven Cloud autorise les connexions depuis Render
2. Whitelist IP Render dans Aiven (si nécessaire)
3. Vérifier les credentials dans Render Dashboard

---

## 📊 COMMANDES UTILES

### Git
```bash
# Statut
git status

# Diff
git diff

# Commit
git add .
git commit -m "message"

# Push
git push origin main

# Annuler dernier commit (soft = garde les fichiers)
git reset --soft HEAD~1

# Forcer un redeploy sans modifications
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Tests locaux
```bash
# Backend
python app.py

# Frontend (autre terminal)
cd frontend
npm start

# Build production
cd frontend
npm run build
```

---

## 🔐 SÉCURITÉ

### **NE JAMAIS COMMITTER :**
- [x] Mots de passe DB (sont dans `.gitignore`)
- [x] JWT_SECRET_KEY (est dans `.gitignore`)
- [x] Fichiers `.env` (est dans `.gitignore`)

### **À faire dans Render Dashboard :**
1. **JWT_SECRET_KEY** : Générer une clé forte
   ```
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. **DB_PASSWORD** : Vérifier qu'il est marqué comme **"Secret"** dans Render
3. **Accès DB** : Restreindre aux IP Render uniquement

---

## 📈 MONITORING

### **Logs Render**
- Dashboard → Service → Logs
- Filtrer par niveau : INFO, ERROR, WARNING

### **Métriques**
- Dashboard → Metrics
- Surveiller : CPU, RAM, Response Time

### **Alertes**
- Configurer des notifications email en cas d'échec de déploiement
- Dashboard → Settings → Notifications

---

## 🔄 WORKFLOW RECOMMANDÉ POUR FUTURES MODIFICATIONS

1. **Modifier le code** en local
2. **Tester localement** (backend + frontend)
3. **Commit** avec message descriptif
4. **Push** vers main
5. **Surveiller** les logs Render
6. **Tester** l'URL de production
7. **Documenter** les changements si nécessaire

---

## 📞 SUPPORT

**Repository GitHub :** https://github.com/toureadama/convocation  
**Render Dashboard :** https://dashboard.render.com  
**Aiven Cloud Console :** https://console.aiven.io/

---

## ✅ STATUT FINAL

**🟢 PRÊT POUR DÉPLOIEMENT**

**Prochaine étape :**
```bash
git add .
git commit -m "fix: corriger syntax error app.py et espaces URLs frontend"
git push origin main
```

Puis surveiller le déploiement automatique sur Render.

---

**Dernière mise à jour :** 9 avril 2026  
**Version :** 1.0.0
