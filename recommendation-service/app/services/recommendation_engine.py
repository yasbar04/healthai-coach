import uuid
from datetime import datetime
from app.schemas.recommendation import (
    Exercise, ExerciseCategory, FitnessLevelEnum, GoalEnum,
    RecommendationRequest, WorkoutSession,
)

# ─────────────────────────────────────────
# Exercise database
# ─────────────────────────────────────────
EXERCISES: list[Exercise] = [
    # ── Cardio ──────────────────────────────────────────────────────────────
    Exercise(
        id="cardio_001", name="Course à pied", category=ExerciseCategory.cardio,
        muscle_groups=["quadriceps", "mollets", "ischio-jambiers", "core"],
        equipment=[], duration_minutes=30, calories_per_hour=600,
        difficulty=FitnessLevelEnum.beginner,
        description="Cardio fondamental améliorant l'endurance cardiovasculaire.",
        instructions=["Chaussures adaptées", "Cadence confortable", "Respiration régulière", "Hydratation"],
        benefits=["Endurance", "Perte de poids", "Santé cardiaque"],
    ),
    Exercise(
        id="cardio_002", name="Vélo stationnaire", category=ExerciseCategory.cardio,
        muscle_groups=["quadriceps", "mollets", "fessiers"],
        equipment=["vélo"], duration_minutes=30, calories_per_hour=500,
        difficulty=FitnessLevelEnum.beginner,
        description="Cardio faible impact idéal pour les articulations.",
        instructions=["Régler la selle à hauteur de hanche", "Cadence 60-80 RPM", "Résistance progressive"],
        benefits=["Cardio", "Faible impact", "Renforcement jambes"],
    ),
    Exercise(
        id="cardio_003", name="Corde à sauter", category=ExerciseCategory.cardio,
        muscle_groups=["mollets", "épaules", "avant-bras", "core"],
        equipment=["corde"], duration_minutes=15, calories_per_hour=800,
        difficulty=FitnessLevelEnum.intermediate,
        description="Cardio haute intensité excellente pour la coordination.",
        instructions=["Poignets souples", "Sauts sur l'avant-pied", "Dos droit", "Pauses toutes les 2 min"],
        benefits=["Cardio intense", "Coordination", "Agilité"],
    ),
    Exercise(
        id="cardio_004", name="Natation", category=ExerciseCategory.cardio,
        muscle_groups=["dos", "épaules", "core", "bras", "jambes"],
        equipment=["piscine"], duration_minutes=45, calories_per_hour=550,
        difficulty=FitnessLevelEnum.beginner,
        description="Cardio complet sollicitant tous les muscles sans impact.",
        instructions=["Technique de nage avant tout", "Alternez styles", "Repos entre séries"],
        benefits=["Corps complet", "Zéro impact", "Récupération"],
    ),
    Exercise(
        id="cardio_005", name="Vélo de route", category=ExerciseCategory.cardio,
        muscle_groups=["quadriceps", "mollets", "fessiers", "core"],
        equipment=["vélo de route"], duration_minutes=60, calories_per_hour=520,
        difficulty=FitnessLevelEnum.intermediate,
        description="Endurance longue distance idéale pour l'objectif endurance.",
        instructions=["Position aérodynamique", "Gestion de l'effort", "Ravitaillement"],
        benefits=["Endurance longue durée", "Cardio", "Mental"],
    ),
    # ── Force ────────────────────────────────────────────────────────────────
    Exercise(
        id="strength_001", name="Pompes", category=ExerciseCategory.strength,
        muscle_groups=["pectoraux", "triceps", "épaules", "core"],
        equipment=[], duration_minutes=15, calories_per_hour=300,
        difficulty=FitnessLevelEnum.beginner,
        description="Exercice polyarticulaire fondamental pour le haut du corps.",
        instructions=["Mains largeur épaules", "Corps en ligne droite", "Descendre la poitrine au sol", "Expirer en poussant"],
        benefits=["Force haut du corps", "Sans matériel", "Core"],
    ),
    Exercise(
        id="strength_002", name="Squats", category=ExerciseCategory.strength,
        muscle_groups=["quadriceps", "fessiers", "ischio-jambiers", "core"],
        equipment=[], duration_minutes=20, calories_per_hour=350,
        difficulty=FitnessLevelEnum.beginner,
        description="Roi des exercices bas du corps, multi-articulaire.",
        instructions=["Pieds largeur épaules", "Descendre cuisses parallèles", "Genoux dans l'axe des pieds", "Dos droit"],
        benefits=["Force jambes", "Fessiers", "Masse musculaire"],
    ),
    Exercise(
        id="strength_003", name="Développé couché", category=ExerciseCategory.strength,
        muscle_groups=["pectoraux", "triceps", "épaules antérieures"],
        equipment=["banc", "barre"], duration_minutes=25, calories_per_hour=280,
        difficulty=FitnessLevelEnum.intermediate,
        description="Exercice emblématique pour le développement pectoral.",
        instructions=["Prise légèrement plus large que les épaules", "Descendre à la poitrine", "Pousser explosif", "Partenaire recommandé"],
        benefits=["Force pectoraux", "Volume haut du corps", "Puissance"],
    ),
    Exercise(
        id="strength_004", name="Tractions (Pull-ups)", category=ExerciseCategory.strength,
        muscle_groups=["grand dorsal", "biceps", "rhomboïdes", "core"],
        equipment=["barre de traction"], duration_minutes=20, calories_per_hour=290,
        difficulty=FitnessLevelEnum.intermediate,
        description="Exercice de tirage au poids du corps excellent pour le dos.",
        instructions=["Prise pronation", "Corps immobile", "Monter menton au-dessus de la barre", "Descente contrôlée"],
        benefits=["Force dos", "Biceps", "Fonctionnel"],
    ),
    Exercise(
        id="strength_005", name="Soulevé de terre", category=ExerciseCategory.strength,
        muscle_groups=["ischio-jambiers", "fessiers", "dos", "trapèzes", "core"],
        equipment=["barre", "poids"], duration_minutes=30, calories_per_hour=400,
        difficulty=FitnessLevelEnum.advanced,
        description="Exercice roi de la force globale.",
        instructions=["Dos plat obligatoire", "Barre près du corps", "Pousser avec les jambes", "Engagement du core"],
        benefits=["Force globale", "Chaîne postérieure", "Puissance maximale"],
    ),
    Exercise(
        id="strength_006", name="Fentes", category=ExerciseCategory.strength,
        muscle_groups=["quadriceps", "fessiers", "ischio-jambiers", "mollets"],
        equipment=[], duration_minutes=20, calories_per_hour=330,
        difficulty=FitnessLevelEnum.beginner,
        description="Exercice unilatéral excellent pour la symétrie et l'équilibre.",
        instructions=["Grand pas en avant", "Genou arrière effleurer le sol", "Revenir position initiale", "Alterner jambes"],
        benefits=["Équilibre", "Symétrie musculaire", "Fessiers"],
    ),
    Exercise(
        id="strength_007", name="Développé militaire", category=ExerciseCategory.strength,
        muscle_groups=["deltoïdes", "triceps", "trapèzes"],
        equipment=["barre", "haltères"], duration_minutes=20, calories_per_hour=270,
        difficulty=FitnessLevelEnum.intermediate,
        description="Exercice de presse au-dessus de la tête pour les épaules.",
        instructions=["Debout ou assis", "Core engagé", "Pousser barre verticalement", "Ne pas cambrer"],
        benefits=["Épaules", "Stabilité", "Force fonctionnelle"],
    ),
    Exercise(
        id="strength_008", name="Dips", category=ExerciseCategory.strength,
        muscle_groups=["triceps", "pectoraux", "épaules antérieures"],
        equipment=["barres parallèles"], duration_minutes=15, calories_per_hour=260,
        difficulty=FitnessLevelEnum.intermediate,
        description="Exercice de pression au poids du corps pour le bas du pectoral et les triceps.",
        instructions=["Corps légèrement incliné", "Descendre jusqu'à 90°", "Pousser et verrouiller"],
        benefits=["Triceps", "Pectoraux bas", "Force fonctionnelle"],
    ),
    # ── HIIT ─────────────────────────────────────────────────────────────────
    Exercise(
        id="hiit_001", name="Burpees", category=ExerciseCategory.hiit,
        muscle_groups=["corps entier", "cardio"],
        equipment=[], duration_minutes=15, calories_per_hour=700,
        difficulty=FitnessLevelEnum.intermediate,
        description="Exercice corps entier haute intensité, cardio et force.",
        instructions=["Position debout", "Saut en arrière en planche", "Pompe optionnelle", "Ramener pieds", "Saut avec bras en l'air"],
        benefits=["Cardio intense", "Corps entier", "Brûle-graisses"],
    ),
    Exercise(
        id="hiit_002", name="Mountain Climbers", category=ExerciseCategory.hiit,
        muscle_groups=["core", "épaules", "quadriceps", "cardio"],
        equipment=[], duration_minutes=10, calories_per_hour=650,
        difficulty=FitnessLevelEnum.beginner,
        description="Exercice de gainage dynamique haute intensité.",
        instructions=["Position planche haute", "Amener genoux vers la poitrine alternativement", "Cadence rapide", "Core serré"],
        benefits=["Core", "Cardio", "Coordination"],
    ),
    Exercise(
        id="hiit_003", name="Jump Squats", category=ExerciseCategory.hiit,
        muscle_groups=["quadriceps", "fessiers", "mollets", "cardio"],
        equipment=[], duration_minutes=15, calories_per_hour=680,
        difficulty=FitnessLevelEnum.intermediate,
        description="Squat explosif avec saut pour puissance et cardio.",
        instructions=["Squat complet", "Sauter explosivement", "Réception souple", "Enchaîner"],
        benefits=["Puissance explosive", "Cardio", "Brûle-graisses"],
        contraindications=["problèmes genoux", "cheville fragile"],
    ),
    Exercise(
        id="hiit_004", name="Box Jumps", category=ExerciseCategory.hiit,
        muscle_groups=["quadriceps", "fessiers", "mollets"],
        equipment=["box pliométrique"], duration_minutes=15, calories_per_hour=600,
        difficulty=FitnessLevelEnum.advanced,
        description="Saut sur box pour développer la puissance explosive des jambes.",
        instructions=["Position fléchie", "Sauter avec les deux pieds", "Réception douce", "Descendre par le côté"],
        benefits=["Puissance", "Explosivité", "Athlétisme"],
        contraindications=["genoux", "chevilles"],
    ),
    # ── Flexibilité ──────────────────────────────────────────────────────────
    Exercise(
        id="flex_001", name="Étirements dynamiques", category=ExerciseCategory.flexibility,
        muscle_groups=["corps entier"],
        equipment=[], duration_minutes=15, calories_per_hour=150,
        difficulty=FitnessLevelEnum.beginner,
        description="Routine d'échauffement mobilisant toutes les articulations.",
        instructions=["Cercles de bras", "Rotations de hanches", "Leg swings", "Neck rolls"],
        benefits=["Mobilité", "Prévention blessures", "Échauffement"],
    ),
    Exercise(
        id="flex_002", name="Étirements statiques", category=ExerciseCategory.flexibility,
        muscle_groups=["corps entier"],
        equipment=[], duration_minutes=20, calories_per_hour=100,
        difficulty=FitnessLevelEnum.beginner,
        description="Récupération active par étirements maintenus.",
        instructions=["Maintenir 30 secondes", "Respirer profondément", "Jamais douloureux", "Progressif"],
        benefits=["Flexibilité", "Récupération", "Relaxation"],
    ),
    Exercise(
        id="flex_003", name="Foam Rolling", category=ExerciseCategory.flexibility,
        muscle_groups=["corps entier"],
        equipment=["foam roller"], duration_minutes=15, calories_per_hour=80,
        difficulty=FitnessLevelEnum.beginner,
        description="Auto-massage myofascial pour la récupération.",
        instructions=["Rouler lentement", "Pause sur points sensibles", "Respirer", "2-3 minutes par zone"],
        benefits=["Récupération", "Réduction douleurs", "Mobilité"],
    ),
    # ── Yoga ─────────────────────────────────────────────────────────────────
    Exercise(
        id="yoga_001", name="Yoga Flow (Vinyasa)", category=ExerciseCategory.yoga,
        muscle_groups=["corps entier", "core"],
        equipment=["tapis"], duration_minutes=45, calories_per_hour=300,
        difficulty=FitnessLevelEnum.beginner,
        description="Enchaînement fluide de postures synchronisées avec la respiration.",
        instructions=["Salutation au soleil", "Guerrier I et II", "Chien tête en bas", "Savasana final"],
        benefits=["Flexibilité", "Équilibre", "Stress"],
    ),
    Exercise(
        id="yoga_002", name="Yoga Restauratif", category=ExerciseCategory.yoga,
        muscle_groups=["corps entier"],
        equipment=["tapis", "coussins"], duration_minutes=30, calories_per_hour=100,
        difficulty=FitnessLevelEnum.beginner,
        description="Poses passives maintenues longtemps pour la récupération profonde.",
        instructions=["Positions soutenues", "Maintenir 5 minutes", "Respiration diaphragmatique", "Relâchement total"],
        benefits=["Récupération profonde", "Stress", "Sommeil"],
    ),
    # ── Sports ───────────────────────────────────────────────────────────────
    Exercise(
        id="sports_001", name="Basketball", category=ExerciseCategory.sports,
        muscle_groups=["jambes", "core", "bras", "cardio"],
        equipment=["ballon", "terrain"], duration_minutes=60, calories_per_hour=550,
        difficulty=FitnessLevelEnum.intermediate,
        description="Sport collectif alliant explosivité, endurance et technique.",
        instructions=["Échauffement obligatoire", "Dribbles", "Tirs", "Défense active"],
        benefits=["Cardio", "Coordination", "Esprit d'équipe"],
    ),
    Exercise(
        id="sports_002", name="Tennis", category=ExerciseCategory.sports,
        muscle_groups=["bras", "épaules", "jambes", "core"],
        equipment=["raquette", "court"], duration_minutes=60, calories_per_hour=500,
        difficulty=FitnessLevelEnum.intermediate,
        description="Sport de raquette pour la coordination et la réactivité.",
        instructions=["Grip adapté", "Position de base", "Déplacement latéral", "Coup droit et revers"],
        benefits=["Coordination", "Cardio", "Réactivité"],
    ),
]

