from gpiozero import Button, OutputDevice
from signal import pause


class Flotteur:
    def __init__(self, pin_flotteur=16, pin_relais=17):
        # Initialisation des composants matériels
        self.bouton = Button(pin_flotteur, pull_up=True)
        self.relais = OutputDevice(pin_relais)

        # Liaison des événements aux méthodes de la classe
        self.bouton.when_pressed = self.lorsque_presse
        self.bouton.when_released = self.lorsque_relache

    def lorsque_presse(self):
        print("Flotteur activé -> Relais ALLUMÉ")
        self.relais.on()

    def lorsque_relache(self):
        print("Flotteur relâché -> Relais ÉTEINT")
        self.relais.off()


# --- Utilisation de la classe ---

# Instanciation de votre objet
#mon_systeme = Flotteur()
