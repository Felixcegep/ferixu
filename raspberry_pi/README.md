# Acquisition et démonstration Raspberry Pi — partie 1

## Objectif et état de l'implémentation

Le Raspberry Pi 4 surveille un basilic en pot. La chaîne de la démonstration est :
**flotteur réel → acquisition horodatée → publication → broker Mosquitto local → abonnement → fichier JSON Lines**.
La décision **réservoir insuffisant → feu rouge** est appliquée sur le Pi avant la publication, selon EF12.

| Objet / fonction | État logiciel |
| --- | --- |
| Flotteur | Lecture immédiate, puis toutes les 600 s, publication sur `ferixu/eau` |
| Feu ARD-625 | Rouge si le réservoir est insuffisant; éteint sinon; éteint et GPIO libérés à l'arrêt |
| BH1750 | Pilote et acquisition optionnelle réelle toutes les 60 s, topic `ferixu/lumiere` |
| STEMMA Soil Sensor | Pilote et acquisition optionnelle réelle du couple température/humidité toutes les 600 s, topic `ferixu/sol`; pourcentage seulement après calibration |
| Pompe / relais alternatif | Pilote sécurisé présent, non activé par le programme principal; broche et polarité à confirmer |
| NiceGUI | Maquette simulée, sans lien avec MQTT ou le matériel |

Le feu éteint signifie ici **état global non déterminé**, et non « tout va bien ». EF10 et EF11 exigent aussi l'humidité et les heures de lumière. Le cumul lumineux, l'historique, la décision complète du feu et l'arrosage automatique restent à intégrer. Le pilote de pompe seul n'implémente pas les limites automatiques de 30 minutes et de 6 arrosages par 24 heures.

Les [exigences corrigées EF01 à EF24](../documentation/exigences_fonctionnelles.md) et l'[inventaire](../documentation/inventaire_materiel.md) font référence. Les alternatives de flotteur, relais et capteur de sol doivent être identifiées avant leur utilisation. La référence du flotteur reste à confirmer (SENS-112-200 ou SENS-112-250). Les jumpers Dupont sont encore indiqués non reçus dans l'inventaire.

## Matériel et branchements à vérifier

**Aucun branchement physique n'a été validé par les tests logiciels.** Couper l'alimentation avant de modifier le montage. Le tableau décrit les broches attendues par le code, en numérotation BCM.

| Élément | BCM | Broche physique | Connexion attendue |
| --- | --- | --- | --- |
| Flotteur mécanique | 16 | 36 | Contact entre GPIO16 et GND, pull-up interne de `Button`; ne pas injecter de 5 V |
| Feu rouge | 23 | 16 | Signal de sortie, actif haut |
| Feu jaune | 22 | 15 | Signal de sortie, actif haut |
| Feu vert | 27 | 13 | Signal de sortie, actif haut |
| I²C SDA | 2 | 3 | BH1750 / STEMMA en parallèle sur le bus |
| I²C SCL | 3 | 5 | BH1750 / STEMMA en parallèle sur le bus |
| GND | — | 6, par exemple | Masse du montage |
| 3,3 V | — | 1, par exemple | Alimentation I²C seulement si compatible avec le module réel |

Avec le montage de flotteur attendu, contact **fermé = insuffisant**, ouvert = suffisant. Vérifier les deux positions physiques et l'orientation du flotteur. Ce circuit à deux fils ne distingue pas un fil débranché d'un contact ouvert : le vérifier avant toute future commande de pompe.

Pour le feu, confirmer les résistances intégrées et la compatibilité avec des sorties 3,3 V dans la fiche du module ARD-625. Son alimentation exacte et son câblage doivent être confirmés avec le module reçu, sans appliquer de 5 V à un GPIO. Corriger uniquement `raspberry_pi/config.py` si les signaux rouge/vert sont inversés sur le montage réel.

Le relais STEMMA se pilote en GPIO, pas en I²C. Le relais alternatif doit être identifié avant de choisir la broche et `active_high`. La pompe reçoit une alimentation séparée adaptée à sa tension, commutée par les contacts COM/NO du relais : **jamais d'alimentation moteur directement par un GPIO**. Aucun GPIO de pompe n'est attribué par défaut.

Pour I²C :

