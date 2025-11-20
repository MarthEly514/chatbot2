# 🔍 Chatbot WhatsApp - Détection Fake News & Deepfakes

## Structure du Projet

```
whatsapp-fakenews-detector/
│
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuration (existant, amélioré)
│   ├── webhook.py                   # Webhooks Meta (existant, amélioré)
│   ├── sender.py                    # Envoi messages (existant, amélioré)
│   ├── message_processor.py         # Router des messages (NOUVEAU)
│   ├── fake_news_detector.py        # Analyse textes (NOUVEAU)
│   ├── deepfake_detector.py         # Analyse médias (NOUVEAU)
│   ├── media_handler.py             # Téléchargement médias (NOUVEAU)
│   └── utils.py                     # Fonctions utilitaires (NOUVEAU)
│
├── models/                          # Cache des modèles (optionnel)
│
├── main.py                          # Point d'entrée (existant, amélioré)
├── requirements.txt                 # Dépendances
├── .env.example                     # Template configuration
├── .gitignore
├── Procfile                         # Pour Railway
├── runtime.txt                      # Version Python pour Railway
└── README.md                        # Documentation
```

## Fichiers à créer/modifier

1. ✅ `requirements.txt` - Dépendances complètes
2. ✅ `app/config.py` - Configuration améliorée
3. ✅ `app/message_processor.py` - Router principal
4. ✅ `app/fake_news_detector.py` - Détection fake news
5. ✅ `app/deepfake_detector.py` - Détection deepfakes
6. ✅ `app/media_handler.py` - Téléchargement médias
7. ✅ `app/sender.py` - Envoi messages amélioré
8. ✅ `app/webhook.py` - Webhooks amélioré
9. ✅ `app/utils.py` - Utilitaires
10. ✅ `main.py` - Point d'entrée amélioré
11. ✅ `.env.example` - Template
12. ✅ `Procfile` - Railway
13. ✅ `runtime.txt` - Python version
14. ✅ `README.md` - Documentation