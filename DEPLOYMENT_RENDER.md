# Guide de Déploiement sur Render

## 📋 Prérequis

1. **Compte Render** : Créez un compte sur [render.com](https://render.com)
2. **Repository Git** : Votre code doit être sur GitHub/GitLab
3. **Base de données MySQL** : Déjà configurée sur Aiven

## 🚀 Déploiement Automatique via render.yaml

### Étape 1 : Connecter le Repository

1. Allez sur [Render Dashboard](https://dashboard.render.com/)
2. Cliquez sur **"New +"** → **"Blueprint"**
3. Connectez votre repository GitHub
4. Render détectera automatiquement le fichier `render.yaml`

### Étape 2 : Configurer les Variables d'Environnement

Lors du premier déploiement, Render vous demandera de configurer les variables marquées `sync: false` :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `DB_HOST` | `mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com` | Hôte MySQL |
| `DB_PORT` | `15107` | Port MySQL |
| `DB_USER` | `avnadmin` | Utilisateur MySQL |
| `DB_PASSWORD` | `AVNS_O9FSI98GLiPqRHk5e0H` | Mot de passe MySQL |
| `DB_NAME` | `douanesci_convocation` | Nom de la base |
| `JWT_SECRET_KEY` | *(générer)* | Clé secrète JWT (cliquez sur "Generate") |

### Étape 3 : Déploiement

1. Cliquez sur **"Apply"**
2. Render va :
   - Builder l'image Docker (~5-10 min)
   - Initialiser la base de données
   - Démarrer l'application
3. Une fois terminé, vous obtiendrez une URL comme : `https://douanesci-convocation.onrender.com`

### Étape 4 : Mettre à jour l'URL de l'API

Après le premier déploiement :

1. Allez dans **Render Dashboard** → Votre service → **Environment**
2. Modifiez `REACT_APP_API_URL` avec l'URL de votre service (ex: `https://douanesci-convocation.onrender.com`)
3. Redéployez manuellement ou poussez un nouveau commit

## 🔧 Déploiement Manuel

Si vous préférez déployer manuellement :

### 1. Backend (Docker)

```bash
# Connectez votre repo GitHub à Render
# Render > New + > Web Service > Connect votre repo

# Configuration :
# - Name: douanesci-convocation
# - Runtime: Docker
# - DockerfilePath: ./Dockerfile
# - Region: Frankfurt
# - Plan: Starter
```

### 2. Variables d'Environnement

Ajoutez ces variables dans **Render Dashboard > Environment** :

```bash
DB_HOST=mysql-a54ef6c-toureadama-2bc0.c.aivencloud.com
DB_PORT=15107
DB_USER=avnadmin
DB_PASSWORD=AVNS_O9FSI98GLiPqRHk5e0H
DB_NAME=douanesci_convocation
JWT_SECRET_KEY=<generate-a-secure-key>
FLASK_ENV=production
FLASK_DEBUG=0
PORT=5000
REACT_APP_API_URL=https://votre-app.onrender.com
```

## 🧪 Tests Post-Déploiement

### 1. Vérifier la Santé de l'API

```bash
curl https://votre-app.onrender.com/health
# Doit retourner: {"status": "OK", "db": "MySQL douanesci_convocation"}
```

### 2. Tester la Connexion Admin

```bash
curl -X POST https://votre-app.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"login": "admin", "password": "admin123"}'
```

### 3. Accéder à l'Application

Ouvrez votre navigateur : `https://votre-app.onrender.com`

## 🔐 Sécurité

### ⚠️ IMPORTANT : Changer les Identifiants Admin par Défaut

Après le premier déploiement :

1. Connectez-vous avec `admin` / `admin123`
2. Allez dans **Admin Utilisateurs**
3. Modifiez le mot de passe admin immédiatement
4. Ou créez un nouvel administrateur et supprimez celui par défaut

### Variables Sensibles

Ne jamais committer ces fichiers :
- `.env`
- `secrets.env`
- `db_config.py` (si vous modifiez les credentials)

## 📊 Monitoring

### Logs Render

Accédez aux logs via :
- **Render Dashboard** → Votre service → **Logs**
- Filtrez par : Build, Runtime, ou All

### Commandes Utiles

```bash
# Voir les logs en temps réel
# Via Render Dashboard > Logs tab

# Redémarrer l'application
# Via Render Dashboard > Manual Deploy > Deploy latest commit

# Vérifier l'état
curl https://votre-app.onrender.com/health
```

## 🐛 Résolution de Problèmes

### Le build échoue

**Problème** : Erreur Node.js/npm
```
Solution: Vérifiez que frontend/package.json est valide
```

**Problème** : Erreur MySQL
```
Solution: Vérifiez les variables d'environnement DB_*
```

### L'application ne démarre pas

1. Vérifiez les logs Render
2. Assurez-vous que la DB est accessible
3. Vérifiez `init_db()` dans les logs

### Erreur 500 sur l'API

1. Vérifiez les logs pour les erreurs Python
2. Assurez-vous que toutes les tables DB existent
3. Vérifiez les permissions utilisateur DB

### Frontend ne charge pas

1. Vérifiez que `npm run build` réussit localement
2. Assurez-vous que `REACT_APP_API_URL` est correct
3. Vérifiez la console du navigateur pour les erreurs CORS

## 🔄 Mises à Jour

Pour mettre à jour l'application :

```bash
# 1. Poussez vos changements sur la branche principale
git add .
git commit -m "Description des changements"
git push origin main

# 2. Render rebuild automatiquement
# Attendez 5-10 minutes pour le déploiement
```

## 📝 Notes Importantes

### Limitations Render Free

- **512 MB RAM** : Suffisant pour cette application
- **750 heures/mois** : L'application peut s'arrêter après inactivité
- **Cold starts** : 1-2 minutes après inactivité

### Optimisations

- Le frontend est servi statiquement par Flask (pas de serveur Node en production)
- Gunicorn utilise 2 workers (suffisant pour le plan gratuit)
- Les fichiers PDF générés sont temporaires (non persistants sur Render Free)

## 🆘 Support

Si vous rencontrez des problèmes :

1. Vérifiez les logs Render
2. Consultez la documentation [Render Docs](https://render.com/docs)
3. Vérifiez que votre DB MySQL est accessible depuis Render

---

**Déploiement réussi !** 🎉

URL de l'application : `https://douanesci-convocation.onrender.com`
