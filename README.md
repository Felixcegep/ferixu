# Pousse — maquette NiceGUI

Maquette minimaliste en **cinq pages distinctes** pour l'application de surveillance et d'arrosage d'une plante en pot. Les données et actions sont simulées : aucun capteur, relais, pompe ou feu n'est commandé.

## Démarrer

```bash
uv sync
uv run python main.py
```

Ouvrir <http://localhost:8080>.

Les pages sont :

| Page | Adresse | Contenu |
| --- | --- | --- |
| État normal | `/` | Mesures, réservoir, feu, arrosages et trois graphiques |
| À surveiller | `/surveillance` | État jaune : situation à surveiller |
| État d’alerte | `/alerte` | Sol sec, lumière faible et réservoir insuffisant |
| Contrôles | `/controles` | Arrosage manuel, mode automatique, tests de pompe et du feu |
| Paramètres | `/parametres` | Seuils, durée et règles du feu |

Sur la page Contrôles, le bouton « Insuffisant » simule un réservoir vide. L’arrosage est alors refusé. Le test de la pompe ne compte pas comme un arrosage.

## Test d’intégration et captures

Lancez le serveur NiceGUI dans un terminal, puis le test dans un autre :

```bash
uv run python main.py
uv run pytest -q tests/test_maquette_integration.py
```

Le test pilote les pages réelles dans Brave headless s’il est installé à son emplacement macOS habituel. Sinon, installez Chromium Playwright avec `uv run playwright install chromium`. Il vérifie les mesures et graphiques, les états normal, jaune et urgent, le blocage si le réservoir est vide, les dialogues de confirmation, le mode automatique, la sauvegarde des paramètres et les compteurs après le test de pompe et un arrosage réussi. Il génère les captures PNG pleine page des cinq pages et du dialogue d’arrosage dans [`maquettes/`](maquettes/). Il échoue si une assertion UI échoue ou si une capture manque, est invalide ou n’a pas les dimensions attendues.

Le test peut aussi être lancé directement avec `uv run python tests/test_maquette_integration.py`.
