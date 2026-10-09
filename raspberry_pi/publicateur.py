import json
import asyncio
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from capteurs.Flotteur import Flotteur
# from capteurs.Bh1750 import CapteurLumiere


async def flotteurSender(flotteur, client, sleeptime=5):
    while True:
        payloadFlotteur = {
            "vide": not flotteur.eau,
            "horodatage": datetime.now(timezone.utc).isoformat(),
        }

        client.publish(
            "ferixu/eau",
            json.dumps(payloadFlotteur)
        )

        print("Flotteur envoyé :", payloadFlotteur)

        await asyncio.sleep(sleeptime)


async def lumiereSender(capteur, client, sleeptime=5):
    while True:
        payloadLux = {
            "lux": capteur.get_lux(),
            "horodatage": datetime.now(timezone.utc).isoformat(),
        }

        client.publish(
            "ferixu/lux",
            json.dumps(payloadLux)
        )

        print("Lux envoyé :", payloadLux)

        await asyncio.sleep(sleeptime)


async def main():

    capteurFlotteur = Flotteur()
    # capteurLumiere = CapteurLumiere()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="ferixu-capteurs"
    )

    client.connect("localhost", 1883, 60)
    client.loop_start()

    try:
        await asyncio.gather(
            flotteurSender(capteurFlotteur, client, 5),
            # lumiereSender(capteurLumiere, client, 10)
        )

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())