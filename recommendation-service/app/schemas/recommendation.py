from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class GoalEnum(str, Enum):
    lose_weight = "lose_weight"
    gain_muscle = "gain_muscle"
    maintain = "maintain"
    endurance = "endurance"


class FitnessLevelEnum(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class ExerciseCategory(str, Enum):
    cardio = "cardio"
    strength = "strength"
    flexibility = "flexibility"
    hiit = "hiit"
    yoga = "yoga"
    sports = "sports"


class Exercise(BaseModel):
    id: str
    name: str
    category: ExerciseCategory
    muscle_groups: list[str]
    equipment: list[str]
    duration_minutes: int
    calories_per_hour: int
    difficulty: FitnessLevelEnum
    description: str
    instructions: list[str]
    benefits: list[str]
    contraindications: list[str] = []


class WorkoutSession(BaseModel):
    session_id: str
    name: str
    goal: GoalEnum
    fitness_level: FitnessLevelEnum
    total_duration_minutes: int
    estimated_calories: int
    exercises: list[Exercise]
    warmup: list[str]
    cooldown: list[str]
    notes: str = ""


class RecommendationRequest(BaseModel):
    user_id: int
    goal: GoalEnum = GoalEnum.maintain
    fitness_level: FitnessLevelEnum = FitnessLevelEnum.beginner
    available_minutes: int = Field(default=45, ge=15, le=180)
    equipment: list[str] = []
    restrictions: list[str] = []
    preferred_categories: list[ExerciseCategory] = []
    current_nutrition_score: Optional[float] = None


class ActivityLogCreate(BaseModel):
    exercise_id: str
    exercise_name: str
    duration_minutes: int = Field(ge=1)
    calories_burned: Optional[int] = None
    notes: Optional[str] = None
    perceived_effort: int = Field(default=5, ge=1, le=10)


class ActivityLogPublic(BaseModel):
    id: str
    user_id: int
    exercise_id: str
    exercise_name: str
    duration_minutes: int
    calories_burned: int
    notes: Optional[str]
    perceived_effort: int
    logged_at: datetime


class ActivityStatsResponse(BaseModel):
    period_days: int
    total_sessions: int
    total_duration_minutes: int
    total_calories_burned: int
    avg_session_duration: float
    avg_perceived_effort: float
    most_common_exercises: list[str]
    activity_trend: list[dict]


class RecommendationResponse(BaseModel):
    recommendation_id: str
    user_id: int
    workout: WorkoutSession
    rationale: str
    ai_tips: list[str]
    next_session_suggestion: str
    generated_at: datetime
