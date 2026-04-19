# HealthAI Coach API (FastAPI) — backend de démo MSPR

Ce backend est **compatible** avec le front que tu as (endpoints attendus).

## 1) Installation (Windows)

Ouvre PowerShell dans ce dossier puis :

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Lancer l'API

```powershell
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Docs Swagger:
- http://localhost:8010/docs

## 3) Brancher le front

Dans ton front, crée `healthai-front/.env` :

```env
VITE_API_BASE_URL=http://localhost:8010
```

## Comptes de démo

- freemium:  user@demo.fr / Demo123!
- premium:   premium@demo.fr / Demo123!
- premium+:  plus@demo.fr / Demo123!
- b2b:       b2b@demo.fr / Demo123!

## Notes
- DB SQLite locale (fichier `healthai.db`) — suffisant pour la soutenance.
- JWT simple (Bearer token).
- CORS autorisé pour http://localhost:5173
