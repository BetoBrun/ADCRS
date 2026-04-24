from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
settings = Settings()
