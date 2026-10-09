# Programmes Raspberry Pi : publicateur et subscriber

Ce dossier contient deux programmes à lancer ensemble dans des terminaux distincts :

| Programme | Rôle |
| --- | --- |
| [publicateur.py](publicateur.py) | Lire l’interrupteur à flotteur et publier l’état du réservoir sur `ferixu/eau` toutes les 5 secondes |
| [subscriber.py](subscriber.py) | Recevoir les messages de `ferixu/eau`, les afficher et les enregistrer en JSON Lines |

Le trajet des données est : **flotteur → publicateur → broker MQTT local → subscriber → fichier JSON Lines**. Les deux scripts se connectent à `localhost:1883`; les instructions ci-dessous les exécutent donc sur le même Raspberry Pi. La fréquence de publication actuelle ne correspond pas encore aux exigences fonctionnelles, qui demandent une vérification toutes les 10 minutes.

La lecture du BH1750 a été commentée dans `publicateur.py`. Les pilotes du BH1750, du STEMMA Soil Sensor et du feu ARD-625 sont présents, mais ces composants ne sont pas encore utilisés par le programme actif. La pompe et sa logique de déclenchement ne sont pas implémentées. La maquette de l’interface est simulée et n’est pas reliée à ces messages.

## Matériel et branchements

Pour la collecte active :

- Raspberry Pi avec Raspberry Pi OS;
- interrupteur à flotteur branché au GPIO BCM 16.

Dans `Flotteur.py`, l’état pressé signifie que le réservoir est vide et l’état relâché signifie qu’il contient de l’eau. Vérifiez que le montage physique correspond à cette interprétation.

Le BH1750 prévu se branche sur I²C : SDA au GPIO 2 (broche physique 3), SCL au GPIO 3 (broche physique 5) et GND à GND. Il n’est pas lu par le programme actif. Pour une future utilisation, activez I²C avec `sudo raspi-config` (**Interface Options → I2C → Enable**) et vérifiez le bus avec `i2cdetect -y 1`.

## Installation

Depuis la racine du dépôt, installez le broker MQTT, les outils de test et les paquets système GPIO :

```bash
sudo apt update
sudo apt install -y python3-venv python3-gpiozero python3-lgpio i2c-tools mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```

Créez l’environnement Python du Raspberry Pi :

```bash
cd raspberry_pi
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

L’option `--system-site-packages` permet à l’environnement virtuel d’utiliser les pilotes GPIO installés par Raspberry Pi OS.

## Lancer la collecte

Dans un terminal, depuis `raspberry_pi`, lancez le publicateur :

```bash
source .venv/bin/activate
python publicateur.py
```

Le broker doit être actif sur `localhost:1883`. Le programme publie sur le topic `ferixu/eau` un objet JSON de cette forme :

```json
{"vide": false, "horodatage": "2026-10-09T12:00:00+00:00"}
```

L’horodatage est au format ISO 8601 en UTC. Appuyez sur `Ctrl+C` pour arrêter le publicateur.

## Recevoir et enregistrer les messages

Dans un second terminal, depuis la racine du dépôt, entrez dans `raspberry_pi`, activez le même environnement et démarrez le subscriber :

```bash
cd raspberry_pi
source .venv/bin/activate
python subscriber.py
```

Le subscriber écoute `ferixu/eau`, affiche les messages reçus et les ajoute à `raspberry_pi/donnees/lectures_capteurs.jsonl` avec les commandes ci-dessus. Le chemin `donnees/` est relatif au dossier depuis lequel le script est lancé. Le dossier est créé au démarrage et le fichier à la réception du premier message; chaque mesure occupe une ligne. Appuyez sur `Ctrl+C` dans chaque terminal pour arrêter les programmes.

Pour observer les messages MQTT sans les enregistrer, utilisez un autre terminal :

```bash
mosquitto_sub -h localhost -t 'ferixu/#' -v
```

## Fonctions prévues

Les exigences complètes sont dans [../EXIGENCES.md](../EXIGENCES.md). La publication de la luminosité, les mesures d’humidité et de température, le cumul des heures de lumière, la logique du feu et la commande sécurisée de la pompe restent à intégrer au programme actif.
