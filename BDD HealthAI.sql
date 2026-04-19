-- ========================================
-- HEALTHAI COACH - DATABASE SCHEMA
-- Application de coaching santé et nutrition
-- ========================================

-- TABLE: Data
-- Description: Données médicales et sanitaires des utilisateurs
-- Contient des informations de profil de santé avec niveaux d'expérience,
-- types de maladies, et indicateurs biologiques clés
CREATE TABLE Data(
   Id_data INT,                          -- Identifiant unique des données de santé
   Experience_Level INT,                 -- Niveau d'expérience sportif (0-10)
   Disease_Type VARCHAR(50),             -- Type de maladie (diabète, hypertension, etc.)
   Severity VARCHAR(50),                 -- Sévérité (légère, modérée, grave)
   Physical_Activity_Level VARCHAR(50),  -- Niveau d'activité physique
   Cholesterol_mg_dL DECIMAL(5,2),       -- Taux de cholestérol en mg/dL
   Blood_Pressure_mmHg DECIMAL(5,2),     -- Tension artérielle en mmHg
   Glucose_mg_dL DECIMAL(5,2),           -- Taux de glucose en mg/dL
   PRIMARY KEY(Id_data)
);

-- TABLE: Nutrition
-- Description: Profil nutritionnel et préférences alimentaires
-- Gère les régimes, restrictions, imbalances et adherence aux plans diététiques
CREATE TABLE Nutrition(
   Id_nutrition INT,                             -- Identifiant unique du profil nutrition
   Meal_Context VARCHAR(50),                     -- Contexte des repas (petit-déj, déjeuner, dîner)
   Adherence_to_Diet_Plan DECIMAL(5,2),          -- % d'adhérence au plan nutritionnel (0-100)
   Preferred_Cuisine VARCHAR(50),                -- Cuisine préférée (italienne, asiatique, etc.)
   Water_Intake INT,                             -- Consommation d'eau quotidienne (L)
   Diet_Recommendation VARCHAR(50),              -- Recommandation diététique (low-carb, équilibré)
   Dietary_Restrictions VARCHAR(50),             -- Restrictions alimentaires (végétarien, sans gluten)
   Dietary_Nutrient_Imbalance_Score INT,         -- Score d'imbalance nutritionnelle (0-100)
   Allergies VARCHAR(50),                        -- Allergies alimentaires
   Low_Carb VARCHAR(50),                         -- Régime pauvre en glucides
   Low_Sodium VARCHAR(50),                       -- Régime pauvre en sodium
   Balanced VARCHAR(50),                         -- Régime équilibré
   PRIMARY KEY(Id_nutrition)
);

-- TABLE: Daily_Data
-- Description: Métriques quotidiennes d'activité et d'exercice
-- Enregistre les données de fréquence cardiaque, calories et type d'exercice journaliers
CREATE TABLE Daily_Data(
   Id_daily INT,              -- Identifiant unique des données journalières
   Max_BPM INT,               -- Fréquence cardiaque maximale (battements/min)
   Resting_BPM INT,           -- Fréquence cardiaque au repos (battements/min)
   Avg_BPM INT,               -- Fréquence cardiaque moyenne (battements/min)
   Exercise_Hours INT,        -- Heures d'exercice quotidien
   Calories_Burned INT,       -- Calories brûlées pendant l'exercice
   Daily_Caloric_Intake INT,  -- Apport calorique total journalier
   Workout_Type VARCHAR(50),  -- Type d'entraînement (cardio, force, yoga, etc.)
   PRIMARY KEY(Id_daily)
);

-- TABLE: Weekly_Data
-- Description: Métriques hebdomadaires de composition corporelle
-- Suivi du poids, masse grasse, IMC et fréquence d'entraînement
CREATE TABLE Weekly_Data(
   Id_weekly INT,         -- Identifiant unique des données hebdomadaires
   Weight DECIMAL(3,2),   -- Poids en kg
   Workout_Frequency INT, -- Nombre d'entraînements par semaine
   Fat_Percentage DECIMAL(3,2), -- Pourcentage de masse grasse (%)
   BMI INT,               -- Indice de Masse Corporelle
   PRIMARY KEY(Id_weekly)
);

