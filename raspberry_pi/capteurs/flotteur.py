from gpiozero import Button, OutputDevice
from signal import pause


class Flotteur:
    def __init__(self, pin_flotteur=16):
        self.eau = False

        # Initialisation des composants matériels
        self.bouton = Button(pin_flotteur)

        # Liaison des événements aux méthodes de la classe
        self.bouton.when_pressed = self.lorsque_presse
        self.bouton.when_released = self.lorsque_relache

    def lorsque_presse(self):
        # quand ya pu deau
        self.eau = False

    def lorsque_relache(self):
        # quand ya du leau
        self.eau = True