# Diagramme des Flux de Données — HealthAI Coach

## Vue d'ensemble

Ce document présente le cheminement complet des données depuis leur collecte brute jusqu'à leur exposition via l'API et leur affichage dans l'interface web.

---

## 1. Diagramme de flux global (DFD niveau 0)

```mermaid
flowchart TD
    subgraph SOURCES["📥 Sources de Données Externes"]
        S1[("🥗 Daily Food & Nutrition\nKaggle — CSV\n650 lignes")]
        S2[("📋 Diet Recommendations\nKaggle — CSV\n1 000 lignes")]
        S3[("💪 Fitness Tracker\nKaggle — CSV\n1 800 lignes")]
        S4[("👥 Gym Members Exercise\nKaggle — CSV\n973 lignes")]
        S5[("🏋️ ExerciseDB API\nREST / JSON\n1 300+ exercices")]
    end

    subgraph ETL["⚙️ Pipeline ETL — APScheduler (etl_scheduler.py)"]
        direction TB
        E1["📥 Ingestion\nLecture CSV / JSON / XLSX\napp/data/*.csv"]
        E2["🔍 Validation de structure\nVérification schéma, types,\nplages de valeurs"]
        E3["🧹 Nettoyage\nSuppression doublons\nTraitement valeurs nulles\nCorrection outliers"]
        E4["📊 Journalisation qualité\nEtlRun — statut exécution\nEtlError — anomalies détectées"]
        E5["✅ Chargement\nseed.py → SQLAlchemy ORM"]

        E1 --> E2 --> E3 --> E5
        E3 --> E4
    end

    subgraph DB["🗄️ Base de Données Relationnelle — SQLite / SQLAlchemy"]
        D1[("👤 Utilisateur")]
        D2[("🥗 Nutrition")]
        D3[("📅 Daily_Data")]
        D4[("📊 Weekly_Data")]
        D5[("🩺 Data — Santé")]
        D6[("💳 Abonnement")]
        D7[("🍎 Aliment")]
        D8[("🏢 B2B")]
        D9[("⚙️ EtlRun / EtlError")]
    end

    subgraph API["🔌 API REST — FastAPI :8010"]
        A1["🔐 /auth — JWT"]
        A2["👤 /users — CRUD"]
        A3["🥗 /nutrition — Logs"]
        A4["💪 /activities — Fitness"]
        A5["📊 /analytics — Tendances"]
        A6["⚙️ /quality — ETL Monitor"]
        A7["📝 /biometrics — Santé"]
        A8["🏋️ /exercises — Catalogue"]
    end

    subgraph FRONT["🖥️ Interface Web — React :5173"]
        F1["📊 Dashboard — KPIs & Graphiques"]
        F2["📝 Journal — Saisie quotidienne"]
        F3["💪 Exercices — Catalogue & Suivi"]
        F4["🥗 Nutrition — Alimentation"]
        F5["⚙️ Qualité ETL — Monitoring"]
        F6["👥 Admin — Gestion utilisateurs"]
    end

    subgraph EXPORT["📤 Export"]
        EX1["📄 JSON"]
        EX2["📊 CSV"]
    end

    %% Collecte
    S1 & S2 & S3 & S4 --> E1
    S5 -->|"Sync hebdomadaire"| E1

    %% ETL → Base
    E5 --> D1 & D2 & D3 & D4 & D5 & D6 & D7 & D8
    E4 --> D9

    %% Base → API
    D1 & D2 & D3 & D4 & D5 --> A2 & A3 & A4 & A5 & A7
    D6 --> A2
    D7 --> A3
    D8 --> A2
    D9 --> A6

    %% API → Frontend
    A1 -->|"Token JWT"| FRONT
    A2 & A3 & A4 & A5 & A6 & A7 & A8 --> F1 & F2 & F3 & F4 & F5 & F6

    %% Export
    F1 & F5 --> EXPORT

    %% Styles
    classDef source fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    classDef etl fill:#fef3c7,stroke:#f59e0b,color:#78350f
    classDef db fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef api fill:#ede9fe,stroke:#7c3aed,color:#3b0764
    classDef front fill:#fce7f3,stroke:#db2777,color:#831843
    classDef export fill:#f3f4f6,stroke:#6b7280,color:#111827

    class S1,S2,S3,S4,S5 source
    class E1,E2,E3,E4,E5 etl
    class D1,D2,D3,D4,D5,D6,D7,D8,D9 db
    class A1,A2,A3,A4,A5,A6,A7,A8 api
    class F1,F2,F3,F4,F5,F6 front
    class EX1,EX2 export
```

