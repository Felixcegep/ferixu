# Installation rapide du broker MQTT

Les instructions complètes d’installation du Raspberry Pi, de création de l’environnement Python, de collecte et d’enregistrement sont dans [README.md](README.md).

Pour installer et démarrer le broker local :

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

Le programme publie l’état du flotteur sur `ferixu/eau`. Pour l’observer :

```bash
mosquitto_sub -h localhost -t 'ferixu/#' -v
```
