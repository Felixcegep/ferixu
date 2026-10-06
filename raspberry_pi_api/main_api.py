import json
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
payload = {
    "lux": capteurLumiere.get_lux(),
    "horodatage": datetime.now(timezone.utc).isoformat(),
}
client.publish("projet/mesures", json.dumps(payload))
