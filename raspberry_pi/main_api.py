import json
import time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

from capteurs.Bh1750 import CapteurLumiere




capteurLumiere = CapteurLumiere()

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                     client_id="capteur-bh1750-001-publicateur")
# broker, port, keepalive (s)
client.connect("localhost", 1883, 60)
# boucle réseau en arrière-plan (garde en vie la connexion avec le broker)
client.loop_start()
try:
    while True:
        payload = {
            "lux": capteurLumiere.get_lux(),
            "horodatage": datetime.now(timezone.utc).isoformat(),
        }
        client.publish("ferixu/lux", json.dumps(payload))
        time.sleep(5)
except KeyboardInterrupt:
    print("Arrêt du capteur.")
finally:
    client.loop_stop()
    client.disconnect()
