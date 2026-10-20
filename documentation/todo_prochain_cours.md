# Suivi de la remise — Pousse / Ferixu

**Mise à jour : 20 octobre 2026.** Partie 1 : 10 %, démonstration en équipe.

## Corrections logicielles effectuées

- Pilotes sans initialisation matérielle à l'import; capteurs héritant de `Capteur`.
- Broches BCM et paramètres MQTT regroupés dans `raspberry_pi/config.py`, lecture du `.env` à la racine.
- Flotteur horodaté en UTC; lecture immédiate puis toutes les 600 s.
- Décision EF12 séparée : réservoir insuffisant → feu rouge. Aucune déduction de vert/jaune sans les autres mesures nécessaires.
- BH1750 optionnel toutes les 60 s et sol optionnel toutes les 600 s; calibration explicite avant publication d'un pourcentage.
- Validation du payload et des valeurs, abonnement QoS 1, erreurs de décodage et d'écriture signalées sans arrêter l'ingestion.
- Identifiants retirés du diagnostic MQTT; réseau et GPIO uniquement lors d'un lancement explicite.
- Pilote de pompe disponible : refus sans eau, durée maximale de 3 s, arrêt et vérifications du réservoir; pas de commande de pompe dans le programme principal.
- Capteurs absents isolés, sans mesure inventée; nouvelle tentative à la période normale et rouge sur erreur du réservoir si le feu fonctionne.
- README d'installation et de démonstration mis à jour.

Les tests utilisent des GPIO simulés. L'essai avec Mosquitto local valide le transport et le fichier, **pas le matériel**.

## Priorités avant la présentation

- [ ] Confirmer le Raspberry Pi 4, les composants reçus et les alternatives réellement utilisées. Résoudre la référence du flotteur SENS-112-200 / SENS-112-250 et la disponibilité des câbles.
- [ ] Vérifier le flotteur sur BCM16 (physique 36), la masse et les deux états réels. Le contact fermé doit correspondre à « insuffisant » pour ce code.
- [ ] Vérifier le feu : rouge BCM23 / physique 16, jaune BCM22 / physique 15, vert BCM27 / physique 13; confirmer résistances, polarité et alimentation du module réel.
- [ ] Installer le `.venv` et les dépendances sur le Pi avec les commandes du [README Raspberry Pi](../raspberry_pi/README.md); exécuter `python -m pip check`.
- [ ] Configurer le broker local, le démarrer, puis lancer l'ingestion et attendre sa confirmation d'abonnement avant la collecte.
- [ ] Démontrer une vraie lecture du flotteur, le message MQTT, le fichier JSONL avec le même horodatage et le feu rouge quand l'eau est insuffisante.
- [ ] Comparer le nombre de messages et les horodatages : aucune perte observable durant l'essai; ne pas assimiler QoS 1 à une écriture garantie sur disque.
- [ ] Vérifier `Ctrl+C`, l'extinction du feu et la libération des GPIO. Ne pas lancer deux processus concurrents sur les mêmes broches.
- [ ] Si le BH1750 et le sol sont présentés : confirmer adresses I²C, modèles réels, dépendances, valeurs et calibration. Sans calibration, annoncer clairement une humidité brute et l'absence de validation d'EF01 en %.
- [ ] Noter les résultats matériels et toute simulation utilisée; les tests automatiques ne remplacent pas l'acquisition réelle.

## Fonctions du projet restant à intégrer

| Partie | Travail restant |
| --- | --- |
| Sol — EF01, EF02 | Calibrer le capteur réel, confirmer la conversion et valider les lectures simultanées toutes les 10 min sur le Pi |
| Luminosité — EF03, EF04 | Valider les lectures toutes les 60 s; ajouter le cumul quotidien à partir de 10 000 lux |
| Réservoir — EF05 | Valider les contacts; intégrer les mesures avant/après pompe au flux publié lors de l'intégration du contrôleur |
| Pompe — EF06 à EF09 | Identifier le relais alternatif; intégrer décision, mode automatique, délai de 30 min, maximum de 6 activations par 24 h et historique; pilote seul insuffisant |
| Feu — EF10 à EF13 | Compléter les règles avec humidité et cumul lumineux, priorité rouge, seuils de 3,6 h et 6 h |
| Contrôles — EF14 à EF17 | Relier les commandes à un contrôleur réel avec refus sans eau et tests limités à 3 s |
| Interface — EF18 à EF23 | Remplacer les données simulées, graphiques à deux axes du sol, historique lumineux et informations d'arrosage |
| Paramètres — EF24 | Faire utiliser les paramètres persistés par le système réel |
| Autres objets reçus | OLED et buzzers non implémentés; préciser leur rôle si retenus dans le périmètre présenté |

La démo minimale n'exige pas une interface terminée. Elle ne dispense pas de remettre le code des objets disponibles prévus dans le périmètre : annoncer précisément ce qui est présent, intégré, testé par simulation et validé physiquement.

## Références

- [Consignes de remise](remise_partie_1.md)
- [Exigences corrigées](exigences_fonctionnelles.md)
- [Inventaire](inventaire_materiel.md)
- [Installation et démonstration](../raspberry_pi/README.md)
