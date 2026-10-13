from abc import ABC, abstractmethod


class Capteur(ABC):

    def __init__(self, nom: str, periode_lecture: float):
        self.nom = nom
        self.periode_lecture = periode_lecture

    @abstractmethod
    def lire(self) -> dict:
        pass

    def fermer(self) -> None:
        """Libère le matériel. Par défaut, on ne fait rien."""
        ...
