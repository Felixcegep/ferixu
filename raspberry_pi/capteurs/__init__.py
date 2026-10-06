"""Composants disponibles dans le paquet ``capteurs``.

Les pilotes de capteurs peuvent accéder au matériel dès leur import. On les
importe donc uniquement lorsqu'un composant est demandé explicitement.
"""

from importlib import import_module

__all__ = [
    "CapteurLumiere",
    "FeuCirculation",
    "Flotteur",
    "SoilSensor",
]

_MODULES = {
    "CapteurLumiere": ".Bh1750",
    "FeuCirculation": ".ARD625",
    "Flotteur": ".Flotteur",
    "SoilSensor": ".Soil_Sensor",
}


def __getattr__(name):
    """Charge le pilote correspondant uniquement si son composant est utilisé."""
    module_name = _MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    component = getattr(import_module(module_name, __name__), name)
    globals()[name] = component
    return component
