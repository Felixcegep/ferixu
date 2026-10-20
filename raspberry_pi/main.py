"""Flotteur, BH1750 et feu dans le thread principal; publication MQTT séparée.

Structure adaptée de la démo de la prof :
https://github.com/5P0-Integration-d-objets-connectes/demo-broker-thread/blob/main/main.py
"""
import threading
import time

import config
from capteurs import Flotteur, CapteurLumiere
from actionneurs import FeuCirculation
from publication_donnees import PublicateurMQTT

def mettre_a_jour_feu(feu, mesure):
    """Eau insuffisante : rouge. Sinon éteint, car le sol et la lumière manquent.

    Ce scénario couvre la condition réservoir d'EF12, pas toute la logique
    EF10 à EF13. Un réservoir suffisant ne suffit pas pour autoriser le vert.
    """
    if mesure.get("etat") == "insuffisant" and mesure.get("vide") is True:
        feu.allumer_rouge()
    elif mesure.get("etat") == "suffisant" and mesure.get("vide") is False:
        feu.allumer_vert()
    else:
        raise ValueError("État du réservoir invalide ou incohérent.")

def publier_mesures_en_attente():
    """Copie les acquisitions partagées sous verrou, puis publie hors du verrou."""
    with verrou:
        mesures = mesures_en_attente.copy()
        mesures_en_attente.clear()
    for topic, mesure in mesures:
        publicateur.publier(topic, mesure)


def boucle_publication():
    """Thread de publication périodique, comme dans la démo du cours."""
    try:
        # Event.wait permet de sortir immédiatement lors d'un Ctrl+C.
        while not arret.wait(config.PERIODE_PUBLICATION):
            publier_mesures_en_attente()
        # Ne pas perdre la dernière acquisition si l'arrêt précède l'échéance.
        publier_mesures_en_attente()
    except Exception as erreur:
        print(f"Erreur de publication MQTT : {erreur}")
        arret.set()


def creer_bus_i2c():
    """Crée le bus dans le programme principal, comme dans la démo de la prof."""
    import board
    return board.I2C()


def main():
    """Lit les capteurs à leurs périodes respectives pendant que le thread publie."""
    global mesures_en_attente, verrou, arret, publicateur

    # Partagé entre les deux threads, comme le compteur de la démo.
    # Ici chaque acquisition doit être conservée, pas seulement un compteur.
    mesures_en_attente = []
    verrou = threading.Lock()
    arret = threading.Event()
    thread_publication = None
    flotteur = None
    i2c = None
    capteur_lumiere = None
    feu = None
    publicateur = None
    try:
        flotteur = Flotteur(config.GPIO_FLOTTEUR, config.PERIODE_LECTURE_RESERVOIR)
        feu = FeuCirculation(config.GPIO_FEU_ROUGE, config.GPIO_FEU_JAUNE,
                            config.GPIO_FEU_VERT)
        publicateur = PublicateurMQTT(client_id="ferixu-publicateur")
        publicateur.connecter()

        thread_publication = threading.Thread(target=boucle_publication)
        thread_publication.start()

        # Horloge monotone pour séparer EF03 (60 s) et EF05 (600 s).
        prochaine_eau = time.monotonic()
        prochaine_lumiere = prochaine_eau
        while not arret.is_set():
            maintenant = time.monotonic()
            if maintenant >= prochaine_eau:
                mesure = flotteur.lire()
                mettre_a_jour_feu(feu, mesure)
                with verrou:
                    mesures_en_attente.append((config.TOPIC_EAU, mesure))
                prochaine_eau = maintenant + flotteur.periode_lecture

            if maintenant >= prochaine_lumiere:
                try:
                    if i2c is None:
                        i2c = creer_bus_i2c()
                    if capteur_lumiere is None:
                        capteur_lumiere = CapteurLumiere(i2c, config.PERIODE_LECTURE_LUMIERE)
                    mesure = capteur_lumiere.lire()
                except (OSError, RuntimeError, ValueError, ImportError) as erreur:
                    # Ne pas transformer une absence/erreur en mesure de zéro lux.
                    print(f"BH1750 indisponible : {erreur}; nouvelle tentative dans 60 s.")
                    capteur_lumiere = None
                else:
                    with verrou:
                        mesures_en_attente.append((config.TOPIC_LUMIERE, mesure))
                prochaine_lumiere = maintenant + config.PERIODE_LECTURE_LUMIERE

            # Attendre la prochaine lecture, sans bloquer le thread MQTT.
            attente = min(prochaine_eau, prochaine_lumiere) - time.monotonic()
            arret.wait(max(0, attente))
    except KeyboardInterrupt:
        print("Arrêt de la lecture de données…")
    finally:
        # Même ordre que la prof : signaler, joindre, puis déconnecter.
        arret.set()
        if thread_publication is not None and thread_publication.ident is not None:
            thread_publication.join()
        # Les finally garantissent la fermeture des GPIO même si la
        # déconnexion MQTT ou la fermeture du flotteur produit une erreur.
        try:
            if publicateur is not None:
                publicateur.deconnecter()
        finally:
            try:
                if flotteur is not None:
                    flotteur.fermer()
            finally:
                try:
                    if feu is not None:
                        feu.fermer()
                finally:
                    # Le pilote reçoit ce bus; c'est donc main.py qui le libère.
                    if i2c is not None:
                        i2c.deinit()


if __name__ == "__main__":
    main()