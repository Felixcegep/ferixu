# Remise du projet — Partie 1 (10 %)

**Date de remise : 20 octobre 2026**  
**Présentation :** en équipe, en classe, le jour de la remise.  
**Grille d’évaluation détaillée :** à venir.

## Travail à remettre

La première partie du projet de session comprend le code source des objets connectés disponibles (capteurs et actionneurs), incluant :

- les scripts d’acquisition de données ;
- la logique de publication et d’abonnement MQTT ;
- la logique de déclenchement des actionneurs.

## Exigences techniques

### Structure et environnement

Le projet doit respecter les bonnes pratiques de structuration vues en classe : un environnement virtuel `.venv` et un fichier `requirements.txt` à jour listant les bibliothèques utilisées.

### Contenu du README

Le README doit décrire :

- l’objectif du projet ;
- la liste des spécifications corrigées et à jour ;
- les capteurs et actionneurs utilisés ;
- les instructions d’installation : création du `.venv` et installation des dépendances avec `requirements.txt` ;
- la façon de lancer la collecte de données et l’endroit où consulter les données.

### Modélisation et acquisition

Les capteurs et actionneurs doivent être modélisés en programmation orientée objet, avec des classes, propriétés et méthodes appropriées. Les autres notions d’orienté objet doivent être appliquées selon les besoins du projet : si plusieurs capteurs partagent des propriétés ou méthodes communes, utiliser une classe abstraite et/ou l’héritage.

Chaque mesure acquise doit être horodatée. La fréquence de lecture de chaque capteur doit respecter l’intervalle minimal imposé par le matériel.

## Présentation et démonstration

La présentation sert à valider le montage physique, l’acquisition des données et leur transmission via MQTT. L’équipe doit démontrer :

1. Le branchement physique des capteurs et actionneurs sur le Raspberry Pi, avec un montage visible et fonctionnel.
2. L’acquisition de données en temps réel à partir d’au moins un capteur.
3. La publication de ces données vers le broker MQTT local.
4. La réception et l’enregistrement de ces données dans un fichier, à partir du broker.
5. Le déclenchement d’au moins un actionneur selon une condition prévue dans les exigences fonctionnelles. Le déclenchement peut être réel ou simulé si la condition ne peut pas être reproduite facilement en direct.

## Critères d’évaluation

### Analyse, préparation de l’environnement et connexion des objets (00SX.1, 00SX.2)

- Le montage physique correspond aux exigences fonctionnelles définies à l’étape de planification.
- Chaque capteur et actionneur est correctement identifié et branché selon les bonnes pratiques vues en cours : broches appropriées, protocole respecté et alimentation adéquate.
- L’environnement de développement est fonctionnel : environnement virtuel Python, dépendances installées et bus I2C/GPIO activés selon le cas.
- L’environnement virtuel et le fichier `requirements.txt` sont présents et à jour.

### Programmation rigoureuse de la logique applicative de l’objet (00SX.4)

- Le code d’acquisition reflète les exigences fonctionnelles définies : fréquence de lecture, unité et seuils. La fréquence de lecture respecte l’intervalle minimal du matériel.
- Les mesures acquises sont horodatées.
- La logique de déclenchement des actionneurs respecte les conditions précisées à l’étape de planification : seuils et durée.
- Le code est structuré de façon cohérente, avec une séparation claire entre acquisition, logique de décision et communication MQTT.
- La communication MQTT fonctionne correctement : publication des données acquises, abonnement et écriture dans un fichier, sans perte de données observable.
- Le code gère les cas d’erreur de base, par exemple un capteur non détecté ou une valeur hors plage.
- La modélisation orientée objet des capteurs et actionneurs est appropriée : classes, propriétés, méthodes, héritage ou classes abstraites lorsque pertinent.

### Documentation, terminologie, orthographe et grammaire (00SX.7)

- Le code est commenté de façon pertinente : méthodes et commentaires expliquant les lignes de code, constantes, valeurs ou éléments dont la logique n’est pas évidente à la simple lecture.
- Le README décrit l’objectif du projet, les capteurs et actionneurs utilisés, l’installation du `.venv` et des dépendances via `requirements.txt`, le lancement de la collecte et l’endroit où consulter les données.
- La terminologie du domaine est utilisée correctement : broker, topic, payload, seuil, GPIO et I2C.
- Toute la documentation remise, y compris le README et les commentaires, est rédigée dans un français correct, sans fautes majeures d’orthographe ou de grammaire.

## Documents du projet associés

- [Exigences fonctionnelles corrigées EF01 à EF24](exigences_fonctionnelles.md)
- [Inventaire du matériel et statuts de réception](inventaire_materiel.md)
- [Composants et fiche du basilic](README.md)
- [Installation et collecte sur le Raspberry Pi](../raspberry_pi/README.md)

Ces consignes définissent les attentes de la remise ; elles ne constituent pas une validation de l’état actuel du code ou du montage.
