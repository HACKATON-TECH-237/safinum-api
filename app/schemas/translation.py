from enum import StrEnum

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TranslationSource(StrEnum):
    glossary = "glossary"  # traduction validée par les locuteurs
    machine = "machine"  # moteur de traduction (texte inédit)
    fallback = "fallback"  # aucune traduction fiable : texte original renvoyé


class TranslationStatus(StrEnum):
    ok = "ok"  # afficher `translation`
    needs_review = "needs_review"  # afficher l'original + signaler ; `suggestion` est indicative
    original_kept = "original_kept"  # afficher l'original (échec, timeout, variable altérée)


class TranslateItem(BaseModel):
    id: str = Field(min_length=1, max_length=128, description="Identifiant du nœud côté extension")
    text: str = Field(
        min_length=1,
        description="Texte assaini : les variables sont déjà masquées ({AMOUNT_0}, {CURRENCY_0}...)",
    )
    context: str | None = Field(default=None, max_length=128, description="Ex. transfer.fees")
    risk_level: RiskLevel = RiskLevel.medium


class TranslateRequest(BaseModel):
    source_lang: str = Field(default="fr", min_length=2, max_length=16)
    target_lang: str = Field(min_length=2, max_length=16)
    items: list[TranslateItem] = Field(min_length=1)


class TranslatedItem(BaseModel):
    id: str
    translation: str = Field(description="Texte à afficher dans la page")
    source: TranslationSource
    status: TranslationStatus
    confidence: float | None = None
    suggestion: str | None = Field(
        default=None, description="Traduction automatique proposée quand status = needs_review"
    )


class TranslateResponse(BaseModel):
    source_lang: str
    target_lang: str
    glossary_version: str | None
    items: list[TranslatedItem]


class Language(BaseModel):
    code: str
    name: str
    glossary_version: str
    validated_entries: int
    validated: bool


class GlossaryEntryOut(BaseModel):
    id: str
    source: str
    translation: str
    context: str | None = None
    risk: RiskLevel


class GlossaryOut(BaseModel):
    language: str
    version: str
    entries: list[GlossaryEntryOut]
