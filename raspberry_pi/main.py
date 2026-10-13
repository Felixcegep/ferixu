"""Acquisition du réservoir dans un thread et publication vers le broker local."""

import threading

import config
from capteurs import Flotteur
from publication_donnees import PublicateurMQTT


def boucle_publication(flotteur, publicateur, arret):
    """Lit immédiatement le flotteur, puis toutes les 10 minutes (EF05)."""
    while not arret.is_set():
        try:
            mesure = flotteur.lire()
            publicateur.publier(config.TOPIC_EAU, mesure)
        except (OSError, RuntimeError, ValueError) as erreur:
            # Une erreur n'est jamais transformée en état d'eau suffisant.
            print(f"Erreur de collecte ou de publication : {erreur}")
            arret.set()
            return
        if arret.wait(config.PERIODE_LECTURE_RESERVOIR):
            return


def main():
    """Initialise les composants et libère les ressources à l'arrêt."""
    flotteur = None
    publicateur = PublicateurMQTT(client_id="ferixu-publicateur")
    arret = threading.Event()
    thread_publication = None
    try:
        flotteur = Flotteur(config.GPIO_FLOTTEUR)
        publicateur.connecter()
        thread_publication = threading.Thread(
            target=boucle_publication, args=(flotteur, publicateur, arret)
        )
        thread_publication.start()
        while not arret.wait(1):
            pass
    except KeyboardInterrupt:
        print("Arrêt de la collecte des données…")
    finally:
        arret.set()
        if thread_publication is not None:
            thread_publication.join()
        publicateur.deconnecter()
        if flotteur is not None:
            flotteur.fermer()


if __name__ == "__main__":
    main()
