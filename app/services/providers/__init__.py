from app.core.config import Settings
from app.services.providers.base import ProviderError, TranslationProvider
from app.services.providers.mock import MockProvider

__all__ = ["ProviderError", "TranslationProvider", "build_provider"]


def build_provider(settings: Settings) -> TranslationProvider | None:
    """Retourne le moteur configuré, ou None si la traduction automatique est désactivée."""
    match settings.translation_provider:
        case "mock":
            return MockProvider()
        case "none" | "":
            return None
        case other:
            raise ValueError(f"Moteur de traduction inconnu : {other!r}")
