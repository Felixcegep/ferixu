"""Pilote BH1750 structuré comme le CapteurVL53L1X de la démo du cours."""
from datetime import datetime, timezone
import math

from .capteur import Capteur


class CapteurLumiere(Capteur):
    def __init__(self, i2c, periode_lecture=60):
        """Reçoit le bus du programme principal; période prévue par EF03 : 60 s."""
        import adafruit_bh1750
        super().__init__("BH1750", periode_lecture)
        self._capteur = adafruit_bh1750.BH1750(i2c)

    def lire(self) -> dict:
        """Lit la luminosité en lux et horodate l'acquisition en UTC."""
        horodatage = datetime.now(timezone.utc).isoformat()
        lux = float(self._capteur.lux)
        if not math.isfinite(lux) or lux < 0:
            raise ValueError("Luminosité invalide.")
        return {"lux": lux, "horodatage": horodatage}

    def get_lux(self):
        """Conserve l'accès ponctuel du pilote existant."""
        return self.lire()["lux"]
