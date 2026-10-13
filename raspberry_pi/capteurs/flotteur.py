"""Lecture du flotteur : contact fermé = niveau insuffisant, à valider sur le Pi."""

from datetime import datetime, timezone

from gpiozero import Button

from .capteur import Capteur


class Flotteur(Capteur):
    def __init__(self, pin_flotteur=16, periode_lecture=600):
        super().__init__("réservoir", periode_lecture)
        self.bouton = Button(pin_flotteur)

    @property
    def eau(self):
        """Lit l'état réel du contact, même avant le premier changement GPIO."""
        return not self.bouton.is_pressed

    def lire(self) -> dict:
        """Horodate l'état du réservoir à l'acquisition, en ISO 8601 UTC."""
        eau = self.eau
        return {
            "etat": "suffisant" if eau else "insuffisant",
            "vide": not eau,
            "horodatage": datetime.now(timezone.utc).isoformat(),
        }

    def fermer(self) -> None:
        """Libère la broche GPIO du flotteur."""
        self.bouton.close()
