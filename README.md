# 🎙️ Bafoka Voice Banking Assistant

Assistant vocal bancaire intelligent pour WhatsApp intégrant:
- 🗣️ Speech-to-Text (Whisper)
- 🧠 NLU avec Groq
- 🔗 Intégration blockchain Bafoka
- 💬 Gestion conversationnelle avec mémoire de contexte

## 📁 Structure du Projet

\`\`\`
bafoka-voice-assistant/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── config.py               # Configuration centralisée
│   ├── models/                 # Modèles de données
│   │   ├── __init__.py
│   │   ├── requests.py         # Schémas de requêtes
│   │   └── responses.py        # Schémas de réponses
│   ├── services/               # Logique métier
│   │   ├── __init__.py
│   │   ├── speech_service.py   # Transcription audio
│   │   ├── nlu_service.py      # Analyse NLU
│   │   ├── blockchain_service.py # API Bafoka
│   │   └── conversation_service.py # Gestion contexte
│   ├── routes/                 # Endpoints API
│   │   ├── __init__.py
│   │   ├── voice.py            # Routes vocales
│   │   └── health.py           # Health checks
│   ├── utils/                  # Utilitaires
│   │   ├── __init__.py
│   │   ├── text_cleaner.py     # Nettoyage texte
│   │   ├── validators.py       # Validations
│   │   └── extractors.py       # Extraction JSON
│   └── middleware/             # Middlewares
│       ├── __init__.py
│       └── error_handler.py    # Gestion erreurs
├── tests/                      # Tests unitaires
├── data/                       # Données temporaires
│   ├── audio/                  # Fichiers audio
│   └── sessions/               # Sessions utilisateur
├── requirements.txt            # Dépendances
├── .env.example               # Variables d'environnement
└── docker-compose.yml         # Déploiement Docker
\`\`\`

## 🚀 Installation

\`\`\`bash
# Cloner le projet
git clone <repo_url>
cd bafoka-voice-assistant

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Télécharger les modèles
python -m spacy download fr_core_news_sm
\`\`\`

## ⚙️ Configuration

Créer un fichier `.env`:
\`\`\`env
# API Keys
GROQ_API_KEY=votre_cle_groq
HF_TOKEN=votre_token_huggingface

# Bafoka Blockchain API
BAFOKA_API_BASE_URL=https://api.bafoka.com
BAFOKA_API_KEY=votre_cle_bafoka

# Configuration
ENVIRONMENT=development
DEBUG=True
\`\`\`

## 🎯 Lancer l'API

\`\`\`bash
# Mode développement avec rechargement auto
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mode production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
\`\`\`

## 📚 Documentation API

Une fois lancé, accéder à:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Tests

\`\`\`bash
pytest tests/ -v
\`\`\`

## 🔄 Flux de Traitement

1. **WhatsApp** → Envoie audio
2. **API /voice/transcribe** → Transcription Whisper
3. **API /voice/analyze** → Analyse NLU (Groq)
4. **API /voice/process** → Orchestration complète
5. **Service Blockchain** → Exécution action Bafoka
6. **Réponse** → Retour à WhatsApp