```bash
sudo raspi-config
# Interface Options → I2C → Enable; redémarrer si demandé.
i2cdetect -y 1
```

Vérifier les adresses avant le code Python : STEMMA `0x36`, BH1750 `0x23` par défaut. Une alternative peut demander une autre bibliothèque ou adresse; ne pas supposer sa compatibilité.

## Installation sur le Raspberry Pi

Depuis la racine du dépôt :

```bash
sudo apt update
sudo apt install -y python3-venv python3-gpiozero python3-lgpio i2c-tools mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
python3 -m venv --system-site-packages raspberry_pi/.venv
source raspberry_pi/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r raspberry_pi/requirements.txt
python -m pip check
```

`--system-site-packages` donne accès au backend GPIO `lgpio` installé par Raspberry Pi OS. Ne pas versionner le `.venv`; il doit être présent sur le Pi de démonstration. `Adafruit-Blinka` fournit les modules `board` et `busio`; ne pas installer le paquet homonyme `board`.

Si aucun `.env` n'existe, copier `.env.example` vers `.env`. S'il existe déjà, l'adapter sans écraser vos valeurs utiles :

```dotenv
MQTT_HOTE=localhost
MQTT_PORT=1883
MQTT_UTILISATEUR=
MQTT_MOT_DE_PASSE=
```

La configuration commune est `raspberry_pi/config.py`; elle seule lit le `.env` à la racine. `config.py` à la racine est un relais de compatibilité. Les deux clients utilisent les mêmes paramètres. Ce lancement vise le broker **local non chiffré**, pas un broker cloud TLS sur 8883. Chaque instance utilise un identifiant MQTT distinct. Les identifiants réels restent dans `.env`, ignoré par Git.

## Lancement : subscriber avant publicateur

Conserver deux terminaux SSH ouverts à la racine du dépôt.

**Terminal A — réception et fichier :**

```bash
source raspberry_pi/.venv/bin/activate
python -m raspberry_pi.ingestion.service_ingestion
```

Attendre **« Ingestion prête : abonnements confirmés. »** avant de lancer la collecte. Le subscriber demande QoS 1 sur les trois topics connus. Le fichier par défaut est `donnees/lectures_capteurs.jsonl` à la racine du dépôt, indépendamment du dossier courant. Pour choisir un fichier :

```bash
python -m raspberry_pi.ingestion.service_ingestion --fichier /tmp/ferixu-demo.jsonl
```

**Terminal B — flotteur et feu :**

```bash
source raspberry_pi/.venv/bin/activate
python -m raspberry_pi.main
```

La première lecture est immédiate; les suivantes ont lieu toutes les 10 minutes. Un ordonnancement monotone évite de faire dépendre les périodes du temps de publication. `Ctrl+C` arrête la collecte, éteint le feu, déconnecte MQTT et libère les GPIO. Une erreur de capteur est isolée : les autres acquisitions continuent. Une erreur MQTT arrête encore la collecte avec un message et le nettoyage des ressources; ce mécanisme de reprise concerne les composants matériels.

Variantes explicites :

```bash
# Diagnostic acquisition seulement : ne suffit pas pour démontrer un actionneur.
python -m raspberry_pi.main --sans-feu
# Une vraie lecture par capteur, puis libération des ressources.
python -m raspberry_pi.main --sans-feu --une-lecture
# Ajouter le BH1750 réel (60 s) et le sol réel (600 s).
python -m raspberry_pi.main --lumiere --sol
```

Ne pas lancer deux collecteurs sur les mêmes GPIO. Le lancement direct reste possible : depuis `raspberry_pi`, `python main.py`. Pour l'ingestion, utiliser la commande `python -m` depuis la racine.

## Payloads, horodatage et consultation

Chaque pilote crée l'horodatage **à l'acquisition**, en ISO 8601 avec fuseau UTC (`+00:00`). Le publicateur et le subscriber conservent cette chaîne. Le fichier est du JSON Lines UTF-8 : une mesure par ligne.

```json
{"etat": "insuffisant", "vide": true, "horodatage": "2026-10-20T14:30:00+00:00"}
```

```json
{"lux": 12345.0, "horodatage": "2026-10-20T14:30:00+00:00"}
```

