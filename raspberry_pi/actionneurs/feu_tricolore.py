"""Pilote du feu ARD-625 : sorties GPIO BCM, actives à l'état haut."""
from contextlib import ExitStack


class FeuTricolore:
    def __init__(self, pin_rouge, pin_jaune, pin_vert):
        from gpiozero import LED
        self._ressources = ExitStack()
        self._ferme = False
        try:
            self.del_rouge = LED(pin_rouge, initial_value=False)
            self._ressources.callback(self.del_rouge.close)
            self.del_jaune = LED(pin_jaune, initial_value=False)
            self._ressources.callback(self.del_jaune.close)
            self.del_verte = LED(pin_vert, initial_value=False)
            self._ressources.callback(self.del_verte.close)
        except Exception:
            self._ressources.close()
            raise

    def eteindre(self):
        """Éteint toutes les couleurs avant une transition."""
        self.del_rouge.off()
        self.del_jaune.off()
        self.del_verte.off()

    def allumer_rouge(self):
        """Active seulement le rouge."""
        self.eteindre()
        self.del_rouge.on()

    def allumer_jaune(self):
        """Active seulement le jaune."""
        self.eteindre()
        self.del_jaune.on()

    def allumer_vert(self):
        """Active seulement le vert."""
        self.eteindre()
        self.del_verte.on()

    def fermer(self):
        """Éteint le feu et libère les GPIO, même si une extinction échoue."""
        if self._ferme:
            return
        self._ferme = True
        try:
            self.eteindre()
        finally:
            self._ressources.close()
