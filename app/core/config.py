from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.
    Lee automáticamente las variables desde el archivo .env o variables del sistema.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Credenciales de Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Credenciales de Gemini y modelos
    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    LLM_MODEL: str = "gemini-3.5-flash"

    # Entorno y CORS
    APP_ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        """Convierte la cadena separada por comas en una lista de orígenes permitidos para CORS."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Instancia singleton accesible desde toda la app
settings = Settings()