-- TABLE: B2B
-- Description: Entreprises partenaires pour les abonnements B2B
-- Contient les informations des organisations utilisant la plateforme
CREATE TABLE B2B(
   Id_entreprise INT,      -- Identifiant unique de l'entreprise
   Name_entreprise VARCHAR(50), -- Nom de l'entreprise
   PRIMARY KEY(Id_entreprise)
);

-- TABLE: Utilisateur
-- Description: Profil utilisateur principal
-- Table centrale contenant les infos personnelles et les références aux données de santé
CREATE TABLE Utilisateur(
   Id INT,                 -- Identifiant unique de l'utilisateur
   Age INT,                -- Âge de l'utilisateur
   Gender VARCHAR(50),     -- Genre (M, F, Autre)
   Name VARCHAR(50),       -- Nom complet de l'utilisateur
   email VARCHAR(50),      -- Adresse email (identifiant unique)
   Id_entreprise INT,      -- Référence à l'entreprise (NULL = particulier)
   Id_data INT NOT NULL,   -- Clé étrangère vers les données de santé
   Id_nutrition INT NOT NULL,    -- Clé étrangère vers le profil nutrition
   Id_daily INT NOT NULL,        -- Clé étrangère vers les données quotidiennes
   Id_weekly INT NOT NULL,       -- Clé étrangère vers les données hebdomadaires
   PRIMARY KEY(Id),
   FOREIGN KEY(Id_entreprise) REFERENCES B2B(Id_entreprise),
   FOREIGN KEY(Id_data) REFERENCES Data(Id_data),
   FOREIGN KEY(Id_nutrition) REFERENCES Nutrition(Id_nutrition),
   FOREIGN KEY(Id_daily) REFERENCES Daily_Data(Id_daily),
   FOREIGN KEY(Id_weekly) REFERENCES Weekly_Data(Id_weekly)
);

-- TABLE: Abonnement
-- Description: Plans d'abonnement et tarification
-- Gère les différents niveaux de service (freemium, premium, premium+, B2B)
CREATE TABLE Abonnement(
   Id_1 INT,              -- Clé étrangère vers utilisateur (partie clé primaire)
   Id_2 INT,              -- Clé étrangère vers utilisateur (partie clé primaire)
   Id INT NOT NULL,       -- Identifiant unique de l'abonnement
   Name VARCHAR(50) NOT NULL,  -- Nom du plan (Freemium, Premium, Premium+)
   Price CURRENCY,             -- Tarif mensuel de l'abonnement
   PRIMARY KEY(Id_1, Id_2),
   FOREIGN KEY(Id_1) REFERENCES Utilisateur(Id),
   FOREIGN KEY(Id_2) REFERENCES Utilisateur(Id)
);

-- TABLE: Aliment
-- Description: Catalogue des aliments avec informations nutritionnelles
-- Contient les propriétés nutritionnelles des aliments pour les analyses diététiques
CREATE TABLE Aliment(
   Id_nutrition INT,      -- Clé étrangère vers profil nutrition (partie clé primaire)
   Id_nutrition_1 INT,    -- Clé étrangère vers profil nutrition (partie clé primaire)
   Food_item VARCHAR(50), -- Nom de l'aliment
   Calories INT,          -- Calories par portion (kcal)
   Protein INT,           -- Protéines (g)
   Carbohydrates INT,     -- Glucides (g)
   Fat INT,               -- Lipides (g)
   Fiber INT,             -- Fibres (g)
   Sugars INT,            -- Sucres (g)
   Sodium INT,            -- Sodium (mg)
   Cholesterol INT,       -- Cholestérol (mg)
   PRIMARY KEY(Id_nutrition, Id_nutrition_1),
   FOREIGN KEY(Id_nutrition) REFERENCES Nutrition(Id_nutrition),
   FOREIGN KEY(Id_nutrition_1) REFERENCES Nutrition(Id_nutrition)
);



-- ========================================
-- SECTION 1: REQUÊTES DE VÉRIFICATION
-- Affiche tous les enregistrements de chaque table
-- ========================================

-- Vérification complète de la table utilisateurs
SELECT * FROM Utilisateur;

-- Vérification complète de la table données de santé
SELECT * FROM Data;

