# Programme Raspberry Pi

Ce dossier contient une première démo du capteur de luminosité BH1750 et de trois DEL. Le programme lit la luminosité chaque seconde et allume une DEL :

| Mesure | DEL allumée |
| --- | --- |
| Moins de 100 lux | Rouge |
| De 100 à moins de 10 000 lux | Jaune |
| 10 000 lux ou plus | Verte |

Cette démo utilise le seuil de 10 000 lux des exigences du projet. Elle ne calcule pas encore les heures de lumière cumulées et ne lit pas l’humidité du sol ni le niveau du réservoir. Les couleurs affichées ici représentent seulement la mesure instantanée de luminosité.

## Matériel et branchements

- Raspberry Pi avec Raspberry Pi OS;
- capteur BH1750;
- trois DEL et trois résistances (environ 220 à 330 Ω chacune).

Reliez le BH1750 au bus I²C du Pi : SDA au GPIO 2 (broche physique 3), SCL au GPIO 3 (broche physique 5), et GND à GND. Alimentez le capteur selon les indications de son module; utilisez une alimentation compatible avec les entrées 3,3 V du Raspberry Pi.

Reliez chaque DEL à une broche GPIO à travers sa résistance, puis à GND. Les broches du programme sont en numérotation **BCM** :

| Couleur | GPIO BCM | Broche physique |
| --- | ---: | ---: |
| Rouge | 27 | 13 |
| Jaune | 22 | 15 |
| Verte | 23 | 16 |

Le commentaire du code initial indiquait GPIO 17, mais `LED(27)` utilise GPIO 27 en mode BCM. Ce programme conserve la broche 27.

## Installation

1. Activez I²C avec `sudo raspi-config`, puis **Interface Options → I2C → Enable**. Redémarrez le Pi si le système le demande.
2. Installez les outils et la bibliothèque GPIO du système :

   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-gpiozero python3-lgpio i2c-tools
   ```

3. Depuis le dossier `raspberry_pi`, créez et activez un environnement Python :

   ```bash
   python3 -m venv --system-site-packages .venv
   source .venv/bin/activate
   ```

4. Installez les bibliothèques Adafruit :

   ```bash
   python -m pip install adafruit-blinka adafruit-circuitpython-bh1750
   ```

5. Vérifiez que le capteur est détecté sur le bus I²C :

   ```bash
   i2cdetect -y 1
   ```

   Le BH1750 apparaît généralement à l’adresse `23` ou `5c` dans la grille.

## Lancer le programme

Depuis `raspberry_pi`, avec l’environnement virtuel activé :

```bash
python luminosite_bh1750.py
```

Les valeurs en lux s’affichent dans le terminal. Appuyez sur `Ctrl+C` pour arrêter le programme; les DEL seront alors éteintes.
