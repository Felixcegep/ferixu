# Programmes Raspberry Pi : publicateur et subscriber

Ce dossier contient deux programmes à lancer ensemble dans des terminaux distincts :

| Programme | Rôle |
| --- | --- |
| [publicateur_mqtt.py](publication_donnees/publicateur_mqtt.py) | Classe `PublicateurMQTT` appelée par `main.py` pour publier l’état du réservoir sur `ferixu/eau` toutes les 10 minutes |
| [service_ingestion.py](ingestion/service_ingestion.py) | Recevoir les messages de `ferixu/eau`, les afficher et les enregistrer en JSON Lines |

Le trajet des données est : **flotteur → publicateur → broker MQTT local → subscriber → fichier JSON Lines**. Les deux scripts se connectent à `localhost:1883`; les instructions ci-dessous les exécutent donc sur le même Raspberry Pi. La première acquisition est immédiate; le thread MQTT la publie à sa prochaine échéance, au plus environ 10 secondes plus tard si le broker répond normalement.

Le flotteur est le seul capteur utilisé par `main.py`. Le feu ARD-625 est commandé à chaque lecture : rouge si le réservoir est insuffisant, éteint sinon. Les pilotes du BH1750 et du STEMMA Soil Sensor restent hors du programme actif. La pompe et sa logique de déclenchement ne sont pas implémentées. La maquette de l’interface est simulée et n’est pas reliée à ces messages.

## Matériel et branchements

Pour la collecte active :

- Raspberry Pi avec Raspberry Pi OS;
- interrupteur à flotteur branché au GPIO BCM 16 (broche physique 36);
- feu ARD-625 : rouge BCM 23 (physique 16), jaune BCM 22 (physique 15), vert BCM 27 (physique 13).

Les broches du feu sont définies dans `raspberry_pi/config.py`, avec la même attribution que le `config.py` racine. Elles doivent être confirmées sur le montage réel. Vérifier la masse commune, les résistances et la compatibilité des entrées du module avec les sorties GPIO 3,3 V; l'alimentation exacte doit être vérifiée dans la fiche du module reçu. Ne pas appliquer de 5 V à un GPIO. Aucun branchement n'est validé par les tests logiciels.

Dans `capteurs/flotteur.py`, l’état pressé signifie que le réservoir est vide et l’état relâché signifie qu’il contient de l’eau. Vérifiez que le montage physique correspond à cette interprétation.

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

Dans un terminal, depuis la racine du dépôt, lancez le publicateur :

```bash
source raspberry_pi/.venv/bin/activate
cd raspberry_pi
python main.py
```

Le broker doit être actif sur `localhost:1883`. Le programme publie sur le topic `ferixu/eau` un objet JSON de cette forme :

```json
{"etat": "suffisant", "vide": false, "horodatage": "2026-10-09T12:00:00+00:00"}
```

L’horodatage est au format ISO 8601 en UTC. Appuyez sur `Ctrl+C` pour arrêter le publicateur.

## Recevoir et enregistrer les messages

Dans un second terminal, depuis la racine du dépôt, activez le même environnement et démarrez le service d’ingestion :

```bash
source raspberry_pi/.venv/bin/activate
python -m raspberry_pi.ingestion.service_ingestion
```

Le subscriber écoute `ferixu/eau`, affiche les messages reçus et les ajoute à `donnees/lectures_capteurs.jsonl` avec les commandes ci-dessus. Le chemin est fixé à la racine du dépôt avec `config.RACINE`, comme dans la démo de la prof. Le dossier est créé au démarrage et le fichier à la réception du premier message; chaque mesure occupe une ligne. Appuyez sur `Ctrl+C` dans chaque terminal pour arrêter les programmes.

Pour observer les messages MQTT sans les enregistrer, utilisez un autre terminal :

```bash
mosquitto_sub -h localhost -t 'ferixu/#' -v
```

## Fonctions prévues

Les exigences complètes sont dans [../EXIGENCES.md](../EXIGENCES.md). La publication de la luminosité, les mesures d’humidité et de température, le cumul des heures de lumière, la logique complète du feu (EF10 à EF13) et la commande sécurisée de la pompe restent à intégrer au programme actif.

## Organisation

```text
raspberry_pi/
├── actionneurs/
│   ├── __init__.py
│   ├── feu_tricolore.py
│   └── pompe.py
├── capteurs/
│   ├── __init__.py
│   ├── capteur.py
│   ├── flotteur.py
│   ├── capteur_bh1750.py
│   └── capteur_sol.py
├── ingestion/
│   ├── __init__.py
│   └── service_ingestion.py
└── publication_donnees/
    ├── __init__.py
    └── publicateur_mqtt.py
```

`capteur.py` définit la classe abstraite `Capteur`; `flotteur.py` contient le pilote `Flotteur` existant.
Les pilotes BH1750 et STEMMA existants sont conservés.
Les programmes se lancent avec `python -m` depuis la racine du dépôt.

## Lancement direct avec le flotteur

Depuis le dossier `raspberry_pi`, après activation du `.venv` :

```bash
python main.py
```

`config.py` définit le broker (`localhost:1883`), le GPIO BCM 16 et la période de lecture (600 secondes). La première lecture est immédiate. Le publicateur attend la confirmation MQTT avec QoS 1 et conserve l’horodatage d’acquisition. `Ctrl+C` signale l’arrêt, attend la fin du thread MQTT, puis libère les GPIO. Le flotteur et le feu sont activés; les autres capteurs et la pompe ne sont pas chargés.

## Démonstration EF12 — réservoir insuffisant et feu rouge

Démarrer le subscriber **avant** le collecteur pour recevoir la première mesure immédiate. Depuis la racine, dans le premier terminal :