EXERCISE_INDEX = {ex.id: ex for ex in EXERCISES}


# ─────────────────────────────────────────
# Filtering & selection logic
# ─────────────────────────────────────────

GOAL_CATEGORY_WEIGHTS: dict[GoalEnum, dict[ExerciseCategory, float]] = {
    GoalEnum.lose_weight:  {ExerciseCategory.hiit: 0.35, ExerciseCategory.cardio: 0.35, ExerciseCategory.strength: 0.20, ExerciseCategory.flexibility: 0.10},
    GoalEnum.gain_muscle:  {ExerciseCategory.strength: 0.60, ExerciseCategory.hiit: 0.20, ExerciseCategory.cardio: 0.10, ExerciseCategory.flexibility: 0.10},
    GoalEnum.endurance:    {ExerciseCategory.cardio: 0.55, ExerciseCategory.hiit: 0.20, ExerciseCategory.strength: 0.15, ExerciseCategory.flexibility: 0.10},
    GoalEnum.maintain:     {ExerciseCategory.cardio: 0.25, ExerciseCategory.strength: 0.30, ExerciseCategory.hiit: 0.20, ExerciseCategory.flexibility: 0.15, ExerciseCategory.yoga: 0.10},
}

DIFFICULTY_MAP = {
    FitnessLevelEnum.beginner: [FitnessLevelEnum.beginner],
    FitnessLevelEnum.intermediate: [FitnessLevelEnum.beginner, FitnessLevelEnum.intermediate],
    FitnessLevelEnum.advanced: [FitnessLevelEnum.beginner, FitnessLevelEnum.intermediate, FitnessLevelEnum.advanced],
}

