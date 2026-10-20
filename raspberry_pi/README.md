# Programmes Raspberry Pi : publicateur et subscriber

Ce dossier contient deux programmes à lancer ensemble dans des terminaux distincts :

| Programme | Rôle |
| --- | --- |
| [publicateur_mqtt.py](publication_donnees/publicateur_mqtt.py) | Classe `PublicateurMQTT` appelée par `main.py` pour publier les acquisitions en attente du flotteur (`ferixu/eau`) et du BH1750 (`ferixu/lumiere`) |
| [service_ingestion.py](ingestion/service_ingestion.py) | Recevoir les messages de `ferixu/eau` et `ferixu/lumiere`, les afficher et les enregistrer en JSON Lines |

Le trajet des données est : **flotteur / BH1750 → publicateur → broker MQTT local → subscriber → fichier JSON Lines**. Les deux scripts se connectent à `localhost:1883`; les instructions ci-dessous les exécutent donc sur le même Raspberry Pi. La première acquisition est immédiate; le thread MQTT la publie à sa prochaine échéance, au plus environ une période de publication plus tard si le broker répond normalement.

Le flotteur et le BH1750 sont les capteurs utilisés par `main.py`. Le feu ARD-625 est commandé à chaque lecture : rouge si le réservoir est insuffisant, éteint sinon. Le BH1750 est lu toutes les 60 s. Seul le STEMMA Soil Sensor reste hors du programme actif. La pompe et sa logique de déclenchement ne sont pas implémentées. La maquette de l’interface est simulée et n’est pas reliée à ces messages.

## Matériel et branchements

Pour la collecte active :

- Raspberry Pi avec Raspberry Pi OS;
- interrupteur à flotteur branché au GPIO BCM 16 (broche physique 36);
- feu ARD-625 : rouge BCM 23 (physique 16), jaune BCM 22 (physique 15), vert BCM 27 (physique 13).

Les broches du feu sont définies dans `raspberry_pi/config.py`, avec la même attribution que le `config.py` racine. Elles doivent être confirmées sur le montage réel. Vérifier la masse commune, les résistances et la compatibilité des entrées du module avec les sorties GPIO 3,3 V; l'alimentation exacte doit être vérifiée dans la fiche du module reçu. Ne pas appliquer de 5 V à un GPIO. Aucun branchement n'est validé par les tests logiciels.

Dans `capteurs/flotteur.py`, l’état pressé signifie que le réservoir est vide et l’état relâché signifie qu’il contient de l’eau. Vérifiez que le montage physique correspond à cette interprétation.

Le BH1750 prévu se branche sur I²C : SDA au GPIO 2 (broche physique 3), SCL au GPIO 3 (broche physique 5) et GND à GND. Il est lu par le programme actif. Avant de lancer, activez I²C avec `sudo raspi-config` (**Interface Options → I2C → Enable**) et vérifiez le bus avec `i2cdetect -y 1`.

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

Le subscriber écoute `ferixu/eau` et `ferixu/lumiere`, affiche les messages reçus et les ajoute à `donnees/lectures_capteurs.jsonl` avec les commandes ci-dessus. Le chemin est fixé à la racine du dépôt avec `config.RACINE`, comme dans la démo de la prof. Le dossier est créé au démarrage et le fichier à la réception du premier message; chaque mesure occupe une ligne. Appuyez sur `Ctrl+C` dans chaque terminal pour arrêter les programmes.

Pour observer les messages MQTT sans les enregistrer, utilisez un autre terminal :

```bash
mosquitto_sub -h localhost -t 'ferixu/#' -v
```

## Fonctions prévues

Les exigences complètes sont dans [../EXIGENCES.md](../EXIGENCES.md). Les mesures d’humidité et de température, le cumul des heures de lumière, la logique complète du feu (EF10 à EF13) et la commande sécurisée de la pompe restent à intégrer au programme actif.

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
Le BH1750 est intégré; le pilote STEMMA reste hors du programme actif.
Les programmes se lancent avec `python -m` depuis la racine du dépôt.

## Lancement direct avec le flotteur

Depuis le dossier `raspberry_pi`, après activation du `.venv` :

```bash
python main.py
```

`config.py` définit le broker (`localhost:1883`), le GPIO BCM 16 et les périodes de lecture (600 s prévues pour le réservoir, 60 s pour la lumière; la valeur locale du réservoir est actuellement de 5 s pour les essais). La première lecture est immédiate. Le publicateur attend la confirmation MQTT avec QoS 1 et conserve l’horodatage d’acquisition. `Ctrl+C` signale l’arrêt, attend la fin du thread MQTT, puis libère les GPIO. Le flotteur, le BH1750 et le feu sont activés; le sol et la pompe ne sont pas chargés.

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

