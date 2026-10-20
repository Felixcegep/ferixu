"""Abonnement et fichier JSONL, selon le service d'ingestion de la démo du cours."""
import json
import paho.mqtt.client as mqtt

from raspberry_pi import config

DOSSIER_DONNEES = config.RACINE / "donnees"
FICHIER_DONNEES = DOSSIER_DONNEES / "lectures_capteurs.jsonl"


def on_connect(client, userdata, flags, reason_code, properties):
    """Refait l'abonnement après chaque connexion au broker."""
    if reason_code.is_failure:
        print(f"Échec de connexion au broker : {reason_code}")
        return
    print("Connecté au broker MQTT")
    client.subscribe(config.TOPIC_EAU)
    client.subscribe(config.TOPIC_LUMIERE)


def on_message(client, userdata, msg):
    """Reçoit le JSON et conserve l'horodatage créé lors de l'acquisition."""
    try:
        mesure = json.loads(msg.payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        print("Message invalide ignoré.")
        return
    if not isinstance(mesure, dict) or not mesure.get("horodatage"):
        print("Mesure sans horodatage ignorée.")
        return
    print(mesure)
    try:
        with open(FICHIER_DONNEES, "a", encoding="utf-8") as fichier:
            fichier.write(json.dumps(mesure) + "\n")
    except OSError as erreur:
        print(f"Impossible d'enregistrer la mesure : {erreur}")


if __name__ == "__main__":
    # Même démarrage explicite et mêmes callbacks que dans la démo.
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id="ferixu-frontend-subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        DOSSIER_DONNEES.mkdir(exist_ok=True)
        client.connect(config.MQTT_HOTE, config.MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("Arrêt du service d'ingestion…")
    finally:
        client.disconnect()