WARMUP_BY_LEVEL = {
    FitnessLevelEnum.beginner: ["5 min marche rapide", "Rotations articulaires (cou, épaules, hanches, chevilles)", "Leg swings x10 chaque jambe"],
    FitnessLevelEnum.intermediate: ["5 min jogging léger", "Étirements dynamiques 3 min", "Squats bodyweight x15", "Pompes x10"],
    FitnessLevelEnum.advanced: ["8 min jogging progressif", "Étirements dynamiques complets", "Mobilité articulaire", "Série légère des exercices prévus"],
}

COOLDOWN_STEPS = [
    "5 min marche lente",
    "Étirement quadriceps 30 sec chaque jambe",
    "Étirement ischio-jambiers 30 sec chaque jambe",
    "Étirement pectoraux 30 sec",
    "Étirement dorsaux 30 sec",
    "Respiration profonde 2 min",
]

GOAL_RATIONALE = {
    GoalEnum.lose_weight: "Programme orienté déficit calorique avec alternance HIIT et cardio pour maximiser la combustion des graisses.",
    GoalEnum.gain_muscle: "Programme hypertrophie privilégiant les exercices polyarticulaires et la surcharge progressive.",
    GoalEnum.endurance: "Programme endurance aérobie avec volumes progressifs pour développer la capacité cardiovasculaire.",
    GoalEnum.maintain: "Programme équilibré combinant force, cardio et mobilité pour maintenir votre condition physique.",
}


