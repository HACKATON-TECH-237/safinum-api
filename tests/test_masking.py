import re

import pytest

from app.services.masking import find_placeholders, mask, placeholders_preserved, unmask

# Valeurs des écrans SAFINUM Pay (tests bloquants de la note de cadrage).
SAFINUM_TEXTS = [
    "Solde : 250 000 FCFA",
    "Vous envoyez 25 000 FCFA, frais 0 FCFA, total 25 000 FCFA",
    "Solde après opération : 225 000 FCFA",
    "Compte n° 6 99 00 11 22 — référence TRX-2026-0042",
    "Date du transfert : 12/11/2026",
    "Contact : support@safinum.test",
    "Montant : 1.250,50 XAF",
]


def digits(text: str) -> list[str]:
    return re.findall(r"\d", text)


@pytest.mark.parametrize("text", SAFINUM_TEXTS)
def test_aucun_chiffre_ne_sort_du_masquage(text):
    masked = mask(text)
    # Seuls les index des marqueurs peuvent contenir des chiffres.
    assert digits(re.sub(r"\{[A-Z]+_\d+\}", "", masked.text)) == []
    assert "FCFA" not in masked.text and "XAF" not in masked.text
    assert "@" not in masked.text


@pytest.mark.parametrize("text", SAFINUM_TEXTS)
def test_aller_retour_identique(text):
    masked = mask(text)
    assert unmask(masked.text, masked.values) == text


def test_valeurs_exactes():
    masked = mask("Vous envoyez 25 000 FCFA, total 225 000 FCFA")
    assert masked.text == "Vous envoyez {NUM_0} {CURRENCY_0}, total {NUM_1} {CURRENCY_1}"
    assert masked.values == {
        "{NUM_0}": "25 000",
        "{NUM_1}": "225 000",
        "{CURRENCY_0}": "FCFA",
        "{CURRENCY_1}": "FCFA",
    }


def test_marqueurs_de_l_extension_conserves_et_index_non_reutilises():
    masked = mask("Total {AMOUNT_0} {CURRENCY_0} et 500 FCFA")
    assert masked.text == "Total {AMOUNT_0} {CURRENCY_0} et {NUM_0} {CURRENCY_1}"
    assert "{CURRENCY_0}" not in masked.values  # appartient à l'extension
    assert unmask(masked.text, masked.values) == "Total {AMOUNT_0} {CURRENCY_0} et 500 FCFA"


def test_texte_sans_variable_inchange():
    masked = mask("Choisissez un bénéficiaire")
    assert masked.text == "Choisissez un bénéficiaire"
    assert not masked.server_masked


def test_controle_des_marqueurs():
    src = "Envoyer {AMOUNT_0} {CURRENCY_0}"
    assert placeholders_preserved(src, "{CURRENCY_0} {AMOUNT_0} xx")  # ordre libre
    assert not placeholders_preserved(src, "xx {AMOUNT_0}")  # perdu
    assert not placeholders_preserved(src, "{AMOUNT_0} {AMOUNT_0} {CURRENCY_0}")  # dupliqué
    assert not placeholders_preserved(src, "{AMOUNT_0} {CURRENCY_0} {DATE_0}")  # inventé
    assert find_placeholders("{A_1} {A_1}")["{A_1}"] == 2
