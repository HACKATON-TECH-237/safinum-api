"""Chargement des glossaires validés (un fichier JSON par langue cible).

Seules les entrées au statut "valide" sont utilisées. Les fichiers dont le nom
commence par "_" (modèles, brouillons) sont ignorés.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.schemas.translation import RiskLevel

logger = logging.getLogger(__name__)

VALIDATED_STATUS = "valide"
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Clé de recherche : espaces normalisés, casse ignorée."""
    return _WS_RE.sub(" ", text.replace(" ", " ").replace(" ", " ")).strip().casefold()


@dataclass(frozen=True)
class GlossaryEntry:
    id: str
    source: str
    translation: str
    context: str | None
    risk: RiskLevel


@dataclass
class Glossary:
    code: str
    name: str
    version: str
    language_validated: bool
    entries: list[GlossaryEntry]

    def __post_init__(self) -> None:
        self._by_context: dict[tuple[str, str | None], GlossaryEntry] = {}
        self._by_text: dict[str, GlossaryEntry] = {}
        for e in self.entries:
            key = normalize(e.source)
            self._by_context[(key, e.context)] = e
            self._by_text.setdefault(key, e)

    def lookup(self, text: str, context: str | None = None) -> GlossaryEntry | None:
        key = normalize(text)
        # Une traduction propre au contexte l'emporte sur la traduction générique.
        if context is not None and (key, context) in self._by_context:
            return self._by_context[(key, context)]
        return self._by_text.get(key)


def load_glossary(path: Path) -> Glossary:
    data = json.loads(path.read_text(encoding="utf-8"))
    lang = data["language"]
    entries = [
        GlossaryEntry(
            id=e["id"],
            source=e["source"],
            translation=e["translation"],
            context=e.get("context"),
            risk=RiskLevel(e.get("risk", "medium")),
        )
        for e in data.get("entries", [])
        if e.get("status") == VALIDATED_STATUS and e.get("translation")
    ]
    return Glossary(
        code=lang["code"],
        name=lang["name"],
        version=str(data.get("version", "0")),
        language_validated=bool(lang.get("validated", False)),
        entries=entries,
    )


class GlossaryStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._glossaries: dict[str, Glossary] = {}

    def load(self) -> None:
        self._glossaries.clear()
        if not self.directory.is_dir():
            logger.warning("Dossier de glossaires introuvable : %s", self.directory)
            return
        for path in sorted(self.directory.glob("*.json")):
            if path.name.startswith("_"):
                continue
            glossary = load_glossary(path)
            self._glossaries[glossary.code] = glossary
            logger.info(
                "Glossaire %s v%s chargé (%d entrées validées)",
                glossary.code,
                glossary.version,
                len(glossary.entries),
            )

    def get(self, code: str) -> Glossary | None:
        return self._glossaries.get(code)

    def all(self) -> list[Glossary]:
        return list(self._glossaries.values())
