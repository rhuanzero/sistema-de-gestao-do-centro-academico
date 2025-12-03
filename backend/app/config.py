from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator
from typing import Optional

class Settings(BaseSettings):
    # --- Configurações do Banco de Dados MySQL ---
    DB_USER: str = "root"
    DB_PASSWORD: Optional[str] = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "sgca"
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"mysql+aiomysql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}"
            f"@{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
        )

    # --- Configurações do MongoDB ---
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "sgca"

    # --- Configurações de Segurança ---
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()