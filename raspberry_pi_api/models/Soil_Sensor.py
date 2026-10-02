#STEMMA Soil Sensor (#4026)

import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw

# Initialisation du bus I2C
i2c_bus = busio.I2C(board.SCL, board.SDA)

# Instanciation du capteur (adresse I2C par défaut : 0x36)
ss = Seesaw(i2c_bus, addr=0x36)

print("Lecture du capteur d'humidité STEMMA Soil Sensor...")

while True:
    # Lecture de l'humidité (valeur capacitive typique dans le sol : 300 à 500)
    touch_value = ss.moisture_read()

    # Lecture de la température en degrés Celsius
    temp_c = ss.get_temp()

    print(f"Humidité (capacitance) : {touch_value} | Température : {temp_c:.2f} °C")

    time.sleep(2)