-- Vérification complète de la table nutrition
SELECT * FROM Nutrition;

-- Vérification complète de la table données quotidiennes
SELECT * FROM Daily_Data;

-- Vérification complète de la table données hebdomadaires
SELECT * FROM Weekly_Data;

-- Vérification complète de la table entreprises (B2B)
SELECT * FROM B2B;

-- Vérification complète de la table abonnements
SELECT * FROM Abonnement;

-- Vérification complète de la table aliments
SELECT * FROM Aliment;


-- ========================================
-- SECTION 2: CRUD UTILISATEURS
-- Create, Read, Update, Delete sur la table Utilisateur
-- ========================================

-- CREATE (Insertion): Ajouter un nouvel utilisateur avec tous ses profils
INSERT INTO Utilisateur
VALUES (1, 29, 'Male', 'Lucas Martin', 'lucas@mail.com', 1, 1, 1, 1, 1);

-- READ (Lecture): Récupérer un utilisateur spécifique par ID
SELECT * FROM Utilisateur
WHERE Id = 1;

-- UPDATE (Mise à jour): Mettre à jour l'âge d'un utilisateur
UPDATE Utilisateur
SET Age = 30
WHERE Id = 1;

-- DELETE (Suppression): Supprimer un utilisateur
DELETE FROM Utilisateur
WHERE Id = 1;


-- ========================================
-- SECTION 3: CRUD NUTRITION
-- Gestion des profils nutritionnels des utilisateurs
-- ========================================

-- CREATE (Insertion): Ajouter un nouveau profil nutritionnel
INSERT INTO Nutrition
VALUES (2,'Dinner',70,'Italian',2,'Low Carb','None',8,'None','Yes','No','Yes');

-- READ (Lecture): Afficher tous les profils nutritionnels
SELECT * FROM Nutrition;

-- UPDATE (Mise à jour): Augmenter la consommation d'eau quotidienne
UPDATE Nutrition
SET Water_Intake = 3
WHERE Id_nutrition = 2;

-- DELETE (Suppression): Supprimer un profil nutritionnel
DELETE FROM Nutrition
WHERE Id_nutrition = 2;


-- ========================================
-- SECTION 4: VUES CONSOLIDÉES - DONNÉES UTILISATEUR
-- Affichage complet du profil utilisateur avec tous les détails de santé et fitness
-- ========================================

-- Profil complet utilisateur: infos personnelles + santé + fitness + nutrition
SELECT
u.Name,                      -- Nom de l'utilisateur
u.Age,                        -- Âge
u.Gender,                     -- Genre
d.Disease_Type,              -- Type de maladie
d.Severity,                  -- Sévérité de la maladie
n.Diet_Recommendation,       -- Recommandation diététique
dd.Workout_Type,             -- Type d'entraînement
w.Weight,                    -- Poids actuel
w.BMI                        -- Indice de Masse Corporelle
FROM Utilisateur u
JOIN Data d ON u.Id_data = d.Id_data
JOIN Nutrition n ON u.Id_nutrition = n.Id_nutrition
JOIN Daily_Data dd ON u.Id_daily = dd.Id_daily
JOIN Weekly_Data w ON u.Id_weekly = w.Id_weekly;

-- Association utilisateurs et entreprises (B2B)
-- Affiche les utilisateurs et leur entreprise affiliée (NULL pour les particuliers)
SELECT
u.Name,                   -- Nom de l'utilisateur
b.Name_entreprise         -- Nom de son entreprise (si applicable)
FROM Utilisateur u
LEFT JOIN B2B b
ON u.Id_entreprise = b.Id_entreprise;

-- Statistique: Nombre d'utilisateurs par entreprise
-- Utile pour le reporting B2B et l'analyse de performance par client
SELECT
b.Name_entreprise,                 -- Nom de l'entreprise
COUNT(u.Id) AS Total_Users         -- Nombre total d'utilisateurs
FROM B2B b
LEFT JOIN Utilisateur u
ON b.Id_entreprise = u.Id_entreprise
GROUP BY b.Name_entreprise;

-- Statistique: Distribution des utilisateurs par âge
-- Permet d'analyser la démographie de la plateforme
SELECT Age, COUNT(*) AS Total
FROM Utilisateur
GROUP BY Age
ORDER BY Age;

