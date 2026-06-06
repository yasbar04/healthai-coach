from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _db = _client[settings.MONGODB_DB]
    await _db["recommendations"].create_index([("user_id", 1), ("created_at", -1)])
    await _db["recommendations"].create_index([("user_id", 1), ("goal", 1)])
    await _db["activity_logs"].create_index([("user_id", 1), ("logged_at", -1)])


async def disconnect_db() -> None:
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not connected")
    return _db
