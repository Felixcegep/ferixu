"""Démo du capteur BH1750 et des trois DEL sur Raspberry Pi.

Broches GPIO en mode BCM : rouge 27, jaune 22, vert 23.
Cette démo indique le niveau de luminosité instantané; elle ne calcule pas
la durée quotidienne de lumière et ne lit pas les autres capteurs du projet.
"""

import time

import adafruit_bh1750
import board
from gpiozero import LED


SEUIL_LUMIERE_SUFFISANTE_LUX = 10_000
SEUIL_LUMIERE_TRES_FAIBLE_LUX = 100
INTERVALLE_SECONDES = 1

del_rouge = LED(27)
del_jaune = LED(22)
del_verte = LED(23)
capteur = adafruit_bh1750.BH1750(board.I2C())


def afficher_niveau_lumiere(lux: float) -> None:
    """Allume une seule DEL selon la luminosité mesurée."""
    del_rouge.off()
    del_jaune.off()
    del_verte.off()

    if lux < SEUIL_LUMIERE_TRES_FAIBLE_LUX:
        del_rouge.on()
    elif lux >= SEUIL_LUMIERE_SUFFISANTE_LUX:
        del_verte.on()
    else:
        del_jaune.on()


try:
    while True:
        luminosite = capteur.lux
        print(f"{luminosite:.2f} lux", flush=True)
        afficher_niveau_lumiere(luminosite)
        time.sleep(INTERVALLE_SECONDES)
except KeyboardInterrupt:
    print("\nArrêt demandé.")
finally:
    del_rouge.off()
    del_jaune.off()
    del_verte.off()
    del_rouge.close()
    del_jaune.close()
    del_verte.close()
