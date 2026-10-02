#Interrupteur à flotteur SENS-112-200

import time
from gpiozero import Button
from signal import pause

# Configuration du capteur sur la broche GPIO 23
# 'pull_up=True' utilise la résistance interne pour forcer l'état à HIGH par défaut
flotteur = Button(23, pull_up=True)

def niveau_haut():
    print("⚠️ Alerte : Niveau de liquide HAUT détecté ! (Circuit fermé)")

def niveau_bas():
    print("✅ Information : Le niveau de liquide est redescendu. (Circuit ouvert)")

# Assignation des fonctions aux événements du capteur
flotteur.when_pressed = niveau_haut
flotteur.when_released = niveau_bas

print("Démarrage de la surveillance du niveau d'eau... (Appuyez sur Ctrl+C pour quitter)")

try:
    # Maintient le script actif en attente d'événements
    pause()
except KeyboardInterrupt:
    print("\nArrêt de la surveillance.")