def _filter_exercises(req: RecommendationRequest) -> list[Exercise]:
    allowed_difficulties = DIFFICULTY_MAP[req.fitness_level]
    result = []
    for ex in EXERCISES:
        if ex.difficulty not in allowed_difficulties:
            continue
        # Equipment filter: only keep exercises where all required equipment is available
        if ex.equipment and req.equipment:
            if not any(eq in req.equipment for eq in ex.equipment):
                continue
        elif ex.equipment and not req.equipment:
            # No equipment available — skip equipment-based exercises
            continue
        # Restriction filter
        skip = False
        for restriction in req.restrictions:
            restriction_lower = restriction.lower()
            if any(restriction_lower in c.lower() for c in ex.contraindications):
                skip = True
                break
        if skip:
            continue
        result.append(ex)
    return result


def _select_exercises(
    filtered: list[Exercise],
    req: RecommendationRequest,
    target_minutes: int,
) -> list[Exercise]:
    weights = GOAL_CATEGORY_WEIGHTS.get(req.goal, GOAL_CATEGORY_WEIGHTS[GoalEnum.maintain])
    if req.preferred_categories:
        for cat in req.preferred_categories:
            weights[cat] = weights.get(cat, 0) + 0.3

    # Sort by weighted category score
    def score(ex: Exercise) -> float:
        return weights.get(ex.category, 0.05)

    sorted_exercises = sorted(filtered, key=score, reverse=True)

    selected: list[Exercise] = []
    total_minutes = 0
    seen_categories: set[ExerciseCategory] = set()

    for ex in sorted_exercises:
        if total_minutes + ex.duration_minutes > target_minutes + 10:
            continue
        if ex.category in seen_categories and len(selected) > 0:
            # Allow duplicate category only if variety is exhausted
            if len(set(e.category for e in selected)) < min(3, len(seen_categories)):
                continue
        selected.append(ex)
        total_minutes += ex.duration_minutes
        seen_categories.add(ex.category)
        if total_minutes >= target_minutes - 10:
            break

    return selected


