import asyncio

from app.services.providers.base import ProviderError
from tests.conftest import make_client, translate


class BrokenPlaceholderProvider:
    """Moteur qui « oublie » les variables : le pipeline doit garder l'original."""

    name = "broken"

    async def translate(self, texts, source_lang, target_lang):
        return ["traduction sans variable" for _ in texts]


class SlowProvider:
    name = "slow"

    async def translate(self, texts, source_lang, target_lang):
        await asyncio.sleep(2)
        return texts


class FailingProvider:
    name = "failing"

    async def translate(self, texts, source_lang, target_lang):
        raise ProviderError("quota dépassé")


def with_provider(provider, **settings):
    client = make_client(**settings)
    client.__enter__()
    client.app.state.pipeline.provider = provider
    return client


# --- Service --------------------------------------------------------------------------------


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "mock"}


def test_langues_et_glossaire(client):
    langs = client.get("/api/v1/languages").json()
    assert langs[0]["code"] == "tst"
    assert langs[0]["validated_entries"] == 5  # T-003 n'est pas validée

    glossary = client.get("/api/v1/glossary/tst").json()
    assert glossary["version"] == "test-1"
    assert "Frais" not in [e["source"] for e in glossary["entries"]]
    assert client.get("/api/v1/glossary/inconnue").status_code == 404


# --- Glossaire ------------------------------------------------------------------------------


def test_glossaire_prioritaire_et_insensible_aux_espaces(client):
    [item] = translate(client, {"id": "a", "text": "  solde   DISPONIBLE ", "context": "balance.title"})
    assert item == {
        "id": "a",
        "translation": "SOLDE-TST",
        "source": "glossary",
        "status": "ok",
        "confidence": 1.0,
    }


def test_glossaire_selon_contexte(client):
    generic, button = translate(
        client,
        {"id": "a", "text": "Envoyer"},
        {"id": "b", "text": "Envoyer", "context": "transfer.submit"},
    )
    assert generic["translation"] == "ENVOYER-TST"
    assert button["translation"] == "ENVOYER-BOUTON-TST"


def test_glossaire_avec_variables_de_l_extension(client):
    [item] = translate(client, {"id": "a", "text": "Montant envoyé : {AMOUNT_0} {CURRENCY_0}"})
    assert item["translation"] == "{CURRENCY_0} {AMOUNT_0} ENVOI-TST"
    assert item["source"] == "glossary"


def test_entree_non_validee_ignoree(client):
    [item] = translate(client, {"id": "a", "text": "Frais", "risk_level": "low"})
    assert item["source"] == "machine"  # pas la traduction "a_revoir" du glossaire


def test_entree_de_glossaire_incoherente_ignoree(client):
    [item] = translate(client, {"id": "a", "text": "Total {AMOUNT_0}", "risk_level": "low"})
    assert item["translation"] != "TOTAL-TST"


# --- Texte inédit ---------------------------------------------------------------------------


def test_texte_inedit_traduit_avec_valeurs_reinjectees(client):
    [item] = translate(
        client, {"id": "a", "text": "Votre solde est de 250 000 FCFA", "risk_level": "low"}
    )
    assert item["source"] == "machine"
    assert item["status"] == "ok"
    assert item["translation"] == "[tst] Votre solde est de 250 000 FCFA"


def test_message_critique_garde_l_original(client):
    text = "Attention : ce transfert de 25 000 FCFA est irréversible"
    [item] = translate(client, {"id": "a", "text": text, "risk_level": "critical"})
    assert item["status"] == "needs_review"
    assert item["translation"] == text
    assert item["suggestion"] == f"[tst] {text}"


def test_variables_seules_non_envoyees_au_moteur(client):
    [item] = translate(client, {"id": "a", "text": "{AMOUNT_0} {CURRENCY_0}"})
    assert item["status"] == "original_kept"
    assert item["translation"] == "{AMOUNT_0} {CURRENCY_0}"


# --- Repli ----------------------------------------------------------------------------------


def test_moteur_qui_perd_une_variable():
    client = with_provider(BrokenPlaceholderProvider())
    [item] = translate(client, {"id": "a", "text": "Frais : 0 FCFA", "risk_level": "low"})
    assert item["status"] == "original_kept"
    assert item["translation"] == "Frais : 0 FCFA"


def test_moteur_trop_lent():
    client = with_provider(SlowProvider(), provider_timeout_seconds=0.1)
    [item] = translate(client, {"id": "a", "text": "Nouveau message", "risk_level": "low"})
    assert item["status"] == "original_kept"


def test_moteur_en_erreur():
    client = with_provider(FailingProvider())
    glossary_item, machine_item = translate(
        client,
        {"id": "a", "text": "Solde disponible"},
        {"id": "b", "text": "Nouveau message", "risk_level": "low"},
    )
    assert glossary_item["source"] == "glossary"  # le glossaire marche toujours
    assert machine_item["status"] == "original_kept"


def test_sans_moteur():
    with make_client(translation_provider="none") as client:
        [item] = translate(client, {"id": "a", "text": "Nouveau message"})
        assert item["status"] == "original_kept"


# --- Validation & sécurité ------------------------------------------------------------------


def test_limites_de_requete():
    with make_client(max_items_per_request=2, max_text_length=10) as client:
        url = "/api/v1/translate"
        items = [{"id": str(i), "text": "abc"} for i in range(3)]
        assert client.post(url, json={"target_lang": "tst", "items": items}).status_code == 413
        long_item = [{"id": "a", "text": "x" * 11}]
        assert client.post(url, json={"target_lang": "tst", "items": long_item}).status_code == 413
        dup = [{"id": "a", "text": "a"}, {"id": "a", "text": "b"}]
        assert client.post(url, json={"target_lang": "tst", "items": dup}).status_code == 422
        assert client.post(url, json={"target_lang": "tst", "items": []}).status_code == 422


def test_cors_extension_chrome(client):
    ext = "chrome-extension://" + "a" * 32
    resp = client.options(
        "/api/v1/translate",
        headers={"Origin": ext, "Access-Control-Request-Method": "POST"},
    )
    assert resp.headers.get("access-control-allow-origin") == ext

    resp = client.options(
        "/api/v1/translate",
        headers={"Origin": "https://site-malveillant.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in resp.headers
