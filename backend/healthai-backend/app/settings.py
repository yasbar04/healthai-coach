import os
from pydantic import BaseModel


class Settings(BaseModel):
    jwt_secret: str = os.getenv("JWT_SECRET", "dev_secret_change_me")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")


    def cors_origins_list(self) -> list[str]:
        # comma-separated
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()