```json
{"temperature_c": 22.5, "humidite_brute": 600.0, "humidite_pct": 50.0, "horodatage": "2026-10-20T14:30:00+00:00"}
```

Ces nombres sont des **exemples de format**, pas des mesures du montage. Sans calibration, `humidite_pct` est absent. Les champs distinguent les types de mesure dans le fichier commun. La période de sol inclut la lecture du réservoir, puisque les deux tâches démarrent ensemble et ont une période de 600 s.

```bash
mosquitto_sub -h localhost -p 1883 -t 'ferixu/#' -q 1 -v
tail -f donnees/lectures_capteurs.jsonl
```

Les messages invalides, non horodatés ou hors plage sont rejetés avec un message d'erreur; ils ne deviennent jamais des mesures valides. Une erreur d'écriture est signalée et l'ingestion reste active pour les messages suivants. **Il n'y a pas de file persistante de reprise après une erreur disque ou un subscriber arrêté.** QoS 1 ne garantit pas l'écriture sur disque et peut produire des doublons; comparer les messages et horodatages durant l'essai plutôt que supposer une livraison exactement une fois.

## Capteur absent : fonctionnement dégradé et reprise

Chaque capteur est initialisé à sa première acquisition, dans `CapteurSupervise`. Un module Python absent, un bus non accessible, un périphérique non détecté, une lecture invalide ou une erreur d'une bibliothèque matérielle est signalé dans le terminal comme **indisponible**. Les autres capteurs et MQTT continuent de fonctionner.

- Aucune valeur de remplacement n'est publiée : ni zéro, ni mesure simulée, ni ancienne mesure réhorodatée.
- Le pilote et son bus sont libérés après une erreur. Chaque pilote I²C possède son objet `busio.I2C`, pour que la libération de l'un ne ferme pas le bus de l'autre.
- Une nouvelle initialisation est tentée à la prochaine échéance normale : **60 s pour la luminosité, 600 s pour le sol et le réservoir**. Le retour d'une vraie mesure est annoncé dans le terminal. Redémarrer proprement le collecteur permet une nouvelle tentative immédiate.
- Si la lecture du réservoir échoue, le feu passe au rouge s'il est disponible. C'est une alerte de panne; elle ne fabrique pas une mesure « insuffisant ». Aucune activation de pompe n'est permise à partir d'un état inconnu.
- Un feu impossible à initialiser est désactivé pour cette exécution; un feu en erreur pendant une commande est fermé. La collecte continue, mais **la démonstration d'actionneur n'est alors pas satisfaite**. Corriger le problème et relancer pour le reprendre.
- `--une-lecture` effectue une seule tentative par capteur puis termine normalement, même si aucune mesure n'est disponible : consulter les messages du terminal et le fichier pour confirmer une acquisition réussie.

Cette reprise est un choix de robustesse du projet, pas une exigence additionnelle du cours. Elle traite les exceptions Python; elle ne peut pas rétablir une alimentation incorrecte, détecter tous les fils débranchés ou interrompre une bibliothèque qui se bloque indéfiniment. En particulier, le flotteur à contact ouvert reste électriquement indiscernable d'un fil débranché avec le câblage actuel. Une vraie détection de cette panne nécessite un circuit supervisé; ne pas l'interpréter comme une sécurité matérielle acquise.

## Calibration du sol

Suivre la méthode des notes de cours avec le capteur réellement utilisé : relever la valeur brute sèche et la valeur brute humide de référence, en respectant les limites d'immersion du fabricant (ne pas immerger l'électronique). Noter ces valeurs dans `.env` :

```dotenv
# Remplacer par VOS relevés, sans recopier une calibration d'exemple.
# SOL_BRUT_SEC=
# SOL_BRUT_HUMIDE=
```

La conversion est `100 × (brut - sec) / (humide - sec)`. Les deux références doivent être finies, et humide doit dépasser sec. Une lecture hors calibration est refusée au lieu d'être artificiellement ramenée à 0 ou 100 %. Sans calibration, le système publie la capacité brute et la température; **EF01 en pourcentage reste à valider** et aucune décision d'arrosage n'est prise à partir de cette valeur brute.

Les fréquences fonctionnelles restent 60 s (BH1750) et 600 s (sol et réservoir); elles n'ont pas été accélérées pour la démo. Avant de changer une fréquence ou d'utiliser un capteur alternatif, vérifier son intervalle minimal dans la documentation fabricant.

