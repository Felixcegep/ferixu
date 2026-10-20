# À faire au prochain cours — Pousse / Ferixu

**État mis à jour : 20 octobre 2026, après intégration du scénario EF12.**
**Remise de la partie 1 : 20 octobre 2026 (10 %), démonstration en équipe.**

Objectif du cours : obtenir une chaîne complète et démontrable **capteur réel → acquisition horodatée → publication → broker MQTT local → abonnement → fichier**, puis déclencher au moins un actionneur selon une exigence fonctionnelle.

## Ce qui est déjà présent

- `raspberry_pi/main.py` lit le flotteur immédiatement dans le thread principal, puis à la période configurée (5 s pour les essais locaux, 600 s requises par EF05). Comme dans la démo de la prof, un thread MQTT séparé publie les acquisitions en attente à la période configurée (5 s actuellement), avec une liste partagée protégée par `Lock` et un `Event` d’arrêt.
- Le publicateur envoie l’état du réservoir sur `ferixu/eau`, avec un horodatage ISO 8601 en UTC et QoS 1.
- Le subscriber reçoit les topics du réservoir et de la lumière et ajoute les messages à `donnees/lectures_capteurs.jsonl` en conservant leur horodatage.
- Le BH1750 est intégré : lecture toutes les 60 s, publication sur `ferixu/lumiere` et enregistrement par le subscriber. Le capteur de sol reste hors du programme actif. Le feu est intégré pour le scénario réservoir insuffisant → rouge (EF12), éteint sinon. Le fichier de la pompe ne contient pas encore d’implémentation.
- L’interface NiceGUI est une maquette simulée ; elle ne reçoit pas les mesures réelles et ne commande pas le matériel.

**Ces éléments décrivent le code présent, pas un montage validé. Les essais matériels restent à effectuer.**

## Priorité 1 — Valider la collecte complète sur le Raspberry Pi

- [ ] Confirmer le matériel réellement disponible et les alternatives utilisées : flotteur, relais, capteur de sol et tube. Vérifier la référence du flotteur (SENS-112-200 ou SENS-112-250) et la disponibilité des câbles Dupont indiqués « non reçu ».
- [ ] Vérifier le branchement du flotteur sur GPIO **BCM 16**, son alimentation et l’interprétation du contact : le code considère un contact fermé comme un réservoir insuffisant.
- [ ] Créer ou vérifier le `.venv`, installer avec `python -m pip install -r requirements.txt` et confirmer que les bibliothèques correspondent aux composants effectivement utilisés.
- [ ] Démarrer Mosquitto, puis le subscriber, puis `main.py`. Le lancement actuel nécessite deux terminaux Python ; `main.py` ne démarre pas le subscriber.
- [ ] Tester les deux états réels du flotteur et vérifier leur réception sur `ferixu/eau` ainsi que leur écriture dans le fichier.
- [ ] Comparer les horodatages et le nombre de messages publiés, reçus et enregistrés pendant l’essai ; vérifier qu’aucune perte n’est observable.
- [ ] Vérifier l’arrêt avec `Ctrl+C` et la libération du GPIO.

**Résultat attendu :** un montage visible, une mesure réelle, un message MQTT reçu et une ligne enregistrée avec le même horodatage.

## Priorité 2 — Ajouter un actionneur pour la démonstration

Le feu tricolore est indiqué « reçu » dans l’inventaire. Un premier scénario possible est **réservoir insuffisant → feu rouge (EF12)**.

- [ ] Vérifier le câblage et l’alimentation du feu. Les broches présentes dans le pilote sont BCM 23 (rouge), 22 (jaune) et 27 (vert) ; elles restent à valider sur le montage.
- [x] Adapter le pilote : initialisation dans une instance avec `TrafficLights`, méthodes en `snake_case`, commentaires français et libération des GPIO à l’arrêt.
- [x] Séparer la décision dans `logique_decision.py` et intégrer le scénario EF12 au programme actif.
- [ ] Montrer le déclenchement du rouge en changeant réellement l’état du flotteur. Si une condition est simulée, préciser laquelle ; conserver une acquisition réelle pour la chaîne MQTT.
- [x] Prévoir l’extinction du feu à l’arrêt. Ne pas afficher un état vert à partir du seul niveau d’eau : EF10 exige aussi l’humidité et les heures de lumière.

**Résultat attendu :** un actionneur physique branché et un déclenchement expliqué par une exigence. Le scénario EF12 seul ne constitue pas toute la logique EF10 à EF13.