```bash
source raspberry_pi/.venv/bin/activate
python -m raspberry_pi.ingestion.service_ingestion
```

Dans le second terminal, avec le flotteur et le feu branchés et vérifiés :

```bash
source raspberry_pi/.venv/bin/activate
cd raspberry_pi
python main.py
```

Le thread principal applique la décision du feu puis ajoute la mesure à la liste partagée. Le thread MQTT publie les acquisitions en attente toutes les 10 secondes. Montrer le flotteur dans la position correspondant à un réservoir insuffisant : contact fermé selon le code actuel. À l'acquisition, le feu doit passer au rouge et la mesure `insuffisant` doit être reçue et enregistrée. Pour montrer une autre position sans attendre les 10 minutes, arrêter proprement le collecteur avec `Ctrl+C`, changer la position et relancer : la première lecture est immédiate.

Avec de l'eau suffisante, le feu reste éteint : cela signifie que l'état global n'est pas déterminé. L'humidité et le cumul lumineux nécessaires au vert/jaune ne sont pas encore acquis. Ce scénario ne constitue donc pas l'implémentation complète d'EF10 à EF13. `Ctrl+C` arrête le thread, déconnecte MQTT, éteint le feu et libère ses GPIO et celui du flotteur. Aucun fallback matériel n'est ajouté à cette étape.

Vérification logicielle avec GPIO simulés, depuis la racine dans un environnement contenant `pytest` et `paho-mqtt` :

```bash
python -m pytest -q raspberry_pi/tests/test_feu_reservoir.py
```

La validation du rouge physique, de la polarité du flotteur et de la chaîne complète sur le Raspberry Pi reste à effectuer.

## Threads — même organisation que la démo de la prof

Le [main.py de la démo du cours](https://github.com/5P0-Integration-d-objets-connectes/demo-broker-thread/blob/main/main.py) sert de référence :

- Thread principal : acquisition réelle du flotteur toutes les 600 s et décision EF12 du feu.
- Thread séparé créé avec `threading.Thread(target=boucle_publication)` : publication des nouvelles acquisitions toutes les 10 s.
- `mesures_en_attente` : liste partagée, au lieu du compteur de quasi-collisions de la démo; chaque acquisition doit conserver son horodatage.
- `verrou = threading.Lock()` : protège l'ajout, la copie et le vidage de la liste. L'envoi MQTT se fait hors du verrou.
- `arret = threading.Event()` et `while not arret.wait(config.PERIODE_PUBLICATION)` : arrêt interrompable du thread MQTT.
- À l'arrêt : `arret.set()`, `thread_publication.join()`, déconnexion puis fermeture des composants. Le thread termine aussi l'envoi des mesures encore en attente.

Contrairement au compteur de la démo, aucune valeur n'est publiée lorsqu'il n'y a pas de nouvelle acquisition. Les deux périodes ont des rôles distincts : la publication toutes les 10 s ne provoque pas une lecture matérielle toutes les 10 s. Le principal utilise `arret.wait(600)` plutôt qu'un long `time.sleep(600)` afin de se réveiller si le thread MQTT signale une erreur. Une erreur de publication provoque l'arrêt; aucune file persistante ni reprise MQTT n'est ajoutée à cette étape. Le service d'ingestion doit être démarré avant le collecteur.

Cette vérification comporte 18 tests réussis, dont une exécution avec un vrai thread Python et des composants simulés. Le test confirme que la lecture reste dans le principal, que les mesures sont publiées par un autre thread et que les acquisitions en attente sont envoyées avant la déconnexion. Il ne valide pas le matériel ni la livraison MQTT sur le Pi.

## Autres formes de code alignées sur la démo

- `main.py` utilise `try/except KeyboardInterrupt/finally`, sans `ExitStack`. Les objets déjà créés sont fermés même si une initialisation ultérieure échoue. Des `finally` imbriqués garantissent l'extinction du feu même si la déconnexion MQTT échoue.
- Les paquets `capteurs` et `actionneurs` utilisent des imports explicites, sans `importlib` ni `__getattr__`. Les pilotes I²C n'ouvrent aucun bus lors de l'importation.
- Comme `CapteurVL53L1X` dans la démo, `CapteurLumiere` et `SoilSensor` héritent de `Capteur`, reçoivent un bus `i2c` dans leur constructeur et exposent `lire()`. Le bus appartient au programme qui le crée. Leurs périodes prévues sont respectivement 60 et 600 s; ces pilotes restent **non intégrés à main.py**. Le sol retourne une capacité brute, pas un pourcentage calibré.
- Le feu utilise `gpiozero.TrafficLights`, comme dans la démo, et libère les GPIO dans `fermer()`.
- L'ingestion déclare ses callbacks, utilise la configuration commune, puis démarre sous `if __name__ == "__main__"`; un import n'ouvre pas de connexion ni de fichier. Les JSON invalides sont ignorés et les erreurs d'écriture signalées.
- Le publicateur conserve ses vérifications de connexion et d'accusé QoS 1 existantes. L'horodatage reste celui de l'acquisition, sans le remplacer à l'envoi : c'est nécessaire pour la remise.

Les dépendances des pilotes I²C sont corrigées : `Adafruit-Blinka` fournit `board`/`busio`; `adafruit-circuitpython-seesaw` fournit `adafruit_seesaw`. Le paquet `board` homonyme et Pydantic ne sont pas nécessaires pour ces pilotes. Sur le Pi, réinstaller avec `python -m pip install -r raspberry_pi/requirements.txt` depuis la racine et garder le backend `lgpio` installé par apt. La calibration du sol, l'intégration des capteurs I²C, la pompe et les validations matérielles restent à faire.
