from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://swzr_admin:swzr_dev_2026@localhost:5432/shouwenzeren"
    JWT_SECRET: str = "swzr-jwt-secret-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    BCRYPT_ROUNDS: int = 12

    AGENT_SERVICE_URL: str = "http://127.0.0.1:8100"  # AGUI 事件代理转发目标(integration)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
