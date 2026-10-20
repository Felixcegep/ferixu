"""Commande du feu ARD-625 avec GPIO Zero, broches en numérotation BCM."""
from gpiozero import TrafficLights


class FeuCirculation:
    def __init__(self, pin_rouge, pin_jaune, pin_vert):
        """Réserve les GPIO à la création de l'instance, feu initialement éteint."""
        self._feu = TrafficLights(red=pin_rouge, amber=pin_jaune, green=pin_vert)

    def allumer_rouge(self):
        """Active le rouge seul; éteint le jaune et le vert."""
        self._feu.value = (1, 0, 0)

    def allumer_jaune(self):
        """Active le jaune seul."""
        self._feu.value = (0, 1, 0)

    def allumer_vert(self):
        """Active le vert seul."""
        self._feu.value = (0, 0, 1)

    def eteindre(self):
        """Éteint les trois couleurs."""
        self._feu.off()

    def fermer(self):
        """Éteint le feu puis libère les GPIO, même si l'extinction échoue."""
        try:
            self.eteindre()
        finally:
            self._feu.close()