-- Statistique: Distribution des utilisateurs par genre
-- Analyse du ratio hommes/femmes
SELECT Gender, COUNT(*) AS Total
FROM Utilisateur
GROUP BY Gender;


-- ========================================
-- SECTION 5: ANALYSE FITNESS & EXERCICE
-- Statistiques sur l'activité physique et les calories brûlées
-- ========================================

-- Moyenne des calories brûlées par tous les utilisateurs
-- Indicateur clé de performance d'activité
SELECT AVG(Calories_Burned)
FROM Daily_Data;

-- Moyenne des heures d'exercice quotidiennes
-- Mesure de l'engagement en activité physique
SELECT AVG(Exercise_Hours)
FROM Daily_Data;

-- Types d'entraînement les plus populaires
-- Identifie les préférences d'exercice des utilisateurs
SELECT Workout_Type, COUNT(*) AS Total
FROM Daily_Data
GROUP BY Workout_Type
ORDER BY Total DESC;

-- Moyenne de l'Indice de Masse Corporelle (IMC)
-- Indicateur de santé générale de la communauté
SELECT AVG(BMI)
FROM Weekly_Data;

-- Poids moyen des utilisateurs
-- Suivi de composition corporelle
SELECT AVG(Weight)
FROM Weekly_Data;

-- Fréquence d'entraînement hebdomadaire moyenne
-- Détermine le niveau d'engagement dans l'exercice régulier
SELECT AVG(Workout_Frequency)
FROM Weekly_Data;


-- ========================================
-- SECTION 6: ANALYSE NUTRITIONNELLE
-- Recommandations et adhérence au régime alimentaire
-- ========================================

-- Cuisines préférées par les utilisateurs
-- Aide à comprendre les préférences alimentaires
SELECT Preferred_Cuisine, COUNT(*) AS Total
FROM Nutrition
GROUP BY Preferred_Cuisine;

-- Consommation d'eau quotidienne moyenne
-- Métrique importante d'hydratation
SELECT AVG(Water_Intake)
FROM Nutrition;

-- Score moyen de déséquilibre nutritionnel
-- Évalue la qualité générale des régimes alimentaires
SELECT AVG(Dietary_Nutrient_Imbalance_Score)
FROM Nutrition;


-- ========================================
-- SECTION 7: ALERTES & RISQUES
-- Identification des utilisateurs avec faible adhérence ou risques sanitaires
-- ========================================

-- Utilisateurs avec mauvaise adhérence au régime
-- Adhérence < 50% = suivi diététique problématique
-- Action: Contact pour coaching nutritionnel intensif
SELECT
u.Name,
n.Adherence_to_Diet_Plan
FROM Utilisateur u
JOIN Nutrition n
ON u.Id_nutrition = n.Id_nutrition
WHERE Adherence_to_Diet_Plan < 50;

-- Utilisateurs à risque sanitaire
-- Alerte sur indicateurs biologiques critiques:
-- - Cholestérol > 240 mg/dL (risque élevé cardiovasculaire)
-- - Glucose > 180 mg/dL (diabète non contrôlé)
-- - Tension > 140 mmHg (hypertension sévère)
SELECT
u.Name,
d.Cholesterol_mg_dL,      -- Taux de cholestérol
d.Glucose_mg_dL,          -- Taux de glucose
d.Blood_Pressure_mmHg     -- Tension artérielle
FROM Utilisateur u
JOIN Data d
ON u.Id_data = d.Id_data
WHERE
Cholesterol_mg_dL > 240
OR Glucose_mg_dL > 180
OR Blood_Pressure_mmHg > 140;


-- ========================================
-- SECTION 8: ANALYSE NUTRITIONNELLE AVANCÉE
-- Détails sur les aliments et leurs propriétés nutritionnelles
-- ========================================

-- Afficher tous les aliments du catalogue
-- Contient l'information nutritionnelle détaillée
SELECT * FROM Aliment;

-- Calories moyennes par aliment
-- Aide à évaluer la densité calorique des aliments
SELECT
Food_item,
AVG(Calories)
FROM Aliment
GROUP BY Food_item;

