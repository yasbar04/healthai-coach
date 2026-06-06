from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "healthai_recommendations"
    ANTHROPIC_API_KEY: str = ""
    MAIN_API_URL: str = "http://localhost:8010"
    SECRET_KEY: str = "change_me"
    ENVIRONMENT: str = "development"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


settings = Settings()
