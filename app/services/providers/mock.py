class MockProvider:
    """Faux moteur pour développer l'extension en parallèle : préfixe le texte avec la langue cible.

    À remplacer par un vrai moteur (NLLB, Google, Azure, LLM...) une fois la langue choisie
    et le moteur vérifié par les locuteurs. Implémenter la même méthode `translate`.
    """

    name = "mock"

    async def translate(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [f"[{target_lang}] {t}" for t in texts]
