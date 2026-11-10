from fastapi import Request

from app.services.glossary import GlossaryStore
from app.services.pipeline import TranslationPipeline


def get_pipeline(request: Request) -> TranslationPipeline:
    return request.app.state.pipeline


def get_glossaries(request: Request) -> GlossaryStore:
    return request.app.state.glossaries
