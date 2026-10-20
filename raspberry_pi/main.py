"""Flotteur et feu dans le thread principal; publication MQTT séparée.

Structure adaptée de la démo de la prof :
https://github.com/5P0-Integration-d-objets-connectes/demo-broker-thread/blob/main/main.py
"""
import threading

import config
from capteurs import Flotteur
from actionneurs import FeuCirculation
from logique_decision import mettre_a_jour_feu
from publication_donnees import PublicateurMQTT


def publier_mesures_en_attente():
    """Copie les acquisitions partagées sous verrou, puis publie hors du verrou."""
    with verrou:
        mesures = mesures_en_attente.copy()
        mesures_en_attente.clear()
    for mesure in mesures:
        publicateur.publier(config.TOPIC_EAU, mesure)


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


def main():
    """Lit le flotteur et commande le feu pendant que le thread publie."""
    global mesures_en_attente, verrou, arret, publicateur

    # Partagé entre les deux threads, comme le compteur de la démo.
    # Ici chaque acquisition doit être conservée, pas seulement un compteur.
    mesures_en_attente = []
    verrou = threading.Lock()
    arret = threading.Event()
    thread_publication = None
    flotteur = None
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

        while not arret.is_set():
            mesure = flotteur.lire()
            mettre_a_jour_feu(feu, mesure)
            # Section protégée, comme le compteur partagé de la démo.
            with verrou:
                mesures_en_attente.append(mesure)
            # Contrairement à sleep(600), cette attente se réveille aussi si
            # le thread MQTT signale un problème et demande l'arrêt.
            arret.wait(flotteur.periode_lecture)
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
                if feu is not None:
                    feu.fermer()


if __name__ == "__main__":
    main()
