"""STEMMA Soil Sensor : température et capacité brute acquises ensemble."""
from datetime import datetime, timezone
import math
from .capteur import Capteur


class CapteurSol(Capteur):
    def __init__(self, i2c, brut_sec=None, brut_humide=None, periode_lecture=600):
        super().__init__("sol", periode_lecture)
        if (brut_sec is None) != (brut_humide is None):
            raise ValueError("Fournir les deux valeurs de calibration, ou aucune.")
        self.brut_sec = float(brut_sec) if brut_sec is not None else None
        self.brut_humide = float(brut_humide) if brut_humide is not None else None
        if self.brut_sec is not None and (
            not math.isfinite(self.brut_sec) or not math.isfinite(self.brut_humide)
            or self.brut_humide <= self.brut_sec
        ):
            raise ValueError("Calibration invalide : humide doit être supérieur à sec.")
        from adafruit_seesaw.seesaw import Seesaw
        self.capteur = Seesaw(i2c, addr=0x36)

    def lire(self):
        """Horodate le couple; le % est absent tant que la sonde n'est pas calibrée."""
        horodatage = datetime.now(timezone.utc).isoformat()
        temperature = float(self.capteur.get_temp())
        brut = float(self.capteur.moisture_read())
        if not math.isfinite(temperature) or not -40 <= temperature <= 85:
            raise ValueError("Température invalide ou hors plage (°C).")
        if not math.isfinite(brut) or not 0 <= brut <= 65535:
            raise ValueError("Humidité brute invalide ou hors plage.")
        mesure = {"temperature_c": temperature, "humidite_brute": brut,
                  "horodatage": horodatage}
        if self.brut_sec is not None:
            pourcentage = 100 * (brut - self.brut_sec) / (self.brut_humide - self.brut_sec)
            # Une mesure hors calibration n'est pas ramenée artificiellement à 0 ou 100.
            if not 0 <= pourcentage <= 100:
                raise ValueError("Humidité hors de l'intervalle de calibration.")
            mesure["humidite_pct"] = pourcentage
        return mesure
