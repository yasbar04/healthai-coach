# Rapport Technique
## Projet HealthAI Coach – Backend métier & Data Engineering

**Certification** : RNCP36581 – Bloc E6.1  
**Équipe** : Yassine Barhdadi, Ayoub Ramdane, Bilal Mounim, Nemo Langar  
**Date** : Avril 2026

---

## Sommaire

1. Contexte et objectifs
2. Choix technologiques
3. Architecture applicative
4. Qualité des données
5. Difficultés rencontrées
6. Résultats obtenus
7. Perspectives d'évolution
8. Bilan

---

## 1. Contexte et objectifs

HealthAI Coach est une startup française dans le domaine de la santé connectée. L'idée c'est de proposer une plateforme qui combine suivi nutritionnel, coaching sportif et surveillance de données biométriques, le tout alimenté à terme par des modules IA. Le cahier des charges qu'on a reçu fixait trois grandes attentes : monter un référentiel de données fiable, fournir un tableau de bord pour piloter l'activité, et livrer quelque chose d'automatisé et reproductible — pas juste une démo qui fonctionne une fois.

On a structuré le travail en quatre parties : un pipeline ETL pour ingérer et nettoyer les données, une base relationnelle avec ses modèles ORM, une API REST documentée, et une interface web permettant de visualiser les indicateurs. La cible côté déploiement était de rester sous trente minutes sur un poste neuf, que ce soit pour un membre de l'équipe ou quelqu'un qui reprendrait le projet.

Le modèle économique de la startup (freemium, Premium, B2B marque blanche) a directement influencé la structure de notre base de données et la gestion des rôles dans l'API. On a prévu trois niveaux d'accès dès le départ : utilisateur standard, administrateur, et partenaire B2B.

---

## 2. Choix technologiques

Deux critères ont guidé nos décisions tout au long du projet : que la stack reste maintenable par une équipe de quatre, et que les compétences du bloc E6.1 soient couvertes dans leur ensemble. À chaque hésitation, on est revenus sur ces deux points.

**Langage et framework API.** Python 3.11 s'est imposé sans débat : la documentation Pandas est dans la webographie du sujet, l'écosystème data est mature, et utiliser le même langage entre l'ETL et l'API simplifie la reprise. Pour l'API, on est partis sur FastAPI parce qu'il génère automatiquement un schéma OpenAPI (exigé dans le cahier des charges) et intègre Pydantic pour la validation des entrées. Avec Flask ou Django, on aurait recodé à la main ce que FastAPI fait nativement.

**Base de données.** On a choisi SQLite pour la phase de développement, avec SQLAlchemy 2.0 comme couche ORM. Le choix de SQLite n'est pas anodin : dans un contexte de prototype, ça supprime une dépendance externe (pas de serveur PostgreSQL à installer), le fichier de base de données voyage avec le projet, et le déploiement en moins de 30 minutes devient réaliste sans infrastructure. SQLAlchemy nous permet de basculer vers PostgreSQL ou tout autre SGBD en changeant une seule variable d'environnement (`DATABASE_URL`) — c'est d'ailleurs documenté dans le guide de déploiement. Les migrations de schéma sont gérées manuellement via des commandes `ALTER TABLE` exécutées au démarrage de l'API, ce qui reste suffisant pour un projet de cette taille.

**Planification ETL.** On a regardé Airflow et Apache Hop. Airflow c'est puissant, mais c'est aussi un service entier à maintenir, avec son interface, sa base de données de métadonnées, etc. Pour une exécution quotidienne sur trois sources, c'est franchement disproportionné. On a choisi APScheduler, qui tourne dans le même processus Python que l'API. Si le volume explose en phase 2, la migration vers un orchestrateur dédié sera possible sans toucher à la logique métier.

**Interface web.** On a construit le frontend en React 18 avec TypeScript et Vite. Le choix de React plutôt qu'une solution serveur comme Jinja2 s'explique par la dynamique de l'interface qu'on voulait atteindre : graphiques interactifs, mises à jour sans rechargement, gestion fine de l'état d'authentification. Pour les graphiques, on a utilisé Recharts, une librairie native React qui permet de contrôler finement le rendu et l'accessibilité de chaque composant visuel. Côté accessibilité RGAA, écrire les composants nous-mêmes nous a permis de contrôler les attributs `aria-label`, l'ordre de tabulation et les contrastes — ce qu'une solution packagée comme Metabase n'aurait pas permis aussi facilement.

