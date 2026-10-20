"""Isolation d'un pilote : absence au démarrage, panne et reconnexion."""
from contextlib import ExitStack
import sys
from .capteur import Capteur


class CapteurIndisponible(RuntimeError):
    """Aucune mesure valide n'est disponible; ne jamais utiliser une ancienne valeur."""


class CapteurSupervise(Capteur):
    def __init__(self, nom, periode_lecture, ouvrir):
        """`ouvrir` crée un contexte possédant le pilote et ses ressources matérielles."""
        super().__init__(nom, periode_lecture)
        self._ouvrir = ouvrir
        self._ressources = None
        self._capteur = None
        self.disponible = False

    def lire(self):
        """Réessaie à chaque échéance normale; aucune valeur simulée de secours."""
        try:
            if self._capteur is None:
                ressources = ExitStack()
                try:
                    capteur = ressources.enter_context(self._ouvrir())
                except BaseException:
                    ressources.close()
                    raise
                self._ressources = ressources
                self._capteur = capteur
            mesure = self._capteur.lire()
        except Exception as erreur:
            # Frontière avec les bibliothèques : certaines utilisent leurs propres
            # types d'exception pour une adresse I²C absente ou un backend manquant.
            self.disponible = False
            self.fermer()
            raise CapteurIndisponible(f"{self.nom} indisponible : {erreur}") from erreur
        if not self.disponible:
            print(f"Capteur {self.nom} disponible.", flush=True)
        self.disponible = True
        return mesure

    def fermer(self):
        """Libère le pilote et son bus sans empêcher le nettoyage des autres objets."""
        ressources, self._ressources = self._ressources, None
        self._capteur = None
        self.disponible = False
        if ressources is not None:
            try:
                ressources.close()
            except Exception as erreur:
                print(f"Erreur de libération de {self.nom} : {erreur}", file=sys.stderr)
