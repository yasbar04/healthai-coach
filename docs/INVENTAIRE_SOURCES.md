# PLAN D'ACTION - MISE EN CONFORMITÉ CAHIER DES CHARGES

## LIVRABLES CRITIQUES À GÉNÉRER

### 1️⃣ INVENTAIRE DES SOURCES DE DONNÉES

**Localisation** : `docs/inventaire_sources.md`  
**Effort** : 2h  
**Priorité** : 🔴 CRITIQUE

#### Template à compléter:

```markdown
# Inventaire des Sources de Données - HealthAI Coach

## Sources Internes

### Data 1: Daily Food & Nutrition Dataset
- **URL** : https://www.kaggle.com/datasets/adilshamim8/daily-food-and-nutrition-dataset
- **Format** : CSV
- **Localisation dans le projet** : `app/data/daily_food_nutrition.csv`
- **Fréquence mise à jour** : [À définir: quotidienne/hebdomadaire/mensuelle]
- **Volume** : [Nb lignes, volume MB]
- **Colonnes clés** : Voir liste ci-dessous
- **Justification** : Alimentation de la base nutritionnelle, support des recommandations qualité
- **Règles qualité appliquées** : 
  - Suppression NaN
  - Validation plages valeurs
  - Dédoublonnage

### Data 2: Diet Recommendations Dataset
- **URL** : https://www.kaggle.com/datasets/ziya07/diet-recommendations-dataset
- **Format** : JSON
- **Localisation** : Chargé via seed.py
- **Fréquence** : Statique (bootstrap)
- **Justification** : Profils santé et recommandations initiales
- **Règles qualité** : Validation schéma JSON

### Data 3: ExerciseDB
- **URL** : https://github.com/ExerciseDB/exercisedb-api
- **Format** : REST API + JSON
- **Justification** : Catalogue dynamique d'exercices (1300+ exercices)
- **Fréquence** : Hebdomadaire (sync recommandé)
- **Règles qualité** : Validation structure exercice

### Data 4: Fitness Tracker Dataset (Synthétiques)
- **localisation** : `app/data/fitness_tracker.csv`
- **Format** : CSV
- **Justification** : Données d'entraînement, calories, steps
- **Colonnes** : steps, calories_burned, minutes_activity, user_profile

### Data 5: Gym Members Exercise Dataset (Synthétiques)
- **URL** : https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset
- **Format** : CSV
- **Justification** : Profils utilisateurs avec métriques biométriques
- **Colonnes** : age, gender, weight, height, BPM, calories, BMI, body_fat

## Sources Externes

### [À documenter pour chaque source externe intégrée]

## Règles de Qualité Globales

| Aspect | Règle | Implémentation |
|--------|-------|----------------|
| Complétude | Pas + de 5% valeurs manquantes | Signalé en EtlError |
| Conformité formats | Dates ISO8601, nombres valides | Validation schéma |
| Dédoublonnage | Suppression doublons emails/IDs | Requête SQL DISTINCT |
| Cohérence | Poids/IMC cohérents | Calcul de vérification |
| Fraîcheur | Données < 7 jours | Timestamp last_sync |

## Matrice Traçabilité Données

```
Kaggle Dataset → CSV → seed.py → SQLAlchemy ORM → PostgreSQL → API /nutrition
                                                                 → Dashboard
                                                                 → Analytics
```
```
