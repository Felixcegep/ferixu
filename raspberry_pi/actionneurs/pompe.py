"""Commande d'un relais confirmé : jamais d'alimentation moteur par le GPIO.

Pilote disponible pour intégration ultérieure; non activé par main.py.
La polarité et la broche du relais alternatif doivent être confirmées.
"""
import math
import threading
import time


class Pompe:
    def __init__(self, pin_relais, flotteur, *, active_high):
        if not isinstance(active_high, bool):
            raise ValueError("La polarité du relais doit être un booléen confirmé.")
        from gpiozero import OutputDevice
        self.flotteur = flotteur
        self._verrou = threading.Lock()
        self._arret = threading.Event()
        self.relais = OutputDevice(pin_relais, active_high=active_high, initial_value=False)

    def arroser(self, duree=3):
        """Refuse sans eau, surveille le niveau et garantit l'arrêt après ≤ 3 s.

        La limite conservatrice vaut aussi pour les tests. Les limites du mode
        automatique (EF08/09) restent à intégrer dans un contrôleur distinct.
        """
        if (isinstance(duree, bool) or not isinstance(duree, (int, float))
                or not math.isfinite(duree) or not 0 < duree <= 3):
            raise ValueError("La durée doit être supérieure à 0 et au plus 3 secondes.")
        if not self._verrou.acquire(blocking=False):
            raise RuntimeError("Un arrosage est déjà en cours.")
        try:
            if self._arret.is_set():
                raise RuntimeError("La pompe est arrêtée définitivement.")
            avant = self.flotteur.lire()
            if avant.get("etat") != "suffisant" or avant.get("vide") is not False:
                raise RuntimeError("Arrosage refusé : eau insuffisante ou état invalide.")
            try:
                fin = time.monotonic() + duree
                self.relais.on()
                while not self._arret.is_set():
                    restant = fin - time.monotonic()
                    if restant <= 0:
                        break
                    if not self.flotteur.eau:
                        raise RuntimeError("Arrosage interrompu : réservoir insuffisant.")
                    self._arret.wait(min(0.1, restant))
            finally:
                # EF05 : relire aussi après une activation interrompue.
                self.relais.off()
                apres = self.flotteur.lire()
            return {"avant": avant, "apres": apres}
        finally:
            self._verrou.release()

    def fermer(self):
        """Interrompt l'activation et attend sa fin avant de libérer le GPIO."""
        self._arret.set()
        with self._verrou:
            try:
                self.relais.off()
            finally:
                self.relais.close()
