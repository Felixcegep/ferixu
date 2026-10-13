# Documentation du projet — Pousse / Ferixu

**Projet :** Système d’irrigation automatique pour plante en pot  
**Équipe :** Ferixu

- [Remise — Partie 1 (10 %), le 20 octobre 2026](remise_partie_1.md)
- [À faire au prochain cours : priorités et fonctions manquantes](todo_prochain_cours.md)
- [Inventaire du matériel : quantités, liens produits et statuts](inventaire_materiel.md)
- [Exigences fonctionnelles EF01 à EF24, états du feu et contrôles](exigences_fonctionnelles.md)

Ces documents décrivent le système prévu. L’état actuel de l’implémentation est présenté dans le [README du dépôt](../README.md).

## Composants et utilité

| Nº | Composant | Type | Utilité |
| --- | --- | --- | --- |
| 1 | STEMMA Soil Sensor (#4026) | Capteur | Mesure l’humidité et la température du sol |
| 2 | BH1750 (#4681) | Capteur | Mesure la luminosité ambiante en lux |
| 3 | Raspberry Pi 4 | Contrôleur | Lit les capteurs, applique les règles et contrôle les actionneurs |
| 4 | Feu tricolore ARD-625 | Actionneur / indicateur | Affiche l’état du système : vert, jaune ou rouge |
| 5 | Pompe submersible 3 V (#4547) | Actionneur | Arrose automatiquement la plante |
| 6 | Interrupteur à flotteur SENS-112-200 | Capteur | Détecte si le réservoir contient suffisamment d’eau |
| 7 | Relais STEMMA (#4409) | Actionneur / interface | Permet au Raspberry Pi d’allumer et d’éteindre la pompe |
| Optionnel | Buzzer passif | Actionneur | Produit une alerte sonore lorsque le réservoir est vide ou lorsqu’une intervention est nécessaire |

La différence de référence du flotteur est signalée dans l’[inventaire](inventaire_materiel.md).

## Plante et paramètres choisis

| Élément | Choix |
| --- | --- |
| Plante | Basilic |
| Besoin principal | Eau et lumière |
| Humidité minimale choisie | 30 % |
| Mesure de l’humidité | Toutes les 10 minutes |
| Arrosage automatique | Pompe activée pendant 3 secondes sous 30 %, sous réserve des conditions de sécurité EF06 à EF09 |
| Luminosité | Mesurée avec le BH1750 en lux |

Les tableaux peuvent être copiés depuis l’aperçu Markdown ou GitHub dans Google Docs.
