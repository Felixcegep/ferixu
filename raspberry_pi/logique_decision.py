"""Règle de démonstration EF12, indépendante de GPIO et de MQTT."""


def mettre_a_jour_feu(feu, mesure):
    """Eau insuffisante : rouge. Sinon éteint, car le sol et la lumière manquent.

    Ce scénario couvre la condition réservoir d'EF12, pas toute la logique
    EF10 à EF13. Un réservoir suffisant ne suffit pas pour autoriser le vert.
    """
    if mesure.get("etat") == "insuffisant" and mesure.get("vide") is True:
        feu.allumer_rouge()
    elif mesure.get("etat") == "suffisant" and mesure.get("vide") is False:
        feu.eteindre()
    else:
        raise ValueError("État du réservoir invalide ou incohérent.")