Le thread principal applique la décision du feu puis ajoute la mesure à la liste partagée. Le thread MQTT publie les acquisitions en attente à la période configurée (actuellement 5 s pour les essais). Montrer le flotteur dans la position correspondant à un réservoir insuffisant : contact fermé selon le code actuel. À l'acquisition, le feu doit passer au rouge et la mesure `insuffisant` doit être reçue et enregistrée. Pour montrer une autre position sans attendre les 10 minutes, arrêter proprement le collecteur avec `Ctrl+C`, changer la position et relancer : la première lecture est immédiate.

Avec de l'eau suffisante, le feu reste éteint : cela signifie que l'état global n'est pas déterminé. L'humidité et le cumul lumineux nécessaires au vert/jaune ne sont pas encore acquis. Ce scénario ne constitue donc pas l'implémentation complète d'EF10 à EF13. `Ctrl+C` arrête le thread, déconnecte MQTT, éteint le feu et libère ses GPIO et celui du flotteur. Les erreurs du BH1750 sont signalées et sa lecture retentée après 60 s, sans fausse mesure. Le flotteur et le feu conservent leur fonctionnement précédent.

Vérification logicielle avec GPIO simulés, depuis la racine dans un environnement contenant `pytest` et `paho-mqtt` :

```bash
python -m pytest -q raspberry_pi/tests/test_feu_reservoir.py
```

La validation du rouge physique, de la polarité du flotteur et de la chaîne complète sur le Raspberry Pi reste à effectuer.

## Threads — même organisation que la démo de la prof

