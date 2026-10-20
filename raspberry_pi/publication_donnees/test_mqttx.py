import json
import time

import paho.mqtt.client as mqtt

from datetime import datetime, timezone

import sys
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE_PROJET))

from capteurs.flotteur import Flotteur


BROKER = "mdbf12d4.ala.us-east-1.emqxsl.com"
PORT = 8883
USERNAME = "pub-pi"
PASSWORD = "12345"
TOPIC = "ferixu/eau"

flotteur = Flotteur()


def on_connect(client, userdata, flags, reason_code, properties):
    # Affiche "Success" ou la raison de l'échec
    print(f"Connexion : {reason_code}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="test-emqx")
client.on_connect = on_connect
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(ca_certs="emqxsl-ca.crt")
client.connect(BROKER, PORT, 60)
client.loop_start()

for i in range(5):
    payloadFlotteur = {
        "vide": not flotteur.eau,
        "horodatage": datetime.now(timezone.utc).isoformat(),
    }

    client.publish(
        TOPIC,
        json.dumps(payloadFlotteur)
    )

    print("Flotteur envoyé :", payloadFlotteur)

    time.sleep(2)

client.loop_stop()
client.disconnect()

