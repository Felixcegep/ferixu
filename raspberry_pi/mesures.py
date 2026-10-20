"""Validation des mesures partagée par le publicateur et l'ingestion."""
from datetime import datetime, timedelta
import math
from raspberry_pi import config


def valider_mesure(topic, mesure):
    """Refuse un payload incomplet, une erreur ou une valeur non finie."""
    if not isinstance(mesure, dict):
        raise ValueError("Le payload doit être un objet JSON.")
    horodatage = mesure.get("horodatage")
    if not isinstance(horodatage, str):
        raise ValueError("Horodatage d'acquisition manquant.")
    date = datetime.fromisoformat(horodatage.replace("Z", "+00:00"))
    if date.utcoffset() != timedelta(0):
        raise ValueError("L'horodatage doit inclure le fuseau UTC.")
    if topic == config.TOPIC_EAU:
        etat = mesure.get("etat")
        if etat not in ("suffisant", "insuffisant"):
            raise ValueError("État du réservoir invalide.")
        if mesure.get("vide") is not (etat == "insuffisant"):
            raise ValueError("Les champs etat et vide doivent être cohérents.")
    elif topic == config.TOPIC_LUMIERE:
        _nombre(mesure, "lux", 0, 65535)
    elif topic == config.TOPIC_SOL:
        _nombre(mesure, "temperature_c", -40, 85)
        _nombre(mesure, "humidite_brute", 0, 65535)
        if "humidite_pct" in mesure:
            _nombre(mesure, "humidite_pct", 0, 100)
    else:
        raise ValueError(f"Topic de mesure non reconnu : {topic}")
    return mesure


def _nombre(mesure, cle, minimum, maximum):
    """Les booléens JSON ne constituent pas des mesures numériques."""
    valeur = mesure.get(cle)
    if (isinstance(valeur, bool) or not isinstance(valeur, (int, float))
            or not minimum <= valeur <= maximum or not math.isfinite(valeur)):
        raise ValueError(f"Mesure {cle} invalide ou hors plage.")