Le [main.py de la démo du cours](https://github.com/5P0-Integration-d-objets-connectes/demo-broker-thread/blob/main/main.py) sert de référence :

- Thread principal : lecture indépendante du flotteur (600 s prévues par EF05, valeur locale d’essai 5 s), décision EF12 et lecture du BH1750 toutes les 60 s.
- Thread séparé créé avec `threading.Thread(target=boucle_publication)` : publication des nouvelles acquisitions à `config.PERIODE_PUBLICATION` (valeur locale d’essai 5 s).
- `mesures_en_attente` : liste partagée de couples `(topic, mesure)`, au lieu du compteur de quasi-collisions de la démo; chaque acquisition doit conserver son horodatage.
- `verrou = threading.Lock()` : protège l'ajout, la copie et le vidage de la liste. L'envoi MQTT se fait hors du verrou.
- `arret = threading.Event()` et `while not arret.wait(config.PERIODE_PUBLICATION)` : arrêt interrompable du thread MQTT.
- À l'arrêt : `arret.set()`, `thread_publication.join()`, déconnexion puis fermeture des composants. Le thread termine aussi l'envoi des mesures encore en attente.

Contrairement au compteur de la démo, aucune valeur n'est publiée lorsqu'il n'y a pas de nouvelle acquisition. Les périodes de lecture et de publication sont distinctes. Le principal calcule la prochaine échéance de chaque capteur avec `time.monotonic()` et attend la plus proche avec `arret.wait(...)`; le thread MQTT reste indépendant. L’attente est interrompue si le thread MQTT demande l’arrêt. Une erreur de publication provoque l'arrêt; aucune file persistante ni reprise MQTT n'est ajoutée à cette étape. Le service d'ingestion doit être démarré avant le collecteur.

Cette vérification comporte 24 tests réussis, dont une exécution avec un vrai thread Python et des composants simulés. Le test confirme que la lecture reste dans le principal, que les mesures sont publiées par un autre thread et que les acquisitions en attente sont envoyées avant la déconnexion. Il ne valide pas le matériel ni la livraison MQTT sur le Pi.

## Autres formes de code alignées sur la démo

- `main.py` utilise `try/except KeyboardInterrupt/finally`, sans `ExitStack`. Les objets déjà créés sont fermés même si une initialisation ultérieure échoue. Des `finally` imbriqués garantissent l'extinction du feu même si la déconnexion MQTT échoue.
- Les paquets `capteurs` et `actionneurs` utilisent des imports explicites, sans `importlib` ni `__getattr__`. Les pilotes I²C n'ouvrent aucun bus lors de l'importation.
- Comme `CapteurVL53L1X` dans la démo, `CapteurLumiere` et `SoilSensor` héritent de `Capteur`, reçoivent un bus `i2c` dans leur constructeur et exposent `lire()`. Le bus appartient au programme qui le crée. Leurs périodes prévues sont respectivement 60 et 600 s; le BH1750 est intégré à `main.py`, tandis que le sol reste hors de la collecte. Le sol retourne une capacité brute, pas un pourcentage calibré.
- Le feu utilise `gpiozero.TrafficLights`, comme dans la démo, et libère les GPIO dans `fermer()`.
- L'ingestion déclare ses callbacks, utilise la configuration commune, puis démarre sous `if __name__ == "__main__"`; un import n'ouvre pas de connexion ni de fichier. Les JSON invalides sont ignorés et les erreurs d'écriture signalées.
- Le publicateur conserve ses vérifications de connexion et d'accusé QoS 1 existantes. L'horodatage reste celui de l'acquisition, sans le remplacer à l'envoi : c'est nécessaire pour la remise.

Les dépendances des pilotes I²C sont corrigées : `Adafruit-Blinka` fournit `board`/`busio`; `adafruit-circuitpython-seesaw` fournit `adafruit_seesaw`. Le paquet `board` homonyme et Pydantic ne sont pas nécessaires pour ces pilotes. Sur le Pi, réinstaller avec `python -m pip install -r raspberry_pi/requirements.txt` depuis la racine et garder le backend `lgpio` installé par apt. La calibration du sol, l'intégration du sol, la pompe et les validations matérielles restent à faire.

## BH1750 — lecture réelle et MQTT

Le BH1750 (#4681) est indiqué **reçu** dans l'inventaire; son fonctionnement matériel reste à vérifier sur le Raspberry Pi 4. Le programme utilise le bus I²C créé avec `board.I2C()`, comme dans la démo de la prof. Avant de lancer, vérifier qu'aucune autre instance de collecte n'utilise les GPIO et confirmer les branchements :

| BH1750 Adafruit | Raspberry Pi, BCM | Broche physique |
| --- | --- | --- |
| VIN | 3,3 V | 1 |
| GND | GND | 6 |
| SDA | GPIO 2 | 3 |
| SCL | GPIO 3 | 5 |

Ce tableau vise le module Adafruit déclaré dans l'inventaire : confirmer la fiche du module réel, sans appliquer du 5 V sur un GPIO. Activer I²C avec `sudo raspi-config` (Interface Options → I2C), redémarrer si demandé, puis vérifier :

```bash
i2cdetect -y 1
```

L'adresse par défaut attendue est `23` (`0x23`). Si elle manque, vérifier alimentation, masse, câblage et bus avant de diagnostiquer Python. Le constructeur utilise cette adresse par défaut; un module configuré à une autre adresse nécessite une adaptation explicite.

Après activation du `.venv`, les dépendances sont déjà listées dans `raspberry_pi/requirements.txt` :

```bash
python -m pip install -r raspberry_pi/requirements.txt
```

La commande de collecte reste `cd raspberry_pi` puis `python main.py`; aucune option supplémentaire n'est nécessaire. Le subscriber doit être lancé avant le collecteur. Pour observer uniquement le BH1750 :

```bash
mosquitto_sub -h localhost -p 1883 -t 'ferixu/lumiere' -v
```

Exemple de payload, conservé tel quel dans le fichier JSONL commun :

```json
{"lux": 12345.0, "horodatage": "2026-10-20T14:00:00+00:00"}
```

Il s'agit d'un exemple de format, pas d'une mesure réelle du montage. La première acquisition est immédiate, les suivantes toutes les **60 s (EF03)**. Le thread MQTT envoie les mesures à sa prochaine échéance, sans republier les anciennes et sans changer leur horodatage. Les messages d'eau et de lumière restent distincts, avec leur propre topic.

Si le capteur, son bus ou sa bibliothèque n'est pas disponible, un message `BH1750 indisponible` est affiché et l'acquisition est retentée à l'échéance suivante, après 60 s. Une lecture invalide n'est pas remplacée par zéro lux. Le flotteur et son feu continuent. À l'arrêt, le thread est joint et le bus I²C est libéré dans `finally`.

Le feu ne change pas selon un relevé lumineux instantané : les exigences utilisent des **heures cumulées**. Le cumul au seuil de 10 000 lux (EF04), l'historique des 7 jours et la logique complète EF10 à EF13 restent à réaliser.

**Attention aux valeurs locales d'essai conservées :** `PERIODE_LECTURE_RESERVOIR = 5` et `PERIODE_PUBLICATION = 5`. EF05 exige normalement 600 s pour le réservoir; rétablir cette valeur pour un fonctionnement conforme. `PERIODE_LECTURE_LUMIERE = 60` respecte EF03 et n'est pas raccourcie pour la démo.

Vérifications logicielles : 24 tests réussis, avec périodes de 60/600 s simulées, routage vers les deux topics, conservation des horodatages, absence/reconnexion du BH1750 et exécution dans un vrai thread Python avec composants simulés. Ces tests ne valident pas les branchements ni la livraison MQTT sur le Pi.

Références consultées : [démo de la prof](https://github.com/5P0-Integration-d-objets-connectes/demo-broker-thread), [notes sur les threads](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/iot/exemple-utilisationn-threads), [branchement BH1750 Adafruit](https://learn.adafruit.com/adafruit-bh1750-ambient-light-sensor/python-circuitpython) et [pilote officiel](https://github.com/adafruit/Adafruit_CircuitPython_BH1750/blob/main/adafruit_bh1750.py). Le pilote indique une conversion de 180 ms, bien inférieure à la période fonctionnelle de 60 s.
