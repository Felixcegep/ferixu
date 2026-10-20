"""Diagnostic local explicite, sans identifiants ni connexion à l'importation.

Depuis la racine : python -m raspberry_pi.publication_donnees.test_mqttx
Nécessite le flotteur réel et le subscriber déjà démarré.
"""
from uuid import uuid4
from contextlib import ExitStack
from raspberry_pi import config
from raspberry_pi.capteurs import Flotteur
from raspberry_pi.publication_donnees import PublicateurMQTT


def main():
    """Publie une vraie lecture horodatée sur le broker configuré."""
    with ExitStack() as ressources:
        flotteur = Flotteur(config.GPIO_FLOTTEUR)
        ressources.callback(flotteur.fermer)
        publicateur = PublicateurMQTT(f"ferixu-diagnostic-{uuid4().hex[:12]}")
        ressources.callback(publicateur.deconnecter)
        publicateur.connecter()
        publicateur.publier(config.TOPIC_EAU, flotteur.lire())


if __name__ == "__main__":
    main()
