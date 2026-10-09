# Pousse — surveillance et arrosage d’une plante

Pousse est un projet d’objets connectés pour surveiller une plante en pot et automatiser son arrosage. Le dépôt contient une maquette d’interface NiceGUI et des programmes MQTT pour le Raspberry Pi.

## État actuel

Le dossier `raspberry_pi/` contient les deux programmes MQTT :

- [publicateur.py](raspberry_pi/publicateur.py) lit l’interrupteur à flotteur et publie l’état du réservoir toutes les 5 secondes sur `ferixu/eau`, avec un horodatage UTC.
- [subscriber.py](raspberry_pi/subscriber.py) s’abonne à ce topic, affiche les mesures reçues et les ajoute à `donnees/lectures_capteurs.jsonl`, dans le dossier depuis lequel il est lancé.

Les deux programmes utilisent le broker MQTT local sur `localhost:1883` et se lancent dans deux terminaux distincts. La publication du BH1750 est commentée pour le moment.

Les pilotes du BH1750, du STEMMA Soil Sensor et du feu ARD-625 sont présents, mais ils ne sont pas intégrés au programme de collecte actif. L’humidité et la température du sol ne sont donc pas mesurées par le programme principal; la commande de la pompe n’est pas implémentée. La maquette NiceGUI est également simulée et n’est pas connectée au broker ni au matériel.

Les exigences prévues, leurs seuils et leurs règles sont détaillés dans [EXIGENCES.md](EXIGENCES.md). Les fonctions ci-dessus décrivent l’état réellement présent dans le code.

## Capteurs et actionneurs

| Composant | Rôle prévu | État dans le code |
| --- | --- | --- |
| Interrupteur à flotteur SENS-112-200 | Détecter si le réservoir contient de l’eau | Lu et publié sur `ferixu/eau` toutes les 5 secondes |
| BH1750 (#4681) | Mesurer la luminosité en lux sur I²C | Pilote présent; lecture et publication désactivées dans `publicateur.py` |
| STEMMA Soil Sensor (#4026) | Mesurer l’humidité et la température du sol sur I²C | Pilote présent; pas encore utilisé par le programme de collecte |
| Feu tricolore ARD-625 | Afficher l’état de la plante | Pilote présent; pas intégré à la logique du programme |
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
