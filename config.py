""" Ceci est le fichier de configuration centrale de l'application """
import os
from pathlib import Path

from dotenv import load_dotenv

RACINE = Path(__file__).resolve().parent
load_dotenv(RACINE / ".env")

def _lecture_env(nom:str) -> str:
    valeur = os.getenv(nom)
    if not valeur:
        raise RuntimeError(f"Variable d'environnement manquante : {nom}")

    return valeur

# ---- Lecture des variables d'environnement --- #
# ---- Broches GPIO (numérotation BCM) ---- #
GPIO_FEU_ROUGE = 23
GPIO_FEU_JAUNE = 22
GPIO_FEU_VERT = 27

# ---- Broker MQTT ---- #
MQTT_HOTE = _lecture_env("MQTT_HOTE")
MQTT_PORT = int(_lecture_env("MQTT_PORT"))
MQTT_UTILISATEUR = _lecture_env("MQTT_UTILISATEUR")
MQTT_MOT_DE_PASSE = _lecture_env("MQTT_MOT_DE_PASSE")

#TOPIC_QUASI_COLLISIONS = "demo/distance/collision"

PERIODE_LECTURE = 0.1
PERIODE_PUBLICATION = 10

# ---- Autre ---- #
#SEUIL_QUASI_COLLISION_CM = 10
