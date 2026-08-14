from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://swzr_admin:swzr_dev_2026@localhost:5432/shouwenzeren"
    JWT_SECRET: str = "swzr-jwt-secret-2026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"
    BCRYPT_ROUNDS: int = 12
    AGENT_BASE_URL: str = ""  # Agent 服务根地址（如 http://127.0.0.1:8100）；留空=未接入走降级。
    # 前端已直连 agent（VITE_AGUI_BASE_URL 指向 agent），后端此配置仅用于将来恢复后端转发时兜底。

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