def build_workout(req: RecommendationRequest) -> WorkoutSession:
    # Reserve 10 min for warmup/cooldown
    exercise_budget = max(15, req.available_minutes - 10)
    filtered = _filter_exercises(req)

    if not filtered:
        # Fallback to beginner no-equipment
        filtered = [ex for ex in EXERCISES if ex.difficulty == FitnessLevelEnum.beginner and not ex.equipment]

    selected = _select_exercises(filtered, req, exercise_budget)
    total_duration = sum(e.duration_minutes for e in selected) + 10
    estimated_calories = sum(
        int(e.calories_per_hour * e.duration_minutes / 60) for e in selected
    )

    return WorkoutSession(
        session_id=str(uuid.uuid4()),
        name=_session_name(req.goal, req.fitness_level),
        goal=req.goal,
        fitness_level=req.fitness_level,
        total_duration_minutes=total_duration,
        estimated_calories=estimated_calories,
        exercises=selected,
        warmup=WARMUP_BY_LEVEL[req.fitness_level],
        cooldown=COOLDOWN_STEPS,
    )


def _session_name(goal: GoalEnum, level: FitnessLevelEnum) -> str:
    names = {
        (GoalEnum.lose_weight, FitnessLevelEnum.beginner): "Brûleur débutant",
        (GoalEnum.lose_weight, FitnessLevelEnum.intermediate): "Fat burner intermédiaire",
        (GoalEnum.lose_weight, FitnessLevelEnum.advanced): "HIIT intensif perte de poids",
        (GoalEnum.gain_muscle, FitnessLevelEnum.beginner): "Initiation musculation",
        (GoalEnum.gain_muscle, FitnessLevelEnum.intermediate): "Hypertrophie intermédiaire",
        (GoalEnum.gain_muscle, FitnessLevelEnum.advanced): "Force & volume avancé",
        (GoalEnum.endurance, FitnessLevelEnum.beginner): "Cardio fondamental",
        (GoalEnum.endurance, FitnessLevelEnum.intermediate): "Endurance progressive",
        (GoalEnum.endurance, FitnessLevelEnum.advanced): "Programme endurance avancé",
        (GoalEnum.maintain, FitnessLevelEnum.beginner): "Équilibre & bien-être",
        (GoalEnum.maintain, FitnessLevelEnum.intermediate): "Maintien intermédiaire",
        (GoalEnum.maintain, FitnessLevelEnum.advanced): "Performance & maintien",
    }
    return names.get((goal, level), "Séance personnalisée")


recommendation_engine = type("RecommendationEngine", (), {
    "build_workout": staticmethod(build_workout),
    "GOAL_RATIONALE": GOAL_RATIONALE,
    "EXERCISES": EXERCISES,
    "EXERCISE_INDEX": EXERCISE_INDEX,
})()
