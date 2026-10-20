"""Décisions de la démonstration, indépendantes des pilotes et de MQTT."""


def mettre_a_jour_feu_reservoir(feu, mesure):
    """EF12 : eau insuffisante → rouge. Les autres mesures restent inconnues.

    Sans humidité ni cumul lumineux, EF10/EF11 ne permettent pas de déduire
    une couleur verte ou jaune. Le feu est donc éteint si l'eau est suffisante.
    """
    if mesure["etat"] == "insuffisant":
        feu.allumer_rouge()
    elif mesure["etat"] == "suffisant":
        feu.eteindre()
    else:
        raise ValueError("État du réservoir inconnu.")
