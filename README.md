# Pousse — surveillance et arrosage d’une plante

Pousse est un projet d’objets connectés pour surveiller une plante en pot et automatiser son arrosage. Le dépôt contient une maquette d’interface NiceGUI et des programmes MQTT pour le Raspberry Pi.

## Première remise

La remise de la partie 1 vaut **10 %** et aura lieu le **20 octobre 2026**, avec une présentation en équipe en classe. Les [consignes et critères d’évaluation](documentation/remise_partie_1.md) détaillent le code à remettre et la démonstration attendue.

## État actuel

Le dossier `raspberry_pi/` contient les deux programmes MQTT :

- [publicateur_mqtt.py](raspberry_pi/publication_donnees/publicateur_mqtt.py) assure la communication MQTT; `main.py` lit l’interrupteur à flotteur dans le thread principal toutes les 10 minutes. Un thread séparé publie les nouvelles acquisitions sur `ferixu/eau` toutes les 10 secondes, avec leur horodatage UTC conservé.
- [service_ingestion.py](raspberry_pi/ingestion/service_ingestion.py) s’abonne à ce topic, affiche les mesures reçues et les ajoute à `donnees/lectures_capteurs.jsonl`, à la racine du dépôt, comme dans la démo du cours.

Les deux programmes utilisent le broker MQTT local sur `localhost:1883` et se lancent dans deux terminaux distincts. Le flotteur est le seul capteur utilisé par `main.py`. Le feu est commandé à chaque lecture : rouge si le réservoir est insuffisant (EF12), éteint sinon.

Les pilotes du BH1750 et du STEMMA Soil Sensor sont présents, mais ils ne sont pas intégrés au programme de collecte actif. Le feu ARD-625 est intégré pour le scénario réservoir insuffisant d’EF12; la logique complète EF10 à EF13 reste à réaliser. L’humidité et la température du sol ne sont donc pas mesurées par le programme principal; la commande de la pompe n’est pas implémentée. La maquette NiceGUI est également simulée et n’est pas connectée au broker ni au matériel.

La [documentation du projet](documentation/README.md) regroupe les composants, la fiche du basilic et l’[inventaire du matériel](documentation/inventaire_materiel.md). Les exigences prévues, leurs seuils et leurs règles sont détaillés dans [documentation/exigences_fonctionnelles.md](documentation/exigences_fonctionnelles.md). Les fonctions ci-dessus décrivent l’état réellement présent dans le code.

## Capteurs et actionneurs

| Composant | Rôle prévu | État dans le code |
| --- | --- | --- |
| Interrupteur à flotteur SENS-112-200 | Détecter si le réservoir contient de l’eau | Lu et publié sur `ferixu/eau` toutes les 10 minutes |
| BH1750 (#4681) | Mesurer la luminosité en lux sur I²C | Pilote présent; pas utilisé par `main.py` |
| STEMMA Soil Sensor (#4026) | Mesurer l’humidité et la température du sol sur I²C | Pilote présent; pas encore utilisé par le programme de collecte |
| Feu tricolore ARD-625 | Afficher l’état de la plante | Rouge si le réservoir est insuffisant; éteint sinon |
| Relais STEMMA (#4409) et pompe 3 V (#4547) | Arroser selon les seuils et les commandes | Pas encore implémentés dans le programme actif |

Les procédures d’installation et de démonstration sur le Raspberry Pi sont dans [raspberry_pi/README.md](raspberry_pi/README.md).

## Maquette NiceGUI

La maquette contient cinq pages : état normal, surveillance, alerte, contrôles et paramètres. Elle permet de parcourir les principaux scénarios d’interface. Ses mesures et ses actions sont simulées : les boutons ne commandent pas les composants physiques.

À la racine du dépôt, installez les dépendances avec [uv](https://docs.astral.sh/uv/) et démarrez l’application :

```bash
uv sync
uv run python frontend/main.py
```

Ouvrez <http://localhost:8080>.

## Vérification de la maquette

Dans un premier terminal, laissez l’application démarrée. Dans un second terminal, lancez le test d’intégration :

```bash
uv run pytest -q frontend/tests/test_maquette_integration.py
```

Le test pilote les pages et génère des captures dans `maquettes/`. Si aucun navigateur compatible n’est installé, installez Chromium avec `uv run playwright install chromium`.
