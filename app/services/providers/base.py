from typing import Protocol


class ProviderError(Exception):
    """Erreur du moteur de traduction (réseau, quota, langue non prise en charge...)."""


class TranslationProvider(Protocol):
    """Moteur de traduction pour les textes absents du glossaire.

    Reçoit uniquement des textes masqués ; doit renvoyer une traduction par texte,
    dans le même ordre, en laissant les marqueurs {TYPE_n} intacts.
    """

    name: str

    async def translate(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]: ...