-- Aliments riches en sodium (> 500mg)
-- Identification pour utilisateurs en régime hyposodé
SELECT
Food_item,
Sodium
FROM Aliment
WHERE Sodium > 500;


-- ========================================
-- SECTION 9: TABLEAU DE BORD ANALYTIQUE
-- Vue d'ensemble de la performance globale de la plateforme
-- ========================================

-- Analyse globale: KPIs principaux
-- Fournit une vue d'ensemble en un coup d'œil
SELECT
COUNT(DISTINCT u.Id) AS Total_Users,           -- Nombre total d'utilisateurs
AVG(w.BMI) AS Avg_BMI,                         -- IMC moyen
AVG(dd.Calories_Burned) AS Avg_Calories_Burned, -- Calories brûlées moyennes
AVG(n.Adherence_to_Diet_Plan) AS Avg_Diet_Score -- Score d'adhérence moyen
FROM Utilisateur u
JOIN Weekly_Data w ON u.Id_weekly = w.Id_weekly
JOIN Daily_Data dd ON u.Id_daily = dd.Id_daily
JOIN Nutrition n ON u.Id_nutrition = n.Id_nutrition;


-- ========================================
-- SECTION 10: GESTION DES ABONNEMENTS
-- Analyse des plans d'abonnement et tarification
-- ========================================

-- Afficher tous les abonnements
-- Connaître tous les plans actifs
SELECT * FROM Abonnement;

-- Statistiques d'abonnement par plan
-- Compte le nombre d'utilisateurs par plan de tarification
SELECT
Name,
Price,
COUNT(*) AS Total
FROM Abonnement
GROUP BY Name, Price;

-- Détails complets des utilisateurs et leurs abonnements
-- Lie les utilisateurs à leurs plans spécifiques
SELECT
u.Name,           -- Nom de l'utilisateur
a.Name,           -- Nom du plan d'abonnement
a.Price           -- Prix de l'abonnement
FROM Utilisateur u
JOIN Abonnement a
ON u.Id = a.Id_1;


-- ========================================
-- SECTION 11: PROFIL D'ACTIVITÉ UTILISATEUR
-- Vue complète de l'activité fitness et composition corporelle
-- ========================================

-- Profil complet d'activité par utilisateur
-- Combine exercice quotidien et composition corporelle hebdomadaire
SELECT
u.Name,                    -- Nom de l'utilisateur
dd.Exercise_Hours,         -- Heures d'exercice
dd.Calories_Burned,        -- Calories brûlées
dd.Workout_Type,           -- Type d'entraînement
w.Weight,                  -- Poids
w.BMI                      -- Indice de Masse Corporelle
FROM Utilisateur u
JOIN Daily_Data dd ON u.Id_daily = dd.Id_daily
JOIN Weekly_Data w ON u.Id_weekly = w.Id_weekly;


-- ========================================
-- SECTION 12: EXPORT API - FORMAT JSON
-- Données structurées pour l'export ou l'intégration avec le frontend
-- ========================================

-- Export consolidé pour API/Frontend
-- Récupère les données essentielles nécessaires au dashboard
SELECT
u.Id,                           -- ID utilisateur
u.Name,                         -- Nom complet
u.Age,                          -- Âge
n.Diet_Recommendation,          -- Recommandation diététique actuelle
dd.Calories_Burned,             -- Calories brûlées récemment
w.Weight                        -- Poids actuel
FROM Utilisateur u
JOIN Nutrition n ON u.Id_nutrition = n.Id_nutrition
JOIN Daily_Data dd ON u.Id_daily = dd.Id_daily
JOIN Weekly_Data w ON u.Id_weekly = w.Id_weekly;


-- ========================================
-- SECTION 13: CONTRÔLE DE QUALITÉ
-- Vérification d'intégrité et d'anomalies dans les données
-- ========================================

-- Vérifier les utilisateurs sans email
-- Les emails sont nécessaires pour l'authentification
SELECT *
FROM Utilisateur
WHERE email IS NULL;

-- Vérifier les consommations d'eau anormales
-- Une consommation <= 0 indique une donnée erronée
SELECT *
FROM Nutrition
WHERE Water_Intake <= 0;

