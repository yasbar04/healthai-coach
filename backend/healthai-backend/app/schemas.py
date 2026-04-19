from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    plan: str = "freemium"  # freemium | premium | premium_plus | b2b

class RegisterResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    plan: str

class UserMe(BaseModel):
    id: int
    email: EmailStr
    plan: str
    role: str = "user"

class SubscribeRequest(BaseModel):
    plan: str

class SubscribeResponse(BaseModel):
    status: str
    plan: str

class ActivityOut(BaseModel):
    id: int
    activity_date: date
    steps: Optional[int] = None
    active_minutes: Optional[int] = None
    calories_out: Optional[int] = None
    distance_km: Optional[float] = None
    workout_type: Optional[str] = None
    sleep_hours: Optional[float] = None
    water_ml: Optional[int] = None
    weight_kg: Optional[float] = None

class ActivityCreate(BaseModel):
    activity_date: date
    steps: Optional[int] = None
    active_minutes: Optional[int] = None
    calories_out: Optional[int] = None
    distance_km: Optional[float] = None
    workout_type: Optional[str] = None
    sleep_hours: Optional[float] = None
    water_ml: Optional[int] = None
    weight_kg: Optional[float] = None

class FoodOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    calories_kcal: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugars_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    meal_type: Optional[str] = None
    water_intake_ml: Optional[int] = None

class NutritionLogOut(BaseModel):
    id: int
    log_date: date
    grams: float
    food_id: int
    food_name: Optional[str] = None
    total_calories_kcal: Optional[float] = None

class SummaryOut(BaseModel):
    total_calories_in: int
    total_calories_out: int
    total_steps: int
    active_days: int

class TrendPoint(BaseModel):
    date: str
    value: float

class TrendOut(BaseModel):
    points: List[TrendPoint]

class EtlRunOut(BaseModel):
    id: int
    source_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    rows_in: int
    rows_out: int
    errors_count: int

class EtlErrorOut(BaseModel):
    id: int
    severity: str
    row_reference: Optional[str] = None
    message: str
    created_at: datetime

class TenantOut(BaseModel):
    mode: str = "b2c"
    brand_name: str = "HealthAI Coach"
