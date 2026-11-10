# Contrat d'interface extension ↔ API

Version 0.1 : à valider entre le Dev 1 (extension) et le Dev 2 (moteur linguistique).
Swagger interactif : `http://localhost:8000/docs`.

## Règles côté extension (obligatoires)

1. **Ne jamais envoyer** le DOM, ni le contenu de `input`, `textarea`, `select`, `contenteditable`, ni les zones sensibles (nom et numéro du bénéficiaire, numéro de compte, références).
2. **Masquer les variables avant l'envoi** avec des marqueurs `{TYPE_n}`, numérotés par type dans l'ordre d'apparition :
   `"Vous envoyez 25 000 FCFA"` → `"Vous envoyez {AMOUNT_0} {CURRENCY_0}"`.
   Types conseillés : `AMOUNT`, `CURRENCY`, `DATE`, `NUM`, `REF`, `NAME`. Garder la correspondance localement, puis réinjecter les valeurs dans `translation`.
   Le serveur masque de nouveau par sécurité tout chiffre, devise, date ou e-mail resté en clair. Il ne peut pas repérer les noms propres : c'est à l'extension de le faire.
3. **Envoyer par lots** : un seul appel par écran, et non un appel par libellé.
4. **Si l'API ne répond pas** (erreur réseau ou délai supérieur à environ 6 s) : laisser le texte original. Le site ne doit jamais être bloqué.

## `POST /api/v1/translate`

```json
{
  "source_lang": "fr",
  "target_lang": "xx",
  "items": [
    { "id": "n12", "text": "Solde disponible", "context": "balance.title", "risk_level": "medium" },
    { "id": "n13", "text": "Vous envoyez {AMOUNT_0} {CURRENCY_0}", "context": "transfer.fees", "risk_level": "critical" }
  ]
}
```

| Champ | Contrainte |
|---|---|
| `items` | 1 à 100 éléments, `id` uniques |
| `text` | 1 à 1000 caractères, variables masquées |
| `risk_level` | `low` \| `medium` (par défaut) \| `high` \| `critical` |
| `context` | Facultatif ; permet de choisir la traduction propre à un écran |

Réponse (même ordre que la requête) :

```json
{
  "source_lang": "fr",
  "target_lang": "xx",
  "glossary_version": "0.1.0",
  "items": [
    { "id": "n12", "translation": "…", "source": "glossary", "status": "ok", "confidence": 1.0 },
    { "id": "n13", "translation": "Vous envoyez {AMOUNT_0} {CURRENCY_0}", "source": "machine",
      "status": "needs_review", "suggestion": "…" }
  ]
}
```

### Que faire selon `status`

| `status` | Affichage dans l'extension |
|---|---|
| `ok` | Afficher `translation` (après réinjection des variables). |
| `needs_review` | Afficher **l'original** avec un indicateur « traduction à vérifier ». `suggestion` peut être montrée dans une infobulle. |
| `original_kept` | Afficher l'original (moteur indisponible, variable altérée ou rien à traduire). |

`source` : `glossary` (traduction validée), `machine` (texte inédit) ou `fallback`.

Une traduction automatique d'un texte `high` ou `critical` n'est **jamais** renvoyée en `ok`.

## `GET /api/v1/languages`

Liste des langues disponibles : `code`, `name`, `glossary_version`, `validated_entries`, `validated`.

## `GET /api/v1/glossary/{lang}`

Entrées validées du glossaire. L'extension peut les mettre en cache, en se basant sur `version`, et traduire les libellés connus **sans appel réseau**. `/translate` ne sert alors que pour les textes inédits.

## `GET /health`

`{"status": "ok", "provider": "mock"}`
