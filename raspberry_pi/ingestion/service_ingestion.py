"""Abonnement MQTT et enregistrement des acquisitions en JSON Lines UTF-8."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

import paho.mqtt.client as mqtt
from raspberry_pi import config
from raspberry_pi.mesures import valider_mesure

TOPICS = (config.TOPIC_EAU, config.TOPIC_LUMIERE, config.TOPIC_SOL)


def on_connect(client, userdata, flags, reason_code, properties):
    """Refait les abonnements après chaque reconnexion."""
    if reason_code.is_failure:
        raise ConnectionError(f"Connexion refusée par le broker : {reason_code}")
    resultat, _ = client.subscribe([(topic, 1) for topic in TOPICS])
    if resultat != mqtt.MQTT_ERR_SUCCESS:
        raise ConnectionError(f"Échec de la demande d'abonnement : {resultat}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    """Annonce l'état prêt uniquement après la confirmation du broker."""
    if any(code.is_failure for code in reason_codes):
        raise ConnectionError("Abonnement refusé par le broker.")
    print("Ingestion prête : abonnements confirmés.", flush=True)


def enregistrer_mesure(topic, payload, fichier):
    """Valide puis conserve le payload et son horodatage, sans les remplacer."""
    mesure = json.loads(payload.decode("utf-8"))
    valider_mesure(topic, mesure)
    with Path(fichier).open("a", encoding="utf-8") as sortie:
        sortie.write(json.dumps(mesure, ensure_ascii=False, allow_nan=False) + "\n")
    return mesure


def on_message(client, userdata, msg):
    """Un mauvais message ne doit pas interrompre les acquisitions suivantes."""
    try:
        mesure = enregistrer_mesure(msg.topic, msg.payload, userdata)
    except (UnicodeError, ValueError, OSError) as erreur:
        print(f"Mesure non enregistrée sur {msg.topic} : {erreur}", file=sys.stderr, flush=True)
        return
    print(f"Enregistré sur {msg.topic} : {mesure}", flush=True)


def main():
    """Démarre explicitement le service; aucun réseau lors d'un import."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fichier", type=Path, default=config.FICHIER_DONNEES)
    args = parser.parse_args()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"ferixu-ingestion-{uuid4().hex[:12]}",
                         userdata=args.fichier)
    if config.MQTT_UTILISATEUR:
        client.username_pw_set(config.MQTT_UTILISATEUR, config.MQTT_MOT_DE_PASSE)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    try:
        args.fichier.parent.mkdir(parents=True, exist_ok=True)
        print(f"Fichier : {args.fichier.resolve()}", flush=True)
        client.connect(config.MQTT_HOTE, config.MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("Arrêt du service d'ingestion.")
    except (OSError, ValueError, RuntimeError) as erreur:
        print(f"Ingestion arrêtée : {erreur}", file=sys.stderr)
        return 1
    finally:
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
