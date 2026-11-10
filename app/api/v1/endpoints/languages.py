from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_glossaries
from app.schemas.translation import GlossaryEntryOut, GlossaryOut, Language
from app.services.glossary import GlossaryStore

router = APIRouter()


@router.get("/languages", response_model=list[Language])
async def list_languages(glossaries: Annotated[GlossaryStore, Depends(get_glossaries)]) -> list[Language]:
    """Langues cibles disponibles (une par glossaire chargé)."""
    return [
        Language(
            code=g.code,
            name=g.name,
            glossary_version=g.version,
            validated_entries=len(g.entries),
            validated=g.language_validated,
        )
        for g in glossaries.all()
    ]


@router.get("/glossary/{lang}", response_model=GlossaryOut)
async def get_glossary(
    lang: str, glossaries: Annotated[GlossaryStore, Depends(get_glossaries)]
) -> GlossaryOut:
    """Entrées validées du glossaire, pour que l'extension les mette en cache et traduise sans appel réseau."""
    glossary = glossaries.get(lang)
    if glossary is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Aucun glossaire pour la langue {lang!r}")
    return GlossaryOut(
        language=glossary.code,
        version=glossary.version,
        entries=[
            GlossaryEntryOut(
                id=e.id, source=e.source, translation=e.translation, context=e.context, risk=e.risk
            )
            for e in glossary.entries
        ],
    )
