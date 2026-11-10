from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuration lue depuis les variables d'environnement ou le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"

    # CORS : origines exactes + motif pour les extensions Chrome.
    # En production, remplacer le motif par l'ID exact de l'extension :
    # ALLOWED_ORIGIN_REGEX=^chrome-extension://<id-de-l-extension>$
    allowed_origins: list[str] = ["http://localhost:3000"]
    allowed_origin_regex: str = r"^chrome-extension://[a-p]{32}$"

    # Moteur de traduction pour les textes absents du glossaire : "mock" ou "none".
    translation_provider: str = "mock"
    translation_api_key: str = ""
    provider_timeout_seconds: float = 5.0

    # Glossaires validés (un fichier JSON par langue cible).
    glossary_dir: Path = BASE_DIR / "data" / "glossary"

    # Limites de requête (protection contre les abus et les erreurs côté extension).
    max_items_per_request: int = 100
    max_text_length: int = 1000

    # Niveaux de risque pour lesquels une traduction automatique n'est jamais affichée
    # seule : l'extension garde l'original et signale qu'une vérification est nécessaire.
    review_risk_levels: list[str] = ["high", "critical"]

    cache_max_entries: int = 5000


@lru_cache
def get_settings() -> Settings:
    return Settings()
