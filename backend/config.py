from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    elevenlabs_api_key: str
    tavily_api_key: str
    mongodb_uri: str
    database_name: str = "mock_interview_app"
    clerk_publishable_key: str
    clerk_secret_key: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()