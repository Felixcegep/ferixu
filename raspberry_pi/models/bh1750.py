#BH1750 (#4681)



import time

import adafruit_bh1750



SEUIL_LUMIERE_SUFFISANTE_LUX = 10_000
SEUIL_LUMIERE_TRES_FAIBLE_LUX = 100
INTERVALLE_SECONDES = 1


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