## Pompe : périmètre du pilote

`Pompe(pin_relais, flotteur, active_high=...)` exige un choix explicite de broche et de polarité. Le relais est inactif à la construction. `arroser(duree)` refuse toute durée hors de ]0, 3] secondes et tout état d'eau insuffisant ou invalide. Le niveau est lu immédiatement avant et après l'activation, et surveillé pendant celle-ci; le relais est coupé dans un `finally`. `fermer()` interrompt une activation et libère la broche. Ne pas connecter les boutons de la maquette à ce pilote sans une vraie logique de contrôle.

Le pilote n'est pas appelé par la démonstration. Le mode automatique, le délai de 30 minutes, le plafond de 6 activations sur 24 heures et leur historique restent à réaliser avant d'autoriser l'arrosage automatique.

## Répétition et présentation

Pendant la préparation (60 minutes maximum) :

1. Vérifier le montage, la référence des composants, les alimentations et l'interprétation du flotteur.
2. Ouvrir SSH et l'IDE distant; activer le `.venv` et vérifier les dépendances.
3. Vérifier Mosquitto, démarrer l'ingestion et attendre ses abonnements.
4. Démarrer la collecte avec le réservoir dans un état connu; montrer la vraie lecture, son horodatage et sa ligne JSONL.
5. Mettre le flotteur en position insuffisante et attendre la lecture suivante. Pour éviter les 10 minutes pendant la présentation, arrêter proprement puis relancer le collecteur : sa première lecture est immédiate. Montrer le rouge physique et la mesure correspondante. Ne pas changer la période pour cette raison.
6. Montrer aussi l'état suffisant et l'extinction, en expliquant que le vert complet n'est pas implémenté.
7. Comparer les publications, réceptions et lignes enregistrées, puis vérifier l'extinction à `Ctrl+C`.

Présentation (10 à 15 minutes) : montage 2 min; SSH/venv/dépendances 2 min; chaîne et feu 5 min; classes et séparation acquisition/décision/MQTT 2 à 3 min; questions 2 à 3 min. La démonstration proposée utilise un vrai flotteur et un vrai feu; si une condition doit être simulée en classe, nommer précisément cette simulation. Ne pas remplacer l'acquisition réelle par les tests logiciels.

## Tests logiciels

Dans un environnement de développement, sans dépendances GPIO :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r raspberry_pi/tests/requirements.txt
python -m pytest -q raspberry_pi/tests
```

Le test MQTT démarre un Mosquitto temporaire sur une adresse locale et un port libre; il ne modifie pas le service système. Il est ignoré si `mosquitto` n'est pas installé. Les autres tests simulent les GPIO et capteurs, vérifient les périodes, les valeurs invalides, la calibration, le feu et l'arrêt/refus de la pompe, ainsi que l'absence au démarrage, la déconnexion et la reprise d'un capteur.

Essai logiciel effectué le 20 octobre 2026 : 45 tests réussis, dont 14 mesures transmises via un vrai broker local et enregistrées sans perte observable, horodatages conservés; un JSON invalide rejeté sans interrompre le subscriber. **À valider sur le Pi : installation matérielle des dépendances, backend GPIO, polarités, I²C, calibration et chaîne complète avec composants physiques.**

## Sources consultées

- [Cours — MQTT : broker local, Paho, callbacks et ingestion](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/transmission-de-donnees/mqtt)
- [Cours — GPIO, I²C, capteurs, relais et calibration](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/iot/connexion-et-utilisation-des-capteurs-et-actionneurs)
- [Cours — threads, Event et arrêt propre](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/iot/exemple-utilisationn-threads)
- [Cours — .env et configuration commune](https://cours-5.gitbook.io/420-5p0-integration-dobjets-connectes/iot/fichier-.env-et-configuration)
- [Fabricant — STEMMA Soil Sensor Python](https://learn.adafruit.com/adafruit-stemma-soil-sensor-i2c-capacitive-moisture-sensor/python-circuitpython-test)

La validation stricte des payloads, les tests automatisés et l'ordonnanceur monotone sont des choix de robustesse du projet; ils ne sont pas présentés comme des conventions imposées par le cours.
