import uuid
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_db
from app.schemas.recommendation import (
    ActivityLogCreate,
    ActivityLogPublic,
    ActivityStatsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_engine import build_workout, GOAL_RATIONALE
from app.services.ai_service import ai_coaching_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
async def get_recommendation(
    req: RecommendationRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    workout = build_workout(req)

    # Fetch user activity stats for AI context
    since = (date.today() - timedelta(days=30)).isoformat()
    pipeline = [
        {"$match": {"user_id": req.user_id, "logged_at": {"$gte": since}}},
        {"$group": {
            "_id": None,
            "total_sessions": {"$sum": 1},
            "total_duration_minutes": {"$sum": "$duration_minutes"},
            "total_calories": {"$sum": "$calories_burned"},
        }},
    ]
    cursor = db["activity_logs"].aggregate(pipeline)
    stats_doc = await cursor.to_list(1)
    user_stats = stats_doc[0] if stats_doc else {}

    ai_result = await ai_coaching_service.get_ai_coaching_tips(
        workout, user_stats, req.current_nutrition_score
    )

    rec_doc = {
        "recommendation_id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "workout": workout.model_dump(),
        "rationale": GOAL_RATIONALE.get(req.goal, ""),
        "ai_tips": ai_result.get("tips", []),
        "next_session_suggestion": ai_result.get("next_session", ""),
        "generated_at": datetime.utcnow(),
    }
    await db["recommendations"].insert_one(rec_doc)

    return RecommendationResponse(
        recommendation_id=rec_doc["recommendation_id"],
        user_id=req.user_id,
        workout=workout,
        rationale=rec_doc["rationale"],
        ai_tips=rec_doc["ai_tips"],
        next_session_suggestion=rec_doc["next_session_suggestion"],
        generated_at=rec_doc["generated_at"],
    )


@router.get("/history/{user_id}", response_model=list[RecommendationResponse])
async def get_recommendation_history(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db["recommendations"].find(
        {"user_id": user_id},
        sort=[("generated_at", -1)],
        limit=limit,
    )
    docs = await cursor.to_list(limit)
    result = []
    for doc in docs:
        from app.schemas.recommendation import WorkoutSession
        result.append(RecommendationResponse(
            recommendation_id=doc["recommendation_id"],
            user_id=doc["user_id"],
            workout=WorkoutSession(**doc["workout"]),
            rationale=doc.get("rationale", ""),
            ai_tips=doc.get("ai_tips", []),
            next_session_suggestion=doc.get("next_session_suggestion", ""),
            generated_at=doc["generated_at"],
        ))
    return result


@router.post("/activity-log", response_model=ActivityLogPublic, status_code=status.HTTP_201_CREATED)
async def log_activity(
    user_id: int,
    payload: ActivityLogCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from app.services.recommendation_engine import EXERCISE_INDEX
    exercise = EXERCISE_INDEX.get(payload.exercise_id)
    calories_burned = payload.calories_burned
    if calories_burned is None and exercise:
        calories_burned = int(exercise.calories_per_hour * payload.duration_minutes / 60)
    calories_burned = calories_burned or 0

    log_doc = {
        "user_id": user_id,
        "exercise_id": payload.exercise_id,
        "exercise_name": payload.exercise_name,
        "duration_minutes": payload.duration_minutes,
        "calories_burned": calories_burned,
        "notes": payload.notes,
        "perceived_effort": payload.perceived_effort,
        "logged_at": datetime.utcnow().isoformat(),
    }
    result = await db["activity_logs"].insert_one(log_doc)

    return ActivityLogPublic(
        id=str(result.inserted_id),
        user_id=user_id,
        exercise_id=payload.exercise_id,
        exercise_name=payload.exercise_name,
        duration_minutes=payload.duration_minutes,
        calories_burned=calories_burned,
        notes=payload.notes,
        perceived_effort=payload.perceived_effort,
        logged_at=datetime.utcnow(),
    )


@router.get("/activity-stats/{user_id}", response_model=ActivityStatsResponse)
async def get_activity_stats(
    user_id: int,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    since = (date.today() - timedelta(days=days)).isoformat()

    pipeline = [
        {"$match": {"user_id": user_id, "logged_at": {"$gte": since}}},
        {"$group": {
            "_id": None,
            "total_sessions": {"$sum": 1},
            "total_duration": {"$sum": "$duration_minutes"},
            "total_calories": {"$sum": "$calories_burned"},
            "avg_effort": {"$avg": "$perceived_effort"},
        }},
    ]
    cursor = db["activity_logs"].aggregate(pipeline)
    agg = (await cursor.to_list(1) or [{}])[0]

    # Daily trend
    trend_pipeline = [
        {"$match": {"user_id": user_id, "logged_at": {"$gte": since}}},
        {"$group": {
            "_id": {"$substr": ["$logged_at", 0, 10]},
            "sessions": {"$sum": 1},
            "duration": {"$sum": "$duration_minutes"},
            "calories": {"$sum": "$calories_burned"},
        }},
        {"$sort": {"_id": 1}},
    ]
    trend_cursor = db["activity_logs"].aggregate(trend_pipeline)
    activity_trend = [
        {"day": doc["_id"], "sessions": doc["sessions"], "duration": doc["duration"], "calories": doc["calories"]}
        for doc in await trend_cursor.to_list(days)
    ]

    # Most common exercises
    ex_pipeline = [
        {"$match": {"user_id": user_id, "logged_at": {"$gte": since}}},
        {"$group": {"_id": "$exercise_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    ex_cursor = db["activity_logs"].aggregate(ex_pipeline)
    most_common = [doc["_id"] for doc in await ex_cursor.to_list(5)]

    total_sessions = agg.get("total_sessions", 0)
    total_duration = agg.get("total_duration", 0)

    return ActivityStatsResponse(
        period_days=days,
        total_sessions=total_sessions,
        total_duration_minutes=total_duration,
        total_calories_burned=agg.get("total_calories", 0),
        avg_session_duration=round(total_duration / total_sessions, 1) if total_sessions else 0.0,
        avg_perceived_effort=round(agg.get("avg_effort", 0), 1),
        most_common_exercises=most_common,
        activity_trend=activity_trend,
    )
