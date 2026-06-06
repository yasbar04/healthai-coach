import pytest
from app.schemas.recommendation import RecommendationRequest, GoalEnum, FitnessLevelEnum, ExerciseCategory
from app.services.recommendation_engine import build_workout, _filter_exercises, EXERCISES


def make_req(**kwargs) -> RecommendationRequest:
    defaults = {
        "user_id": 1,
        "goal": GoalEnum.maintain,
        "fitness_level": FitnessLevelEnum.beginner,
        "available_minutes": 45,
        "equipment": [],
        "restrictions": [],
        "preferred_categories": [],
    }
    defaults.update(kwargs)
    return RecommendationRequest(**defaults)


def test_build_workout_returns_exercises():
    req = make_req(goal=GoalEnum.lose_weight, fitness_level=FitnessLevelEnum.beginner)
    workout = build_workout(req)
    assert len(workout.exercises) > 0
    assert workout.total_duration_minutes > 0
    assert workout.estimated_calories > 0


def test_build_workout_respects_difficulty():
    req = make_req(fitness_level=FitnessLevelEnum.beginner)
    workout = build_workout(req)
    for ex in workout.exercises:
        assert ex.difficulty == FitnessLevelEnum.beginner


def test_build_workout_no_equipment():
    req = make_req(equipment=[])
    workout = build_workout(req)
    for ex in workout.exercises:
        assert not ex.equipment, f"{ex.name} requires equipment but none available"


def test_build_workout_with_equipment():
    req = make_req(equipment=["barre", "poids", "banc"], fitness_level=FitnessLevelEnum.intermediate)
    workout = build_workout(req)
    assert len(workout.exercises) > 0


def test_filter_excludes_restrictions():
    req = make_req(restrictions=["genoux"], fitness_level=FitnessLevelEnum.intermediate)
    filtered = _filter_exercises(req)
    for ex in filtered:
        assert not any("genoux" in c.lower() for c in ex.contraindications)


def test_gain_muscle_favors_strength():
    req = make_req(goal=GoalEnum.gain_muscle, fitness_level=FitnessLevelEnum.intermediate, equipment=["barre", "poids", "banc"])
    workout = build_workout(req)
    categories = [ex.category for ex in workout.exercises]
    assert ExerciseCategory.strength in categories


def test_endurance_favors_cardio():
    req = make_req(goal=GoalEnum.endurance, fitness_level=FitnessLevelEnum.beginner)
    workout = build_workout(req)
    categories = [ex.category for ex in workout.exercises]
    assert ExerciseCategory.cardio in categories


def test_workout_has_warmup_and_cooldown():
    req = make_req()
    workout = build_workout(req)
    assert len(workout.warmup) > 0
    assert len(workout.cooldown) > 0


def test_exercise_database_complete():
    for ex in EXERCISES:
        assert ex.id
        assert ex.name
        assert len(ex.instructions) > 0
        assert len(ex.benefits) > 0
        assert ex.calories_per_hour > 0
