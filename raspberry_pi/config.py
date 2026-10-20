"""Configuration centrale du Raspberry Pi, broches en numérotation BCM."""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

MQTT_HOTE = "localhost"
MQTT_PORT = 1883
MQTT_DELAI_SECONDES = 10
TOPIC_EAU = "ferixu/eau"
GPIO_FLOTTEUR = 16
# Même attribution que le config.py racine; à confirmer sur le montage réel.
GPIO_FEU_ROUGE = 23
GPIO_FEU_JAUNE = 22
GPIO_FEU_VERT = 27
# EF05 : vérification périodique du réservoir toutes les 10 minutes.
PERIODE_LECTURE_RESERVOIR = 600

# Le thread MQTT envoie les nouvelles acquisitions au plus toutes les 10 s.
PERIODE_PUBLICATION = 10
