"""Configuration centrale du Raspberry Pi, broches en numérotation BCM."""

MQTT_HOTE = "localhost"
MQTT_PORT = 1883
MQTT_DELAI_SECONDES = 10
TOPIC_EAU = "ferixu/eau"
GPIO_FLOTTEUR = 16
# EF05 : vérification périodique du réservoir toutes les 10 minutes.
PERIODE_LECTURE_RESERVOIR = 600
