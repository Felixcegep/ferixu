#STEMMA Soil Sensor (#4026)

import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw
from pydantic import BaseModel

# Create I2C bus
i2c_bus = busio.I2C(board.SCL, board.SDA)



class SoilSensor(BaseModel):
    ss = Seesaw(i2c_bus, addr=0x36)


    def get_temp(self):
        return self.ss.get_temp()
    def get_moisture(self):
        return self.ss.moisture_read()