## Priorité 3 — Corriger les erreurs de base et préparer la remise

- [ ] Gérer dans le subscriber un JSON invalide, un payload incomplet, un problème d’écriture du fichier et une connexion MQTT impossible, avec des messages compréhensibles.
- [ ] Tester un broker indisponible et une lecture de capteur en erreur ; ne jamais remplacer une erreur par une mesure valide ou une autorisation d’arrosage.
- [x] Aligner les pilotes I²C sur `Capteur` avec bus fourni au constructeur, supprimer leurs initialisations matérielles à l’import et corriger les dépendances. Le BH1750 est intégré; l’intégration du sol et la validation matérielle des deux restent à faire.
- [ ] Mettre à jour les README avec le montage réellement utilisé, les broches BCM/physiques, les alimentations, les bus, les topics, les payloads et les commandes vérifiées.
- [ ] Corriger le lien `../EXIGENCES.md` du README Raspberry Pi vers `../documentation/exigences_fonctionnelles.md` et clarifier les instructions de lancement.
- [ ] Préparer une courte procédure de démonstration : démarrage du broker, subscriber, collecte, changement du flotteur, consultation du fichier et déclenchement du feu.
- [ ] Noter les résultats des essais, les simulations utilisées et ce qui reste à valider sur le matériel.

## Suite du projet — Fonctions encore manquantes

Ces tâches complètent les exigences du projet. La priorité du prochain cours reste la chaîne de démonstration ; la remise demande aussi le code des objets disponibles.

| Partie | Travail restant |
| --- | --- |
| Sol — EF01, EF02 | Intégrer l’humidité et la température ensemble toutes les 10 minutes, avec horodatage. Identifier le capteur alternatif et documenter sa calibration avant toute conversion en %. |
| Luminosité — EF03, EF04 | Lecture toutes les 60 s intégrée et testée en simulation; valider sur le Pi. Ajouter le cumul quotidien au seuil de 10 000 lux. Le pilote fabricant attend 180 ms pour la conversion, compatible avec la période de 60 s. |
| Réservoir — EF05 | Synchroniser sa lecture avec le sol et ajouter les vérifications immédiatement avant et après chaque activation de la pompe. |
| Pompe et relais — EF06 à EF09 | Implémenter les pilotes et la décision : humidité sous 30 %, mode automatique actif, eau suffisante, 3 secondes, délai minimal de 30 minutes et maximum de 6 arrosages automatiques par période de 24 heures. |
| Sécurité de la pompe — EF07, EF14, EF16 | Refuser toute activation si l’eau est insuffisante ou si sa lecture échoue, y compris en manuel et en test. Limiter le test à 3 secondes et garantir l’arrêt en fin de durée et à l’arrêt du programme. |
| Feu complet — EF10 à EF13 | Combiner humidité, lumière et réservoir ; appliquer la priorité au rouge, les seuils de 3,6 h et 6 h et le retour à la couleur appropriée à la prochaine lecture. |
| Contrôles — EF14 à EF17 | Relier les boutons au matériel : arrosage manuel, mode automatique, test pompe/relais et test des trois couleurs. |
| Interface — EF18 à EF23 | Remplacer les données simulées par les mesures horodatées ; afficher les graphiques réels (sol à deux axes et luminosité), les 7 derniers jours de lumière et les informations d’arrosage. |
| Paramètres — EF24 | Enregistrer les paramètres modifiés et les faire utiliser par la logique réelle du système. |

## Références

- [Consignes de la remise et démonstration](remise_partie_1.md)
- [Exigences corrigées EF01 à EF24](exigences_fonctionnelles.md)
- [Inventaire et statuts du matériel](inventaire_materiel.md)
- [Installation et lancement sur le Raspberry Pi](../raspberry_pi/README.md)

## Ajout du BH1750

- [x] Intégrer sa lecture réelle toutes les 60 s indépendamment du flotteur.
- [x] Publier les mesures horodatées sur `ferixu/lumiere` via le thread existant et les enregistrer.
- [x] Signaler une absence/lecture invalide sans inventer de lux; retenter à la prochaine minute.
- [ ] Valider `i2cdetect -y 1`, le branchement 3,3 V / GND / SDA / SCL, les lectures et la transmission sur le Raspberry Pi.
- [ ] Ajouter ultérieurement le cumul lumineux EF04 et les historiques.

Les périodes locales du réservoir et de publication sont actuellement à 5 s et ont été conservées. Rétablir 600 s pour la lecture du réservoir afin de respecter EF05; la lumière reste à 60 s selon EF03.
