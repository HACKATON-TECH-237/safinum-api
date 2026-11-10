import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.services.glossary import GlossaryStore
from app.services.pipeline import TranslationPipeline
from app.services.providers import build_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        glossaries = GlossaryStore(settings.glossary_dir)
        glossaries.load()
        app.state.glossaries = glossaries
        app.state.pipeline = TranslationPipeline(settings, glossaries, build_provider(settings))
        yield

    app = FastAPI(
        title="Safinum API",
        description="Moteur linguistique de l'extension SAFINUM : glossaire validé + traduction des textes inédits.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.dependency_overrides[get_settings] = lambda: settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=settings.allowed_origin_regex or None,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", tags=["service"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "provider": app.state.pipeline.provider.name if app.state.pipeline.provider else "none",
        }

    app.include_router(api_router)
    return app


app = create_app()
