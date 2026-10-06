Installe des logiciels pour tout le système.


sudo apt update
sudo apt install -y mosquitto mosquitto-clients
mosquitto est le broker lui-même ; mosquitto-clients fournit les commandes de test mosquitto_pub et mosquitto_sub.






sudo systemctl status mosquitto


sudo systemctl enable mosquitto # Démarrage automatique au boot du Pi
sudo systemctl start mosquitto 



Terminal A : s'abonner


mosquitto_sub -h localhost -t projet/bme680
Terminal B : publier un message test




Copy
mosquitto_pub -h localhost -t projet/bme680 -m "test"
Si le terminal A affiche test, le broker fonctionne.