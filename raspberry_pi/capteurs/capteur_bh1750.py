"""Acquisition BH1750 en lux, une fois par minute (EF03)."""
from datetime import datetime, timezone
import math
from .capteur import Capteur


class CapteurLumiere(Capteur):
    def __init__(self, i2c, periode_lecture=60):
        import adafruit_bh1750
        super().__init__("luminosité", periode_lecture)
        self.capteur = adafruit_bh1750.BH1750(i2c)

    def lire(self):
        """Refuse une valeur invalide plutôt que de publier une mesure fictive."""
        horodatage = datetime.now(timezone.utc).isoformat()
        lux = float(self.capteur.lux)
        if not math.isfinite(lux) or not 0 <= lux <= 65535:
            raise ValueError("Luminosité invalide ou hors plage (lux).")
        return {"lux": lux, "horodatage": horodatage}
