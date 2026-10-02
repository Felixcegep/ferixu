# BH1750 (#4681)

import time
import board
import adafruit_bh1750
from pydantic import BaseModel, ConfigDict, Field


SEUIL_LUMIERE_SUFFISANTE_LUX = 10_000
SEUIL_LUMIERE_TRES_FAIBLE_LUX = 100
INTERVALLE_SECONDES = 1


class CapteurLumiere:
    capteur = adafruit_bh1750.BH1750(board.I2C())
    def get_lux(self):
        return self.capteur.lux