**Déploiement.** En environnement Windows (contexte de développement de l'équipe), on a mis en place des scripts batch (`start_all.bat`, `setup_windows.bat`) qui lancent le backend et le frontend en parallèle en une commande. Le guide de déploiement inclut aussi une configuration Docker Compose pour les environnements Linux et les déploiements en production, avec les variables d'environnement nécessaires.

---

## 3. Architecture applicative

L'application est organisée en trois couches distinctes. Les sources externes (fichiers CSV Kaggle, JSON) entrent par le pipeline ETL, qui écrit dans la base SQLite via les modèles SQLAlchemy. L'API FastAPI devient l'unique point d'entrée pour accéder aux données, que ce soit depuis le frontend React, un outil externe ou un futur service mobile. Le frontend ne contacte jamais la base directement.

**Côté backend**, on a 12 routeurs FastAPI qui couvrent l'ensemble des fonctionnalités : authentification et gestion des sessions (`auth.py`), utilisateurs (`users.py`), activités sportives (`activities.py`), nutrition (`nutrition.py`), données biométriques (`biometrics.py`), analytics (`analytics.py`), qualité ETL (`quality.py`), recommandations IA (`ai.py`), consultations (`consultations.py`), gestion multi-tenant (`tenant.py`), et deux routeurs complémentaires pour le schéma étendu (`bdd.py`, `exercises_ext.py`). Au total l'API expose une quarantaine d'endpoints documentés dans Swagger, accessibles à `http://localhost:8010/docs`.

**Le pipeline ETL** est géré par deux fichiers principaux : `etl_scheduler.py` qui configure les tâches planifiées avec APScheduler, et `seed.py` qui contient la logique d'ingestion et de nettoyage. Trois jobs tournent en arrière-plan : synchronisation des données alimentaires chaque jour à 00h30, synchronisation des données fitness chaque jour à 01h00, et vérification qualité toutes les heures. Les exécutions sont tracées dans deux tables dédiées (`etl_runs` et `etl_errors`) pour permettre la supervision depuis l'interface.

**Côté frontend**, cinq écrans sont disponibles : le Dashboard avec ses métriques et graphiques, la page Activités, la page Nutrition, et deux pages réservées aux administrateurs — la gestion des utilisateurs et la supervision ETL. La navigation adapte les liens affichés selon le rôle de l'utilisateur connecté. Tous les composants partagent le même layout et les mêmes conventions d'accessibilité.

**Le schéma de base de données** compte 13 modèles ORM : les entités métier principales (User, Activity, Food, NutritionLog, Biometrics, Exercise), les entités de tracking ETL (EtlRun, EtlError), et des entités complémentaires pour le schéma étendu (HealthData, DailyData, WeeklyData, B2BCompany). Le fichier `BDD HealthAI.sql` fourni dans le projet permet de recréer la structure complète.

---

## 4. Qualité des données

On a traité la qualité à plusieurs niveaux plutôt que de tout concentrer dans un seul module.

À l'entrée de l'API, Pydantic refuse les valeurs incohérentes avant même qu'elles touchent la base — un âge négatif ou supérieur à 150 ans, un poids à zéro, une date dans le futur pour un log passé : tout ça est rejeté avec un message d'erreur explicite.

Dans le pipeline, `seed.py` applique une série de transformations sur chaque source : conversion de type forcée via Pandas, normalisation de la casse, suppression des doublons sur des clés métier (email pour les utilisateurs, nom normalisé pour les aliments), et rejet des lignes hors bornes (poids supérieur à 500 kg, valeurs caloriques négatives). Les lignes rejetées sont écrites dans la table `etl_errors` avec la sévérité, la référence de la ligne source et le message d'erreur, pour qu'un admin puisse les consulter depuis l'interface EtlQuality.

Chaque exécution du pipeline est rejouable sans effets de bord. Les insertions utilisent la logique "insert ou ignore" pour ne pas créer de doublons si le pipeline est relancé.

Sur les jeux de données fournis (daily_food_nutrition.csv, diet_recommendations.csv, fitness_tracker.csv), les trois sources passent sans anomalie. En conditions réelles, avec de la donnée utilisateur brute, les taux seraient inférieurs — c'est exactement pour ça qu'on a construit ce système de suivi.

---

## 5. Difficultés rencontrées

**Hétérogénéité des sources CSV.** Les fichiers Kaggle n'ont pas du tout le même schéma d'un dataset à l'autre. "Calories", "calories_kcal", "Caloric Value" — c'est la même information mais avec trois noms différents selon la source. On a d'abord essayé de forcer un schéma unique, ce qui obligeait à modifier le code dès qu'on ajoutait un nouveau dataset. On a fini par implémenter un mapping tolérant dans `seed.py` qui teste plusieurs noms de colonnes candidats pour chaque champ attendu. C'est une vingtaine de lignes en plus, mais le pipeline absorbe les variations sans intervention manuelle.

**Gestion des migrations de schéma.** SQLAlchemy crée les tables automatiquement au premier démarrage via `Base.metadata.create_all()`, mais ça ne gère pas les évolutions de schéma sur une base existante. Pour ajouter une colonne à une table déjà créée (par exemple `workout_type` sur `activities`), on a dû mettre en place des commandes `ALTER TABLE` exécutées conditionnellement au démarrage de l'API dans `main.py`. C'est fonctionnel mais pas aussi propre qu'un système de migrations versionné type Alembic — c'est un point qu'on a identifié pour la suite.

**Accessibilité des graphiques.** Recharts génère des éléments SVG, ce qui est mieux qu'un canvas en termes d'accessibilité, mais un SVG brut ne dit pas grand-chose à un lecteur d'écran non plus. On a ajouté des attributs `aria-label` explicites sur chaque graphique, des titres de figure, et on s'est assurés que les couleurs respectent les ratios de contraste RGAA niveau AA. Le dashboard reste lisible et navigable au clavier.

**Synchronisation frontend/backend.** Au début du projet, les types TypeScript du frontend ne correspondaient pas exactement aux schémas Pydantic du backend, ce qui créait des erreurs silencieuses à l'affichage. On a corrigé ça en alignant manuellement les interfaces TypeScript sur les schémas de réponse de l'API, et en testant chaque endpoint depuis le frontend avant de valider l'intégration.

---

## 6. Résultats obtenus

L'ensemble des livrables prévus dans le cahier des charges est produit et fonctionnel. Le pipeline ingère les trois sources de données en un seul run, les données nettoyées sont stockées en base et disponibles via l'API. Le frontend expose les indicateurs métier à travers cinq écrans. L'API est entièrement documentée via Swagger.

| Indicateur | Valeur observée |
|---|---|
| Endpoints API documentés | 44 (12 routeurs) |
| Tables en base de données | 13 modèles ORM |
| Sources de données intégrées | 3 (Kaggle CSV) |
| Rôles utilisateurs gérés | 3 (user, admin, b2b_partner) |
| Taux de succès ETL (données fournies) | 100 % |
| Temps de démarrage API | ~2 secondes |
| Temps de déploiement local (scripts batch) | < 10 minutes |
| Cible cahier des charges | ≤ 30 minutes |

Les données alimentaires, de fitness et les profils utilisateurs sont accessibles au format JSON via l'API et peuvent être exportées en CSV depuis les endpoints correspondants. La documentation OpenAPI générée par FastAPI est complète et à jour à chaque démarrage.

---

## 7. Perspectives d'évolution

**Migration PostgreSQL.** La priorité technique la plus directe est de passer la base de SQLite à PostgreSQL en production. SQLAlchemy isole complètement le code applicatif du moteur de base de données — il suffit de changer la variable `DATABASE_URL` dans le fichier `.env` et d'ajouter les dépendances `psycopg2`. Ce passage permettrait aussi d'activer les extensions `pg_trgm` pour la recherche floue sur les noms d'aliments et d'exercices.

**Migrations versionnées.** Intégrer Alembic remplacerait les `ALTER TABLE` manuels dans `main.py` par un système de migrations versionné et rejouable. C'est un prérequis avant de travailler à plusieurs sur le schéma en parallèle.

**Sécurité API.** L'authentification JWT est en place, mais il faudra ajouter un système de clés API pour les partenaires B2B (table `api_key` liée aux tenants), et du rate limiting pour les endpoints publics.

**Automatisation téléchargement sources.** Aujourd'hui les CSV Kaggle sont téléchargés manuellement et placés dans `app/data/`. L'API Kaggle permettrait d'automatiser ce téléchargement, le token étant stocké dans un secret Docker ou une variable d'environnement.

**Module IA.** L'architecture est prête à accueillir des recommandations personnalisées. Une table `recommendation` peut se greffer directement sur `app_user`, et un endpoint `/api/v1/recommendations/{user_id}` consommerait le modèle sans toucher au reste de l'API.

**Monitoring.** Les logs JSON qu'on génère sont déjà dans un format compatible avec Prometheus. Exposer un endpoint `/metrics` et brancher Grafana serait le prochain chantier pour une supervision en production.

---

## 8. Bilan

Ce qu'on livre correspond à ce que le cahier des charges demandait : pas une démo technique isolée, mais un prototype structuré, documenté et repris par une équipe qui n'a pas participé au développement. Les compétences du bloc E6.1 sont couvertes — collecte et identification des sources, ingestion automatisée, nettoyage et contrôle qualité, modélisation relationnelle, API documentée, visualisation avec accessibilité.

Le choix de SQLite plutôt que PostgreSQL en développement est un compromis conscient : ça simplifie le déploiement initial et correspond à la cible des 30 minutes, tout en laissant ouverte la migration vers un moteur de production sans refactoring. De la même façon, l'ETL intégré dans le processus API plutôt que dans un orchestrateur externe comme Airflow est adapté au volume actuel, avec une voie claire vers plus de robustesse si la volumétrie évolue.

Les fondations sont là pour attaquer la phase 2 sur des données réelles et des modules IA.

---

**Auteurs** : Yassine Barhdadi, Ayoub Ramdane, Bilal Mounim, Nemo Langar  
**Encadrant** : [À compléter]  
**Date** : Avril 2026
