# Guide de Configuration des Environnements

Ce projet supporte deux environnements de déploiement : **développement local** et **production** (Render).

## 🖥️ Configuration en LOCAL

### Backend (Python/Flask)

1. **Créer le fichier `.env.local`** à la racine du projet :
```env
FLASK_ENV=development
JWT_SECRET_KEY=douanes-local-jwt-super-secure-2024
DATABASE_URL=mysql://root:password@localhost:3306/douanesci_convocation
```

2. **Lancer le backend** :
```bash
# Windows
set FLASK_ENV=development && python app.py

# Mac/Linux
export FLASK_ENV=development && python app.py
```

Le backend se lancera sur `http://localhost:5000` avec les CORS configurés pour `http://localhost:3000`.

### Frontend (React)

1. **Le fichier `.env.local`** existe déjà dans `frontend/` :
```env
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENV=local
```

2. **Lancer le frontend** :
```bash
cd frontend
npm start
```

Le frontend se lancera sur `http://localhost:3000`.

---

## 🚀 Configuration en PRODUCTION (Render)

### Backend (Render Dashboard)

Définissez ces variables d'environnement dans le dashboard Render :

```
FLASK_ENV=production
JWT_SECRET_KEY=<votre-clé-secrète-longue-et-sécurisée>
DATABASE_URL=<votre-URL-MySQL-Render>
```

**Le backend sera accessible à :** `https://convocation-douanesci.onrender.com`

### Frontend (Render Dashboard)

Définissez ces variables d'environnement dans le dashboard Render :

```
REACT_APP_API_URL=https://convocation-douanesci.onrender.com
REACT_APP_ENV=production
```

**Le frontend sera accessible à :** `https://convocation-a762.onrender.com`

---

## 🔄 Bascule rapide

### En LOCAL :
```bash
# Backend
python app.py  # Charge automatiquement .env.local

# Frontend
cd frontend
npm start  # Charge automatiquement .env.local
```

### En PRODUCTION :
Les variables d'environnement sont définies dans le dashboard Render.
La bascule se fait automatiquement lors du déploiement.

---

## ⚙️ Configuration CORS

Les origines CORS sont automatiquement configurées selon l'environnement :

**Development** :
- `http://localhost:3000`
- `http://localhost:5000`

**Production** :
- `https://convocation-a762.onrender.com` (Frontend)
- `https://convocation-douanesci.onrender.com` (Backend)

---

## 📋 Structure des fichiers .env

```
projet/
├── .env.local           (backend - local) - NE PAS commiter
├── .env.production      (backend - production) - template uniquement
├── frontend/
│   ├── .env.local       (frontend - local) - NE PAS commiter
│   └── .env.production  (frontend - production) - template uniquement
└── .gitignore           (exclut tous les .env*)
```

---

## 🔐 Sécurité

✅ **Ne jamais commiter les fichiers `.env.local`** (ajoutés dans `.gitignore`)
✅ **Les variables sensibles** (JWT_SECRET_KEY, DATABASE_URL) doivent être définies dans le dashboard Render
✅ **En production**, assurez-vous d'utiliser des clés secrètes fortes et uniques

---

## 🧪 Vérifier la configuration

### Vérifier le backend

```bash
# Health check
curl http://localhost:5000/health
```

### Vérifier le frontend

Ouvrez la console du navigateur (F12) et vérifiez :
```javascript
console.log(process.env.REACT_APP_API_URL)  // http://localhost:5000
console.log(process.env.REACT_APP_ENV)       // local
```

---

## 📝 Commandes utiles

```bash
# Frontend - Local
npm start

# Frontend - Production (local test)
npm run build:prod
npm install -g serve
serve -s build -l 3000

# Backend - Vérifier les dépendances
pip install -r requirements.txt
pip install python-dotenv
```
