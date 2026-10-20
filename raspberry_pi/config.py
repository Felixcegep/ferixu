"""Configuration centrale du Raspberry Pi, broches en numérotation BCM."""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

MQTT_HOTE = "localhost"
MQTT_PORT = 1883
MQTT_DELAI_SECONDES = 10
TOPIC_EAU = "ferixu/eau"
TOPIC_LUMIERE = "ferixu/lumiere"
GPIO_FLOTTEUR = 16
# Même attribution que le config.py racine; à confirmer sur le montage réel.
GPIO_FEU_ROUGE = 23
GPIO_FEU_JAUNE = 22
GPIO_FEU_VERT = 27
# EF05 prévoit 600 s; la valeur locale de 5 s est conservée pour les essais.
PERIODE_LECTURE_RESERVOIR = 5

# Période du thread MQTT (indépendante des périodes de lecture).
PERIODE_PUBLICATION = 5

# EF03 : lecture de la luminosité toutes les minutes.
PERIODE_LECTURE_LUMIERE = 60
