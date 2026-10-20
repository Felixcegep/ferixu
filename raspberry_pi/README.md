# Organisation du projet
```
Ferixu backend
├── actionneurs         : classes des actionneurs (sauf flotteur)
├── capteurs            : classes des capteurs (et flotteur)
├── config.py           : données de configuration
├── ingestion           : code pour le subscriber
├── main.py             : publisher temporaire
├── publication_donnees : classe de publisher
├── requirements.txt    : dépendances
└── tests               : tests
```

# Utilisation
1. Faire un venv : `python -m venv .venv`
2. Installer les requirements : `pip install -r requirements.md`
3. Exécuter le subscriber : `python -m ingestion.service_ingestion`
4. Exécuter le publisher : `python main.py`