"""Composants disponibles dans le paquet ``capteurs``.

Les pilotes et leurs bibliothèques sont chargés à la demande. Le matériel
n'est initialisé que lors de la construction explicite d'un capteur.
"""

from importlib import import_module

__all__ = [
    "Capteur",
    "CapteurLumiere",
    "Flotteur",
    "CapteurSol",
]

_MODULES = {
    "Capteur": ".capteur",
    "CapteurLumiere": ".capteur_bh1750",
    "Flotteur": ".flotteur",
    "CapteurSol": ".capteur_sol",
}


def __getattr__(name):
    """Charge le pilote correspondant uniquement si son composant est utilisé."""
    module_name = _MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    component = getattr(import_module(module_name, __name__), name)
    globals()[name] = component
    return component
