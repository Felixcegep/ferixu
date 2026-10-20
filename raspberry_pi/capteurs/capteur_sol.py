"""Pilote STEMMA Soil Sensor selon la classe Capteur de la démo du cours."""
from datetime import datetime, timezone
import math

from .capteur import Capteur


class SoilSensor(Capteur):
    def __init__(self, i2c, periode_lecture=600):
        """Reçoit le bus du programme principal; couple sol toutes les 10 min."""
        from adafruit_seesaw.seesaw import Seesaw
        super().__init__("STEMMA sol", periode_lecture)
        self._capteur = Seesaw(i2c, addr=0x36)

    def lire(self) -> dict:
        """Acquiert température et capacité brute ensemble, sans inventer de %."""
        horodatage = datetime.now(timezone.utc).isoformat()
        temperature = float(self.get_temp())
        humidite_brute = float(self.get_moisture())
        if not math.isfinite(temperature) or not -40 <= temperature <= 85:
            raise ValueError("Température du sol invalide ou hors plage.")
        if not math.isfinite(humidite_brute) or not 0 <= humidite_brute <= 65535:
            raise ValueError("Humidité brute invalide ou hors plage.")
        return {"temperature_c": temperature, "humidite_brute": humidite_brute,
                "horodatage": horodatage}

    def get_temp(self):
        """Lit la température en °C, selon l'API du pilote Adafruit."""
        return self._capteur.get_temp()

    def get_moisture(self):
        """Lit une capacité brute; une calibration reste nécessaire pour EF01."""
        return self._capteur.moisture_read()