---

## 2. Détail du pipeline ETL (DFD niveau 1)

```mermaid
flowchart LR
    subgraph INGEST["Ingestion"]
        I1["Lecture fichier\nCSV / JSON"]
        I2["Parsing\nPandas / json.load"]
        I3["Détection format\net encodage"]
        I1 --> I3 --> I2
    end

    subgraph VALIDATE["Validation"]
        V1["Vérification colonnes\nobligatoires"]
        V2["Contrôle types\n(int, float, str, date)"]
        V3["Vérification plages\n(âge 0-120, IMC 10-60...)"]
        V4["Enregistrement\nerreurs → EtlError"]
        V1 --> V2 --> V3
        V3 -->|"Anomalie"| V4
    end

    subgraph CLEAN["Nettoyage"]
        C1["Suppression doublons\n(email, ID)"]
        C2["Imputation NaN\n(médiane, mode)"]
        C3["Normalisation\n(casse, dates ISO)"]
        C4["Filtrage outliers\n(IQR ×1.5)"]
        C1 --> C2 --> C3 --> C4
    end

    subgraph LOAD["Chargement"]
        L1["Transformation\nSchéma SQLAlchemy"]
        L2["INSERT / UPSERT\nBase SQLite"]
        L3["Mise à jour\nEtlRun (statut, stats)"]
        L1 --> L2 --> L3
    end

    INGEST --> VALIDATE --> CLEAN --> LOAD

    style INGEST fill:#dbeafe,stroke:#3b82f6
    style VALIDATE fill:#fef3c7,stroke:#f59e0b
    style CLEAN fill:#d1fae5,stroke:#059669
    style LOAD fill:#ede9fe,stroke:#7c3aed
```

---

## 3. Flux d'authentification et sécurité

```mermaid
sequenceDiagram
    actor User as 👤 Utilisateur
    participant Front as React (Frontend)
    participant Auth as /auth (FastAPI)
    participant DB as SQLite

    User->>Front: Saisit email + mot de passe
    Front->>Auth: POST /auth/login {email, password}
    Auth->>DB: SELECT user WHERE email = ?
    DB-->>Auth: Utilisateur + hash bcrypt
    Auth->>Auth: Vérifie bcrypt.checkpw()
    Auth-->>Front: 200 OK { token JWT, user }
    Front->>Front: Stocke token (localStorage)
    Front->>Auth: GET /analytics/summary\n[Authorization: Bearer <token>]
    Auth->>Auth: Décode + valide JWT
    Auth-->>Front: 200 OK { données }
    Front-->>User: Affiche Dashboard
```

---

## 4. Planification des tâches ETL automatisées

| Tâche | Déclencheur | Fréquence | Source | Destination |
|-------|-------------|-----------|--------|-------------|
| `sync_food_data` | Cron | Quotidien 00h30 | `daily_food_nutrition.csv` | Table `Nutrition` + `Aliment` |
| `sync_fitness_data` | Cron | Quotidien 01h00 | `fitness_tracker.csv` | Table `Daily_Data` + `Weekly_Data` |
| `data_quality_check` | Cron | Toutes les heures | Toutes les tables | Table `EtlRun` / `EtlError` |
| `sync_exercises` | Manuel / Hebdo | Hebdomadaire | ExerciseDB API | Table `ExerciseCache` |

---

## 5. Règles de qualité appliquées

| Dimension | Règle | Seuil d'alerte | Action corrective |
|-----------|-------|----------------|-------------------|
| **Complétude** | % de valeurs non nulles | < 95 % | Log EtlError, imputation médiane |
| **Unicité** | Doublons sur email/ID | > 0 | Suppression, conservation premier enregistrement |
| **Validité** | Valeurs dans les plages définies | > 1 % hors plage | Écrêtage (clip) aux bornes |
| **Cohérence** | BMI cohérent avec poids/taille | Écart > 5 % | Recalcul BMI |
| **Fraîcheur** | Timestamp dernière sync | > 24 h | Alerte dashboard qualité |
