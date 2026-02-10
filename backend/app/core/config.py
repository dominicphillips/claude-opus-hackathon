from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://storyspark:storyspark_dev@localhost:5432/storyspark"
    anthropic_api_key: str = ""
    replicate_api_token: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    gemini_api_key: str = ""
    clip_storage_path: str = "/app/clips"

    model_config = {"env_file": ".env"}


settings = Settings()
