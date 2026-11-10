"""Pipeline de traduction : glossaire -> masquage -> moteur -> contrôle -> repli.

Principe : en cas de doute, on renvoie le texte original. L'API ne bloque jamais
l'affichage du site et ne laisse jamais passer une variable financière modifiée.
"""

import asyncio
import logging
import re
import time
from collections import OrderedDict
from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.translation import (
    TranslatedItem,
    TranslateItem,
    TranslateRequest,
    TranslateResponse,
    TranslationSource,
    TranslationStatus,
)
from app.services.glossary import GlossaryStore
from app.services.masking import PLACEHOLDER_RE, MaskResult, mask, placeholders_preserved, unmask
from app.services.providers import ProviderError, TranslationProvider

logger = logging.getLogger(__name__)

_HAS_LETTER_RE = re.compile(r"[^\W\d_]")


class _LRUCache:
    def __init__(self, max_entries: int) -> None:
        self.max_entries = max_entries
        self._data: OrderedDict[tuple[str, str, str], str] = OrderedDict()

    def get(self, key: tuple[str, str, str]) -> str | None:
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def set(self, key: tuple[str, str, str], value: str) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        while len(self._data) > self.max_entries:
            self._data.popitem(last=False)


@dataclass
class _Pending:
    item: TranslateItem
    masked: MaskResult


def _original(item: TranslateItem) -> TranslatedItem:
    return TranslatedItem(
        id=item.id,
        translation=item.text,
        source=TranslationSource.fallback,
        status=TranslationStatus.original_kept,
    )


class TranslationPipeline:
    def __init__(
        self,
        settings: Settings,
        glossaries: GlossaryStore,
        provider: TranslationProvider | None,
    ) -> None:
        self.settings = settings
        self.glossaries = glossaries
        self.provider = provider
        self.cache = _LRUCache(settings.cache_max_entries)

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        started = time.perf_counter()
        glossary = self.glossaries.get(request.target_lang)
        results: dict[str, TranslatedItem] = {}
        pending: list[_Pending] = []
        server_masked = 0

        for item in request.items:
            masked = mask(item.text)
            server_masked += len(masked.values)

            # 1. Rien à traduire (uniquement des variables, chiffres ou ponctuation).
            if not _HAS_LETTER_RE.search(PLACEHOLDER_RE.sub("", masked.text)):
                results[item.id] = _original(item)
                continue

            # 2. Glossaire validé.
            if glossary and (entry := glossary.lookup(masked.text, item.context)):
                if placeholders_preserved(masked.text, entry.translation):
                    results[item.id] = TranslatedItem(
                        id=item.id,
                        translation=unmask(entry.translation, masked.values),
                        source=TranslationSource.glossary,
                        status=TranslationStatus.ok,
                        confidence=1.0,
                    )
                    continue
                logger.warning("Entrée de glossaire %s : marqueurs incohérents, ignorée", entry.id)

            pending.append(_Pending(item, masked))

        # 3. Moteur de traduction pour les textes inédits.
        if pending:
            translations = await self._machine_translate(
                [p.masked.text for p in pending], request.source_lang, request.target_lang
            )
            for p, translated in zip(pending, translations, strict=True):
                results[p.item.id] = self._check(p, translated)

        items = [results[item.id] for item in request.items]
        logger.info(
            "translate %s->%s items=%d glossary=%d machine=%d fallback=%d server_masked=%d %.0fms",
            request.source_lang,
            request.target_lang,
            len(items),
            sum(i.source == TranslationSource.glossary for i in items),
            sum(i.source == TranslationSource.machine for i in items),
            sum(i.source == TranslationSource.fallback for i in items),
            server_masked,
            (time.perf_counter() - started) * 1000,
        )
        return TranslateResponse(
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            glossary_version=glossary.version if glossary else None,
            items=items,
        )

    async def _machine_translate(
        self, texts: list[str], source_lang: str, target_lang: str
    ) -> list[str | None]:
        """Traduit les textes masqués ; None pour chaque texte non traduit (échec, timeout...)."""
        out: list[str | None] = [None] * len(texts)
        if self.provider is None:
            return out

        to_send: list[int] = []
        for i, text in enumerate(texts):
            cached = self.cache.get((source_lang, target_lang, text))
            if cached is not None:
                out[i] = cached
            else:
                to_send.append(i)
        if not to_send:
            return out

        try:
            translated = await asyncio.wait_for(
                self.provider.translate([texts[i] for i in to_send], source_lang, target_lang),
                timeout=self.settings.provider_timeout_seconds,
            )
            if len(translated) != len(to_send):
                raise ProviderError("nombre de traductions différent du nombre de textes")
        except TimeoutError:
            logger.warning("Moteur %s : délai dépassé", self.provider.name)
            return out
        except Exception as exc:  # le site ne doit jamais être bloqué par le moteur
            logger.warning("Moteur %s indisponible : %s", self.provider.name, type(exc).__name__)
            return out

        for i, t in zip(to_send, translated, strict=True):
            out[i] = t
            self.cache.set((source_lang, target_lang, texts[i]), t)
        return out

    def _check(self, p: _Pending, translated: str | None) -> TranslatedItem:
        if not translated or not translated.strip():
            return _original(p.item)
        # Une variable perdue, dupliquée ou inventée : on garde l'original.
        if not placeholders_preserved(p.masked.text, translated):
            logger.warning("Item %s : marqueurs altérés par le moteur, original conservé", p.item.id)
            return _original(p.item)

        candidate = unmask(translated, p.masked.values)
        if p.item.risk_level in self.settings.review_risk_levels:
            return TranslatedItem(
                id=p.item.id,
                translation=p.item.text,
                source=TranslationSource.machine,
                status=TranslationStatus.needs_review,
                suggestion=candidate,
            )
        return TranslatedItem(
            id=p.item.id,
            translation=candidate,
            source=TranslationSource.machine,
            status=TranslationStatus.ok,
        )
