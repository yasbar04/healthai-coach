# GUIDE DE DÉPLOIEMENT - HealthAI Coach

**Objectif** : Permettre à tout équipe technique de reproduire l'environnement complet  
et lancer la solution en **moins de 30 minutes**.

**Durée estimée** : 
- Première fois (installation complète) : 25-30 minutes
- Démarrages suivants : 2-3 secondes (Docker Compose)

---

## TABLE DES MATIÈRES

1. [Prérequis](#prérequis)
2. [Installation Windows](#windows)
3. [Installation Linux/Mac](#linux)
4. [Deployment avec Docker](#docker)
5. [Vérification fonctionnement](#vérification)
6. [Troubleshooting](#troubleshooting)
7. [Variables d'environnement](#variables)

---

## 1. PRÉREQUIS {#prérequis}

### Minimaux (pour Windows batch scripts)

- **Windows 10/11**
- **Python 3.9+** (vérifier : `python --version`)
- **Node.js 18+** (vérifier : `node --version`)
- **PostgreSQL 12+** OU SQLite (inclus)
- **Git** (optionnel mais recommandé)
- **4 GB RAM disponible**
- **500 MB disque libre**

### Recommandés

- **Docker Desktop 4.0+** (déploiement contenerisé)
- **VS Code** + extensions Python/Node
- **Postman** (test API)
- **DBeaver** (gestion BDD)

---

## 2. INSTALLATION WINDOWS {#windows}

### Option A : Installation classique (Scripts batch)

#### Étape 1 : Vérifier prérequis

```powershell
python --version          # Should return 3.9+
node --version           # Should return 18+
npm --version            # Should return 8+
```

#### Étape 2 : Cloner le projet

```powershell
git clone <repository-url> healthai-coach
cd healthai-coach
```

Ou télécharger le ZIP et décompresser.

#### Étape 3 : Setup backend

```powershell
cd backend\healthai-backend
```

Exécuter le script setup **une seule fois** :

```powershell
.\setup_windows.bat
```

Ce script :
- ✅ Crée virtualenv Python
- ✅ Installe dépendances pip
- ✅ Initialise BDD SQLite
- ✅ Seed données de démo

#### Étape 4 : Setup frontend

```powershell
cd front\healthai-front
npm install           # Installe dépendances Node (~3 min)
```

#### Étape 5 : Lancer l'application

De la racine projet :

```powershell
.\start_all.bat
```

Deux fenêtres CMD se lancent :
- **Backend** : http://localhost:8010
- **Frontend** : http://localhost:5173

✅ **Fait !** L'app est prête.

---

### Option B : Installation avec Docker

#### Étape 1 : Prérequis Docker

```powershell
docker --version        # Should return Docker version 4.0+
docker-compose --version
```

#### Étape 2 : Build images

```powershell
docker-compose build
```

#### Étape 3 : Lancer les services

```powershell
docker-compose up
```

L'app démarre automatiquement :
- Backend : http://localhost:8010
- Frontend : http://localhost:5173
- Database : postgres://localhost:5432

---

## 3. INSTALLATION LINUX/MAC {#linux}

### Prérequis

```bash
python3 --version       # 3.9+
node --version         # 18+
postgresql --version   # Optionnel, SQLite par défaut
```

### Installation

```bash
# Cloner
git clone <repo-url> && cd healthai-coach

# Backend
cd backend/healthai-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed BDD
python3 app/seed.py

# Frontend
cd ../../front/healthai-front
npm install

# Lancer
cd ../../
# Terminal 1: Backend
cd backend/healthai-backend && \
source venv/bin/activate && \
uvicorn app.main:app --reload --port 8010

# Terminal 2: Frontend
cd front/healthai-front && \
npm run dev
```

---

## 4. DÉPLOIEMENT AVEC DOCKER {#docker}

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    container_name: healthai_db
    environment:
      POSTGRES_USER: healthai
      POSTGRES_PASSWORD: ${DB_PASSWORD:-healthai123}
      POSTGRES_DB: healthai_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U healthai"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API
  backend:
    build: ./backend/healthai-backend
    container_name: healthai_backend
    environment:
      - DATABASE_URL=postgresql://healthai:${DB_PASSWORD:-healthai123}@postgres:5432/healthai_db
      - API_PORT=8010
      - CORS_ORIGINS=http://localhost:5173,http://localhost:3000
      - JWT_SECRET=${JWT_SECRET:-your-secret-key-change-in-prod}
    ports:
      - "8010:8010"
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8010

  # Frontend
  frontend:
    build: ./front/healthai-front
    container_name: healthai_frontend
    environment:
      - VITE_API_BASE_URL=http://localhost:8010
    ports:
      - "5173:5173"
    depends_on:
      - backend
    command: npm run dev

volumes:
  postgres_data:
```

### Build et démarrage

```bash
# Build images
docker-compose build

# Démarrer services
docker-compose up -d

# Vérifier status
docker-compose ps

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Arrêter
docker-compose down
```

### Utiliser PostgreSQL en production

```bash
# Variables d'environnement (fichier .env)
DB_PASSWORD=your-strong-password-here
JWT_SECRET=your-jwt-secret-here
```

---

## 5. VÉRIFICATION FONCTIONNEMENT {#vérification}

### 5.1 API Backend

#### Vérifier statut

```bash
curl http://localhost:8010/
# Retour: {"status": "HealthAI API running"}
```

#### Accéder Swagger

```
http://localhost:8010/docs
```

#### Tester authentification

```bash
# Créer compte
curl -X POST http://localhost:8010/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8010/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"Test123!"}'

# Réponse: {"access_token":"eyJ...","token_type":"bearer"}
```

#### Tester endpoint utilisateur

```bash
export TOKEN="<access_token_from_login>"

curl -X GET http://localhost:8010/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### 5.2 Frontend

#### Accéder interface web

```
http://localhost:5173
```

**Page d'accueil** → Cliquer "Login"  
**Credentials démo** :
- Email: `user@demo.fr`
- Password: `Demo123!`

#### Vérifier pages

- ✅ **Dashboard** : Graphiques visibles
- ✅ **Activities** : Liste activités chargée
- ✅ **Nutrition** : Aliments visibles
- ✅ **EtlQuality** : Logs ETL affichés
- ✅ **Users** : Liste utilisateurs (si admin)

### 5.3 Database

#### Accéder BDD (SQLite)

```bash
# SQLite CLI
sqlite3 backend/healthai-backend/healthai.db

# Requêtes test:
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM activities;
SELECT COUNT(*) FROM foods;
```

#### Accéder BDD (PostgreSQL - Docker)

```bash
docker exec -it healthai_db psql -U healthai healthai_db

# Dans psql:
\dt                    # Lister tables
SELECT * FROM users;   # Requêtes
\q                     # Quitter
```

---

## 6. TROUBLESHOOTING {#troubleshooting}

### Problème : "Address already in use"

```
Error: Port 8010 already used
```

**Solution** :
```powershell
# Tuer process sur port 8010
netstat -ano | findstr :8010
taskkill /PID <PID> /F

# Ou utiliser port différent
uvicorn app.main:app --port 8011
```

### Problème : "Module not found"

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution** :
```bash
# Vérifier virtualenv activé
which python    # Doit montrer path avec venv

# Réinstaller
pip install -r requirements.txt
```

### Problème : "Connection refused"

```
requests.exceptions.ConnectionError: ('Connection aborted')
```

**Solution** :
```bash
# Vérifier backend démarre
curl http://localhost:8010

# Vérifier logs
docker-compose logs backend

# Redémarrer
docker-compose restart backend
```

### Problème : "Database locked"

```
sqlite3.OperationalError: database is locked
```

**Solution** :
```bash
# Fermer autres connexions
lsof -i :5432    # Affiche connexions

# Ou supprimer et recréer BDD
rm backend/healthai-backend/healthai.db
python backend/healthai-backend/app/seed.py
```

### Problème : "npm ERR! 404"

```
npm ERR! code E404
```

**Solution** :
```bash
cd front/healthai-front
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 7. VARIABLES D'ENVIRONNEMENT {#variables}

### Backend (.env ou env exports)

```bash
# Base de données
DATABASE_URL=postgresql://user:pass@localhost:5432/healthai_db
# ou SQLite (défaut)
# DATABASE_URL=sqlite:///./healthai.db

# API
API_PORT=8010
API_HOST=0.0.0.0
API_RELOAD=True              # Dev mode

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Sécurité
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=168

# Logs
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend (.env)

```bash
VITE_API_BASE_URL=http://localhost:8010
VITE_APP_TITLE=HealthAI Coach
VITE_DEBUG=false
```

### Charger variables

**Windows** :
```powershell
# Fichier .env dans root project
$env:DATABASE_URL="..."
$env:JWT_SECRET="..."
```

**Linux/Mac** :
```bash
# Fichier .env
source .env

# Ou diriger dans docker-compose
env_file:
  - .env
```

---

## DÉPLOIEMENT EN PRODUCTION

### Préparation

```bash
# Secrets forts
JWT_SECRET=<64 caractères aléatoires>
DB_PASSWORD=<mot de passe très fort>

# Domaine
CORS_ORIGINS=https://healthai-coach.com

# HTTPS obligatoire
DATABASE_URL=postgresql://...
```

### Docker Stack (Swarm) ou Kubernetes

```bash
# Stack Swarm
docker stack deploy -c docker-compose.prod.yml healthai

# Kubernetes
kubectl apply -f k8s/
```

### CI/CD Pipeline

```yaml
# GitHub Actions exemple
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm run build
      - run: docker-compose build && docker-compose push
```

---

## SUPPORT ET AMÉLIORATION

Pour toute question / problème de déploiement :

1. Vérifier logs : `docker-compose logs`
2. Consulter Swagger docs : http://localhost:8010/docs
3. Valider BDD : voir section Vérification

---

**Dernière mise à jour** : [DATE]  
**Version** : 1.0.0  
**Support** : [CONTACT EMAIL]
