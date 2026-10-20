"""Configuration du Pi : seul module lisant le .env, broches en BCM."""
import os
from pathlib import Path
from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parents[1]
load_dotenv(RACINE / ".env")
MQTT_HOTE = os.getenv("MQTT_HOTE", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_UTILISATEUR = os.getenv("MQTT_UTILISATEUR", "")
MQTT_MOT_DE_PASSE = os.getenv("MQTT_MOT_DE_PASSE", "")
MQTT_DELAI_SECONDES = 10
TOPIC_EAU = "ferixu/eau"
TOPIC_LUMIERE = "ferixu/lumiere"
TOPIC_SOL = "ferixu/sol"
FICHIER_DONNEES = RACINE / "donnees" / "lectures_capteurs.jsonl"
GPIO_FLOTTEUR = 16
# Broches conservées du pilote existant : à confirmer sur le montage.
GPIO_FEU_ROUGE = 23
GPIO_FEU_JAUNE = 22
GPIO_FEU_VERT = 27
PERIODE_LECTURE_RESERVOIR = 600
PERIODE_LECTURE_SOL = 600
PERIODE_LECTURE_LUMIERE = 60
SEUIL_LUMIERE_SUFFISANTE_LUX = 10_000
# Ne jamais inventer les valeurs de calibration du capteur alternatif.
SOL_BRUT_SEC = os.getenv("SOL_BRUT_SEC")
SOL_BRUT_HUMIDE = os.getenv("SOL_BRUT_HUMIDE")
