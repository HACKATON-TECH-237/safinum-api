"""Masquage et contrôle des variables financières.

L'extension masque normalement les variables avant l'envoi. Le backend refait le
travail par sécurité : tout ce qui ressemble encore à un montant, une devise, une
date, un numéro ou un e-mail est remplacé par un marqueur avant d'être transmis au
moteur de traduction, puis réinjecté à l'identique.

Format des marqueurs : {TYPE_n}, par exemple {AMOUNT_0}, {CURRENCY_0}, {NUM_1}.
"""

import re
from collections import Counter
from dataclasses import dataclass, field

PLACEHOLDER_RE = re.compile(r"\{([A-Z]+)(?:_(\d+))?\}")

# L'ordre compte : les motifs les plus spécifiques d'abord.
_SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("DATE", re.compile(r"\b\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}\b")),
    (
        "CURRENCY",
        re.compile(r"(?<![\w{])(?:F\s?CFA|FCFA|XAF|XOF|EUR|USD|€|\$)(?![\w}])", re.IGNORECASE),
    ),
    # Chiffres avec séparateurs de milliers ou décimales : 250 000 / 1.250,50 / 6 99 00 11 22
    ("NUM", re.compile(r"\d(?:[\d.,   ]*\d)?")),
]


@dataclass
class MaskResult:
    text: str
    values: dict[str, str] = field(default_factory=dict)  # marqueur ajouté par le serveur -> valeur

    @property
    def server_masked(self) -> bool:
        return bool(self.values)


def find_placeholders(text: str) -> Counter[str]:
    return Counter(m.group(0) for m in PLACEHOLDER_RE.finditer(text))


def _split_on_placeholders(text: str) -> list[tuple[bool, str]]:
    """Découpe le texte en segments (est_marqueur, contenu) pour ne jamais re-masquer un marqueur."""
    parts: list[tuple[bool, str]] = []
    pos = 0
    for m in PLACEHOLDER_RE.finditer(text):
        if m.start() > pos:
            parts.append((False, text[pos : m.start()]))
        parts.append((True, m.group(0)))
        pos = m.end()
    if pos < len(text):
        parts.append((False, text[pos:]))
    return parts


def mask(text: str) -> MaskResult:
    """Remplace les valeurs sensibles restantes par des marqueurs numérotés."""
    # Les compteurs démarrent après les index déjà utilisés par l'extension.
    next_index: dict[str, int] = {}
    for m in PLACEHOLDER_RE.finditer(text):
        kind, idx = m.group(1), int(m.group(2) or 0)
        next_index[kind] = max(next_index.get(kind, 0), idx + 1)

    result = MaskResult(text=text)
    segments = _split_on_placeholders(text)

    for kind, pattern in _SENSITIVE_PATTERNS:
        new_segments: list[tuple[bool, str]] = []
        for is_placeholder, chunk in segments:
            if is_placeholder:
                new_segments.append((True, chunk))
                continue
            pos = 0
            for m in pattern.finditer(chunk):
                if m.start() > pos:
                    new_segments.append((False, chunk[pos : m.start()]))
                n = next_index.get(kind, 0)
                next_index[kind] = n + 1
                token = f"{{{kind}_{n}}}"
                result.values[token] = m.group(0)
                new_segments.append((True, token))
                pos = m.end()
            if pos < len(chunk):
                new_segments.append((False, chunk[pos:]))
        segments = new_segments

    result.text = "".join(chunk for _, chunk in segments)
    return result


def placeholders_preserved(source: str, translated: str) -> bool:
    """Vrai si chaque marqueur de la source apparaît exactement autant de fois dans la traduction."""
    return find_placeholders(source) == find_placeholders(translated)


def unmask(text: str, values: dict[str, str]) -> str:
    """Réinjecte les valeurs masquées par le serveur. Les marqueurs de l'extension restent tels quels."""
    return PLACEHOLDER_RE.sub(lambda m: values.get(m.group(0), m.group(0)), text)
