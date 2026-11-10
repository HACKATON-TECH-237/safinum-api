# 🌍 Safinum API

> **Backend FastAPI** dédié à l'extension Chrome Safinum pour la traduction et le traitement en langues nationales.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/managed_by-uv-DE5FE9?style=for-the-badge)](https://docs.astral.sh/uv/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📌 Présentation

**Safinum API** est le moteur backend conçu pour alimenter l'extension Chrome du projet Safinum. Son objectif principal est de briser les barrières linguistiques sur le web en fournissant des services de traduction instantanée vers et depuis les langues nationales / locales.

### ✨ Fonctionnalités principales
- 🔄 **Traduction bidirectionnelle** : Traduction de texte entre langues internationales (français, anglais...) et langues nationales.
- 🔍 **Détection automatique de langue** : Identification de la langue source du contenu sélectionné.
- ⚡ **Performances élevées** : Construit sur **FastAPI** pour des temps de réponse minimaux.
- 🔌 **Prêt pour l'extension Chrome** : Support des requêtes asynchrones et configuration CORS dédiée.
- 📖 **Documentation auto-générée** : Swagger UI et ReDoc intégrés d'office.

---

## 🛠️ Stack Technique

- **Langage** : Python 3.14+
- **Framework Web** : [FastAPI](https://fastapi.tiangolo.com/)
- **Gestionnaire de dépendances & environnement** : [uv](https://docs.astral.sh/uv/)
- **Serveur ASGI** : Uvicorn
- **Conteneurisation** : Docker & Docker Compose

---

## 🚀 Démarrage Rapide

### Prérequis
- [uv](https://docs.astral.sh/uv/) installé sur votre machine (recommandé) ou Python 3.14+
- [Docker](https://www.docker.com/) & Docker Compose (optionnel)

### 1. Installation avec `uv`

```bash
# Cloner le projet (si ce n'est pas déjà fait)
git clone <url-du-repo>
cd Safinum/safinum-api

# Synchroniser l'environnement et installer les dépendances
uv sync
```

### 2. Variables d'environnement

Créez un fichier `.env` à la racine de `safinum-api` :

```env
APP_ENV=development
PORT=8000
HOST=0.0.0.0
ALLOWED_ORIGINS=chrome-extension://*,http://localhost:3000
# Clé API pour le modèle d'IA / service de traduction (si applicable)
TRANSLATION_API_KEY=votre_cle_ici
```

### 3. Lancer le serveur de développement

Avec `uv` :
```bash
uv run fastapi dev
# ou avec uvicorn directement :
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur sera accessible sur [http://localhost:8000](http://localhost:8000).

---

## 🐳 Déploiement avec Docker

Pour lancer l'API dans un conteneur isolé avec Docker Compose :

```bash
docker compose up --build -d
```

Pour arrêter le service :
```bash
docker compose down
```

---

## 📖 Documentation de l'API

Une fois le serveur démarré, vous pouvez tester et explorer les points de terminaison directement via :
- **Swagger UI** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** : [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🛣️ Aperçu des Endpoints

| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Vérification de l'état du service |
| `GET` | `/api/v1/languages` | Liste des langues nationales prises en charge |
| `POST` | `/api/v1/translate` | Traduit un texte vers la langue cible demandée |
| `POST` | `/api/v1/detect` | Détecte la langue d'un texte fourni |

### Exemple de requête de traduction (`POST /api/v1/translate`)

```json
{
  "text": "Bonjour, bienvenue sur la plateforme.",
  "source_lang": "fr",
  "target_lang": "fon"
}
```

**Réponse :**
```json
{
  "original_text": "Bonjour, bienvenue sur la plateforme.",
  "translated_text": "Kú àbɔ̀, mǐ d'alɔ we nú tòxó nùkúnjí.",
  "source_lang": "fr",
  "target_lang": "fon"
}
```

---

## 📁 Structure Recommandée du Projet

```text
safinum-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── translate.py
│   │       │   └── languages.py
│   │       └── router.py
│   ├── core/
│   │   └── config.py
│   ├── models/
│   │   └── translation.py
│   ├── schemas/
│   │   └── translation.py
│   └── services/
│       └── translation_service.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── main.py
└── README.md
```

---

## 👥 Équipe & Hackathon

Projet développé dans le cadre du **Hackathon Safinum**.
