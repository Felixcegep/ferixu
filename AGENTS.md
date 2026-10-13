# Instructions pour les agents — Ferixu / Pousse

## Contexte et sources à consulter

Le projet surveille un basilic en pot et automatise son arrosage avec un Raspberry Pi 4, des capteurs et des actionneurs. La remise de la partie 1 vaut **10 %** et est prévue le **20 octobre 2026**, avec une démonstration en équipe en classe.

Avant de modifier une partie du projet, consulter les documents applicables :

- [Consignes de la remise, démonstration et critères d’évaluation](documentation/remise_partie_1.md).
- [Exigences fonctionnelles corrigées EF01 à EF24](documentation/exigences_fonctionnelles.md), référence des comportements attendus.
- [Inventaire du matériel](documentation/inventaire_materiel.md), référence des quantités et statuts de réception.
- [Composants et paramètres du basilic](documentation/README.md).
- [README principal](README.md) et [README Raspberry Pi](raspberry_pi/README.md), pour l’état de l’implémentation et les commandes de lancement.

Distinguer les fonctions prévues, implémentées, simulées et validées sur le matériel. Ne pas présenter une exigence ou un pilote présent dans le dépôt comme une fonction déjà opérationnelle. Conserver les modifications de l’utilisateur sans les écraser.

## Priorités de la première remise

Pour les travaux liés à cette remise, privilégier une chaîne démontrable : **capteur → acquisition horodatée → publication → broker MQTT local → abonnement → enregistrement dans un fichier**, et le déclenchement d’au moins un actionneur selon une exigence fonctionnelle.

La démonstration doit inclure un montage visible et fonctionnel, au moins un capteur réel et au moins un actionneur. Une simulation du déclenchement est permise lorsque la condition ne peut pas être reproduite facilement en direct ; la documenter explicitement. Ne pas remplacer toute l’acquisition matérielle par des données simulées.

## Organisation et programmation orientée objet

- Dossiers, fichiers Python, fonctions, méthodes et variables : `snake_case`.
- Classes : `PascalCase` ; constantes : `UPPER_SNAKE_CASE`.
- Séparer les pilotes de capteurs/actionneurs, l’acquisition, la logique de décision, la communication MQTT et l’enregistrement.
- Modéliser les capteurs et actionneurs avec des classes, propriétés et méthodes appropriées. Réutiliser une classe abstraite ou l’héritage lorsque des comportements communs le justifient ; ne pas ajouter de hiérarchie inutile.
- Commenter en français les méthodes et les choix non évidents, notamment les unités, seuils, constantes, broches et interprétations électriques.

## Acquisition et règles fonctionnelles

Respecter les exigences EF01 à EF24 pour les travaux concernés :

- Humidité (%) et température du sol (°C) : lecture ensemble toutes les 10 minutes.
- Luminosité (lux) : lecture toutes les 1 minute ; lumière suffisante à partir de 10 000 lux ; cumul quotidien et historique des 7 derniers jours.
- Réservoir : vérification toutes les 10 minutes avec le sol, immédiatement avant et après chaque activation de la pompe ; état « suffisant » ou « insuffisant ».
- Valeurs initiales d’arrosage : seuil d’humidité de 30 %, durée de 3 secondes, délai automatique minimal de 30 minutes et maximum de 6 arrosages automatiques par période de 24 heures ; le mode automatique doit être activé pour arroser automatiquement.
- Ne jamais activer la pompe avec un niveau d’eau insuffisant, y compris pour l’arrosage manuel et les tests. Le test de la pompe et du relais dure au maximum 3 secondes.
- Feu : appliquer les conditions de EF10 à EF13, avec priorité au rouge sur le jaune ; seuils de lumière de 3,6 h et 6 h. Ne pas reprendre l’ancien seuil jaune de 4,8 h.
- Interface : respecter les mesures et horodatages affichés, le graphique humidité/température à deux axes, le graphique de luminosité, les historiques, les contrôles et la persistance des paramètres définis dans les exigences.

Horodater chaque mesure à l’acquisition, conserver cet horodatage dans le payload MQTT et dans le fichier de sortie, et documenter le format et le fuseau horaire. Vérifier l’intervalle minimal du matériel dans sa documentation avant de changer la fréquence de lecture. Ne pas inventer une conversion en pourcentage pour l’humidité : documenter la calibration utilisée.

Gérer les erreurs de base : capteur non détecté, lecture invalide ou hors plage, connexion MQTT et écriture du fichier. Ne pas convertir une erreur en mesure valide ni en autorisation d’arrosage. Prévoir l’arrêt de la pompe à la fin de la durée prévue et lors de l’arrêt du programme.

## Matériel et dépendances

Consulter les statuts de l’inventaire avant de supposer qu’un composant est disponible. Documenter les alternatives effectivement utilisées. La référence du flotteur reste à vérifier : SENS-112-200 dans les exigences et SENS-112-250 dans le lien produit de l’inventaire.

Documenter les broches en précisant la numérotation BCM ou physique, le protocole, l’alimentation et les bus I2C/GPIO nécessaires. Ne pas affirmer qu’un branchement est validé sans vérification matérielle.

Maintenir les fichiers `requirements.txt` concernés à jour avec les bibliothèques utilisées. Documenter la création et l’activation du `.venv` et l’installation avec `python -m pip install -r requirements.txt` ; les instructions `uv` seules ne suffisent pas pour la remise. Ne pas versionner le `.venv` ; il doit être présent dans l’environnement de démonstration.

## Documentation et vérification

Après une modification de comportement ou de lancement, mettre à jour les README concernés : objectif, spécifications corrigées, matériel utilisé, installation, lancement de la collecte, broker, topics, payloads, emplacement et consultation des données. Garder les documents en français correct et utiliser la terminologie du domaine avec précision.

Vérifier ce qui est pertinent pour la modification :

- cohérence des fréquences, unités, seuils et durées avec les exigences ;
- horodatage conservé de l’acquisition à l’enregistrement ;
- publication, abonnement et enregistrement MQTT sans perte observable pendant l’essai ;
- conditions de déclenchement et de refus des actionneurs ;
- erreurs de base et arrêt de la pompe ;
- commandes d’installation et de lancement documentées.

Utiliser des tests ciblés et des simulations lorsque le matériel n’est pas accessible. Indiquer les vérifications effectuées et ce qui reste à valider sur le Raspberry Pi. Ne pas prétendre qu’un test logiciel valide le montage physique. La grille d’évaluation détaillée est encore à venir ; ne pas inventer de pondérations supplémentaires.
