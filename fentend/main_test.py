import json
from pathlib import Path

import paho.mqtt.client as mqtt
from uvicorn.loops.asyncio import asyncio_loop_factory

Path("donnees").mkdir(exist_ok=True)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Échec de connexion au broker : {reason_code}")
        return
    print("Connecté au broker MQTT")
    # Abonnement ici : il est refait automatiquement après une reconnexion
    client.subscribe("ferixu/lux")
    client.subscribe("ferixu/eau")


def on_message(client, userdata, msg):
    
    mesure = json.loads(msg.payload.decode("utf-8"))
    print(mesure)
    # JSON Lines : une mesure par ligne, ajoutée à la fin du fichier
    with open("donnees/lectures_capteurs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(mesure) + "\n")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                     client_id="ferixu-frontend-subscriber")

client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
# bloque et attend les messages
client.loop_forever()
