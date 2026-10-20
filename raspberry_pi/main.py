"""Acquisition réelle, décisions du feu et publication vers le broker local."""
import argparse
from contextlib import ExitStack, contextmanager
from pathlib import Path
import sys
import signal
import threading
import time
from uuid import uuid4

# Rend aussi possible le lancement documenté : cd raspberry_pi; python main.py.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from raspberry_pi import config
from raspberry_pi.capteurs import Flotteur
from raspberry_pi.capteurs.capteur_supervise import CapteurIndisponible, CapteurSupervise
from raspberry_pi.actionneurs import FeuTricolore
from raspberry_pi.logique_decision import mettre_a_jour_feu_reservoir
from raspberry_pi.publication_donnees import PublicateurMQTT


@contextmanager
def ouvrir_flotteur():
    """Crée le GPIO seulement au moment de la tentative d'acquisition."""
    flotteur = Flotteur(config.GPIO_FLOTTEUR)
    try:
        yield flotteur
    finally:
        flotteur.fermer()


@contextmanager
def ouvrir_capteur_i2c(type_capteur):
    """Un bus possédé par chaque pilote : une panne ne ferme pas le voisin."""
    with ExitStack() as ressources:
        import board
        import busio
        i2c = busio.I2C(board.SCL, board.SDA)
        ressources.callback(i2c.deinit)
        if type_capteur == "lumiere":
            from raspberry_pi.capteurs import CapteurLumiere
            capteur = CapteurLumiere(i2c, config.PERIODE_LECTURE_LUMIERE)
        else:
            from raspberry_pi.capteurs import CapteurSol
            capteur = CapteurSol(i2c, config.SOL_BRUT_SEC, config.SOL_BRUT_HUMIDE,
                                 config.PERIODE_LECTURE_SOL)
        ressources.callback(capteur.fermer)
        yield capteur


def commander_feu(feu, mesure):
    """Une panne du feu ne doit pas interrompre l'acquisition des capteurs."""
    try:
        if mesure is None:
            feu.allumer_rouge()
        else:
            mettre_a_jour_feu_reservoir(feu, mesure)
    except Exception as erreur:
        print(f"Feu indisponible : {erreur}; collecte maintenue.", file=sys.stderr)
        try:
            feu.fermer()
        except Exception as nettoyage:
            print(f"Erreur de libération du feu : {nettoyage}", file=sys.stderr)
        return None
    return feu


def collecter(taches, publicateur, feu, arret, une_lecture=False):
    """Ordonnance les acquisitions avec l'horloge monotone, sans dérive réseau.

    Une tâche = (capteur, topic). L'horodatage UTC est créé par le pilote;
    la décision est appliquée avant l'envoi MQTT.
    """
    prochains = [time.monotonic()] * len(taches)
    while not arret.is_set():
        for index, (capteur, topic) in enumerate(taches):
            if time.monotonic() < prochains[index]:
                continue
            try:
                mesure = capteur.lire()
            except CapteurIndisponible as erreur:
                print(f"{erreur}; nouvelle tentative dans {capteur.periode_lecture} s.",
                      file=sys.stderr, flush=True)
                # Le rouge signale ici une panne, pas une mesure d'eau inventée.
                if topic == config.TOPIC_EAU and feu is not None:
                    feu = commander_feu(feu, None)
            else:
                if topic == config.TOPIC_EAU and feu is not None:
                    feu = commander_feu(feu, mesure)
                publicateur.publier(topic, mesure)
            prochains[index] += capteur.periode_lecture
            # Pas de rafale de lectures si une opération a pris trop de temps.
            if prochains[index] <= time.monotonic():
                prochains[index] = time.monotonic() + capteur.periode_lecture
        if une_lecture:
            return
        arret.wait(max(0, min(prochains) - time.monotonic()))


def demander_arret(signum, frame):
    """Fait passer SIGTERM par le même nettoyage que Ctrl+C."""
    raise KeyboardInterrupt


def main():
    """Initialise les objets demandés et libère toutes les ressources à l'arrêt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sans-feu", action="store_true", help="Diagnostic acquisition seulement")
    parser.add_argument("--lumiere", action="store_true", help="Activer le BH1750 réel")
    parser.add_argument("--sol", action="store_true", help="Activer le STEMMA réel")
    parser.add_argument("--une-lecture", action="store_true", help="Une acquisition réelle par capteur, puis arrêt")
    args = parser.parse_args()
    try:
        signal.signal(signal.SIGTERM, demander_arret)
        with ExitStack() as ressources:
            flotteur = CapteurSupervise(
                "réservoir", config.PERIODE_LECTURE_RESERVOIR, ouvrir_flotteur)
            ressources.callback(flotteur.fermer)
            feu = None
            if not args.sans_feu:
                try:
                    feu = FeuTricolore(config.GPIO_FEU_ROUGE, config.GPIO_FEU_JAUNE, config.GPIO_FEU_VERT)
                except Exception as erreur:
                    print(f"Feu indisponible : {erreur}; collecte maintenue.", file=sys.stderr)
                else:
                    ressources.callback(feu.fermer)
            taches = [(flotteur, config.TOPIC_EAU)]
            if args.lumiere:
                capteur = CapteurSupervise("luminosité", config.PERIODE_LECTURE_LUMIERE,
                                          lambda: ouvrir_capteur_i2c("lumiere"))
                ressources.callback(capteur.fermer)
                taches.append((capteur, config.TOPIC_LUMIERE))
            if args.sol:
                capteur = CapteurSupervise("sol", config.PERIODE_LECTURE_SOL,
                                          lambda: ouvrir_capteur_i2c("sol"))
                ressources.callback(capteur.fermer)
                taches.append((capteur, config.TOPIC_SOL))
            publicateur = PublicateurMQTT(client_id=f"ferixu-publicateur-{uuid4().hex[:12]}")
            ressources.callback(publicateur.deconnecter)
            publicateur.connecter()
            collecter(taches, publicateur, feu, threading.Event(), args.une_lecture)
    except KeyboardInterrupt:
        print("Arrêt de la collecte et libération des GPIO.")
    except Exception as erreur:
        print(f"Collecte arrêtée : {erreur}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
