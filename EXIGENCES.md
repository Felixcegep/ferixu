# Exigences fonctionnelles — Pousse

## Liens importants

- [Dossier Google Drive du projet](https://drive.google.com/drive/u/1/folders/1ra_aOinUYsP94G0czu8sHVF1TeXjjfa6)
- [Page Notion « Projet — Link important »](https://app.notion.com/p/Projet-Link-important-3ea81a9a2ae3806781cceb5b11109b18)

## Exigences fonctionnelles

| Nº | Exigence fonctionnelle | Capteur / actionneur concerné |
| --- | --- | --- |
| EF01 | Le système doit mesurer l’humidité du sol en pourcentage (%) toutes les 10 minutes. | STEMMA Soil Sensor (#4026) |
| EF02 | Le système doit mesurer la température du sol en degrés Celsius (°C) toutes les 10 minutes. | STEMMA Soil Sensor (#4026) |
| EF03 | Le système doit mesurer la luminosité ambiante en lux toutes les 10 minutes. | BH1750 (#4681) |
| EF04 | Le système doit considérer qu’une période est suffisamment lumineuse lorsque le capteur mesure au moins 10 000 lux. Le système doit cumuler la durée pendant laquelle cette condition est respectée durant la journée. | BH1750 (#4681) |
| EF05 | Le système doit vérifier toutes les 10 minutes si le réservoir contient suffisamment d’eau. L’état doit être enregistré comme « suffisant » ou « insuffisant ». | Interrupteur à flotteur SENS-112-200 |
| EF06 | Lorsque l’humidité du sol descend sous 30 %, le système doit activer le relais et faire fonctionner la pompe pendant 3 secondes. | STEMMA Soil Sensor + relais STEMMA (#4409) + pompe 3 V (#4547) |
| EF07 | Le système ne doit jamais activer la pompe si l’interrupteur à flotteur indique que le niveau d’eau du réservoir est insuffisant. | Interrupteur à flotteur + relais + pompe |
| EF08 | Après un arrosage automatique, le système doit attendre au moins 30 minutes avant de permettre un nouvel arrosage automatique, même si l’humidité est encore sous 30 %. | Raspberry Pi 4 + relais + pompe |
| EF09 | Le système doit limiter le nombre d’arrosages automatiques à 6 arrosages de 3 secondes par période de 24 heures afin de réduire le risque de surarrosage en cas d’anomalie. | Raspberry Pi 4 + relais + pompe |
| EF10 | Le feu doit afficher vert lorsque l’humidité du sol est de 40 % ou plus, que la plante a reçu au moins 6 heures de lumière suffisante dans la journée et que le réservoir contient de l’eau. | STEMMA Soil Sensor + BH1750 + flotteur + feu ARD-625 |
| EF11 | Le feu doit afficher jaune lorsque l’humidité du sol est comprise entre 30 % et 39 %, ou lorsque la plante a reçu moins de 4,8 heures de lumière suffisante dans la journée. | STEMMA Soil Sensor + BH1750 + feu ARD-625 |
| EF12 | Le feu doit afficher rouge lorsque l’humidité du sol descend sous 30 %, lorsque la plante a reçu moins de 3,6 heures de lumière suffisante dans la journée, ou lorsque le réservoir est vide. | STEMMA Soil Sensor + BH1750 + flotteur + feu ARD-625 |
| EF13 | Lorsque les conditions d’alerte disparaissent, le feu doit automatiquement revenir à la couleur correspondant au nouvel état de la plante lors de la prochaine lecture des capteurs. | Feu tricolore ARD-625 |
| EF14 | L’application doit permettre à l’utilisateur de forcer manuellement un arrosage de 3 secondes à l’aide d’un bouton « Arroser maintenant ». L’arrosage manuel doit être bloqué si le réservoir est vide. | Relais STEMMA + pompe + interrupteur à flotteur |
| EF15 | L’application doit permettre à l’utilisateur d’activer ou de désactiver le mode d’arrosage automatique. Lorsque le mode automatique est désactivé, aucune activation automatique de la pompe ne doit être effectuée. | Raspberry Pi 4 + relais + pompe |
| EF16 | L’application doit permettre de tester manuellement le relais et la pompe à l’aide d’un bouton de test. Le test doit durer 3 secondes maximum et être refusé si le réservoir est vide. | Relais STEMMA + pompe + interrupteur à flotteur |
| EF17 | L’application doit permettre de tester manuellement le feu tricolore en activant successivement les couleurs verte, jaune et rouge. | Feu tricolore ARD-625 |
| EF18 | L’application doit afficher en temps réel la dernière valeur d’humidité du sol (%), la température du sol (°C), la luminosité (lux) et l’état du niveau d’eau du réservoir. | STEMMA Soil Sensor + BH1750 + interrupteur à flotteur |
| EF19 | L’application doit afficher un graphique de l’humidité du sol (%) en fonction du temps. | STEMMA Soil Sensor |
| EF20 | L’application doit afficher un graphique de la luminosité (lux) en fonction du temps. | BH1750 |
| EF21 | L’application doit afficher un graphique de la température du sol (°C) en fonction du temps. | STEMMA Soil Sensor |
| EF22 | L’application doit afficher le nombre total d’heures de lumière suffisante reçues durant la journée, avec un objectif quotidien situé entre 6 et 8 heures. | BH1750 |
| EF23 | L’application doit afficher la date et l’heure du dernier arrosage, ainsi que le nombre d’arrosages effectués durant les dernières 24 heures. | Raspberry Pi 4 + relais + pompe |
| EF24 | L’application doit permettre à l’utilisateur de modifier le seuil minimal d’humidité, le seuil de luminosité et la durée d’arrosage, puis d’enregistrer ces paramètres. | Raspberry Pi 4 + interface utilisateur |

## États du feu tricolore

| Couleur | État | Condition |
| --- | --- | --- |
| 🟢 Vert | Normal | Humidité ≥ 40 %, lumière suffisante et réservoir avec eau. |
| 🟡 Jaune | À surveiller | Humidité entre 30 et 39 % ou moins de 4,8 h de lumière suffisante. |
| 🔴 Rouge | Urgent | Humidité < 30 %, moins de 3,6 h de lumière suffisante ou réservoir vide. |

Les seuils de 4,8 heures et 3,6 heures correspondent respectivement à 80 % et 60 % de l’objectif minimal de 6 heures de lumière par jour.

## Données affichées dans l’application

L’utilisateur pourra consulter :

- l’humidité actuelle du sol en % ;
- la température actuelle du sol en °C ;
- la luminosité actuelle en lux ;
- le nombre d’heures de lumière suffisante reçues durant la journée ;
- l’état du réservoir : suffisant / insuffisant ;
- l’état actuel du système : normal / à surveiller / urgent ;
- la date et l’heure du dernier arrosage ;
- le nombre d’arrosages effectués durant les dernières 24 heures ;
- un graphique de l’humidité du sol ;
- un graphique de la luminosité ;
- un graphique de la température du sol.

## Contrôles manuels

L’utilisateur pourra :

- appuyer sur « Arroser maintenant » pour déclencher la pompe pendant 3 secondes ;
- activer ou désactiver l’arrosage automatique ;
- tester la pompe et le relais ;
- tester les trois couleurs du feu tricolore ;
- modifier certains seuils du système.

Même en mode manuel, la pompe ne pourra pas fonctionner lorsque l’interrupteur à flotteur indique que le réservoir est vide.
