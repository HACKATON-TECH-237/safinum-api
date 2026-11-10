from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_pipeline
from app.core.config import Settings, get_settings
from app.schemas.translation import TranslateRequest, TranslateResponse
from app.services.pipeline import TranslationPipeline

router = APIRouter()


@router.post("/translate", response_model=TranslateResponse, response_model_exclude_none=True)
async def translate(
    body: TranslateRequest,
    pipeline: Annotated[TranslationPipeline, Depends(get_pipeline)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TranslateResponse:
    """Traduit un lot de textes assainis (variables masquées) vers la langue cible."""
    if len(body.items) > settings.max_items_per_request:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Au plus {settings.max_items_per_request} textes par requête",
        )
    too_long = [i.id for i in body.items if len(i.text) > settings.max_text_length]
    if too_long:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Textes trop longs (max {settings.max_text_length} caractères) : {too_long[:5]}",
        )
    if len({i.id for i in body.items}) != len(body.items):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Identifiants `id` en double")

    return await pipeline.translate(body)
