# Pousse — Ferixu

Système de surveillance et d'arrosage prévu pour un basilic en pot avec un Raspberry Pi 4, des capteurs et des actionneurs.

La [remise de la partie 1](documentation/remise_partie_1.md) est prévue le **20 octobre 2026 (10 %)**. Les [spécifications corrigées EF01 à EF24](documentation/exigences_fonctionnelles.md) décrivent les comportements attendus; l'[inventaire](documentation/inventaire_materiel.md) distingue les composants reçus, alternatifs et non reçus.

## État du code

- Le flotteur est lu et horodaté en UTC immédiatement, puis toutes les 10 minutes.
- Les mesures sont publiées vers le broker MQTT local; un service distinct les reçoit et les enregistre en JSON Lines.
- Le feu rouge est commandé lorsque le réservoir est insuffisant (EF12); le feu reste éteint quand les autres conditions globales sont inconnues.
- Un capteur absent ou en erreur est signalé comme indisponible, sans fausse mesure; les autres lectures continuent et une reconnexion est tentée à la prochaine échéance.
- Le BH1750 et le sol peuvent être activés explicitement avec `--lumiere` et `--sol`, aux périodes prévues de 60 et 600 secondes. Le sol nécessite une calibration pour produire un pourcentage.
- Le pilote sécurisé de pompe est présent, mais non activé dans le programme principal. La logique d'arrosage automatique reste à intégrer.
- L'interface NiceGUI est une **maquette simulée**; elle ne reçoit pas les mesures MQTT et ne commande aucun composant.

Les tests logiciels ont réussi avec des GPIO simulés et un vrai broker local. **Le montage physique et le fonctionnement sur Raspberry Pi restent à valider.** La liste détaillée des fonctions restantes est dans [le suivi de la remise](documentation/todo_prochain_cours.md).

## Installation et démonstration Raspberry Pi

Les instructions complètes de matériel, câblage, `.venv`, dépendances, broker, topics, payloads et démonstration sont dans [raspberry_pi/README.md](raspberry_pi/README.md).

Après l'installation des paquets système indiqués dans ce document, depuis la racine :

```bash
python3 -m venv --system-site-packages raspberry_pi/.venv
source raspberry_pi/.venv/bin/activate
python -m pip install -r raspberry_pi/requirements.txt
```

Configurer `.env` à partir de `.env.example` pour `localhost:1883`. Démarrer Mosquitto puis, dans deux terminaux avec le `.venv` activé :

```bash
# Terminal A : attendre « Ingestion prête ».
python -m raspberry_pi.ingestion.service_ingestion
```

```bash
# Terminal B : flotteur réel et feu.
python -m raspberry_pi.main
```

Les données se trouvent dans `donnees/lectures_capteurs.jsonl` à la racine :

```bash
tail -f donnees/lectures_capteurs.jsonl
mosquitto_sub -h localhost -t 'ferixu/#' -q 1 -v
```

`Ctrl+C` arrête la collecte et libère les ressources. Les broches et polarités doivent correspondre au montage réel avant tout lancement.

## Structure

```text
raspberry_pi/
├── config.py               # Configuration .env, broches BCM, fréquences
├── main.py                 # Acquisition périodique et orchestration
├── mesures.py              # Validation des payloads horodatés
├── logique_decision.py     # Règle EF12 du feu, indépendante de MQTT
├── capteurs/               # Classe abstraite et pilotes
├── actionneurs/            # Feu et pompe (pompe non activée)
├── publication_donnees/    # Client publicateur MQTT
├── ingestion/             # Abonnement et enregistrement du fichier
└── tests/                 # Tests ciblés et essai Mosquitto local
```

## Maquette NiceGUI

Installer dans un environnement distinct des dépendances matérielles :

```bash
python3 -m venv frontend/.venv
source frontend/.venv/bin/activate
python -m pip install -r frontend/requirements.txt
python frontend/main.py
```

Ouvrir <http://localhost:8080>. L'installation avec `uv sync` puis `uv run python frontend/main.py` reste possible. Pour le parcours d'intégration de la maquette, garder le serveur démarré et utiliser `uv run pytest -q frontend/tests/test_maquette_integration.py`. Au besoin, installer Chromium avec `uv run playwright install chromium`.

## Vérification de la collecte

```bash
python -m pip install -r raspberry_pi/tests/requirements.txt
python -m pytest -q raspberry_pi/tests
```

Ces tests vérifient le logiciel; ils ne valident pas le câblage ou la calibration du montage physique.
