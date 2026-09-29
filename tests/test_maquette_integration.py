"""Test d’intégration Playwright de l’UI NiceGUI et export des captures plein écran.

Lancez `uv run pytest -q tests/test_maquette_integration.py` ou directement
`uv run python tests/test_maquette_integration.py`. Le serveur doit tourner sur
http://127.0.0.1:8080.
"""
from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "maquettes"
BASE_URL = "http://127.0.0.1:8080"
BRAVE = Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser")


def screenshot(page: Page, name: str) -> Path:
    path = OUTPUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    if not path.is_file():
        raise AssertionError(f"La capture n’a pas été créée : {path}")
    width, height = png_dimensions(path)
    if width < 1100 or height < 700 or path.stat().st_size < 30_000:
        raise AssertionError(
            f"Capture trop petite ou vide: {path} ({width}x{height}, {path.stat().st_size} octets)"
        )
    print(f"CAPTURE {path.relative_to(ROOT)} — {width}x{height}, {path.stat().st_size:,} octets")
    return path


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(f"Fichier PNG invalide: {path}")
    return struct.unpack(">II", header[16:24])


def wait_for_chart_data(page: Page) -> None:
    # ECharts utilise un canvas distinct par graphique dans cette maquette.
    expect(page.locator(".nicegui-echart canvas")).to_have_count(3, timeout=15_000)
    color_counts = page.locator(".nicegui-echart canvas").evaluate_all(
        """canvases => canvases.map(canvas => {
            const context = canvas.getContext('2d');
            if (!context || !canvas.width || !canvas.height) return 0;
            const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
            const colors = new Set();
            for (let i = 0; i < pixels.length; i += 160) {
                if (pixels[i + 3] > 0) colors.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
            }
            return colors.size;
        })"""
    )
    if any(count < 6 for count in color_counts):
        raise AssertionError(f"Un graphique semble vide ou sans tracé (couleurs par canvas : {color_counts})")
    for expected in ("Humidité du sol", "Luminosité", "Température du sol"):
        expect(page.locator(".charts").get_by_text(expected, exact=True)).to_be_visible()


def assert_notification(page: Page, text: str) -> None:
    expect(page.get_by_text(text, exact=False).last).to_be_visible(timeout=5_000)


def confirm_dialog(page: Page, capture: str | None = None) -> None:
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog.get_by_role("button", name="Annuler")).to_be_visible()
    confirm = dialog.get_by_role("button", name="Confirmer")
    expect(confirm).to_be_visible()
    if capture:
        screenshot(page, capture)
    confirm.click()


def current_watering_count(page: Page) -> int:
    match = re.search(r"(\d+) / 6 arrosages sur 24 h", page.locator("body").inner_text())
    if match is None:
        raise AssertionError("Le compteur d’arrosages est absent de la page d’accueil")
    return int(match.group(1))


def expect_last_watering_date(page: Page) -> None:
    date_pattern = re.compile(r"\d{2}/\d{2}/\d{4} à \d{2} h \d{2}")
    expect(page.get_by_text(date_pattern)).to_be_visible()


def run() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    browser_errors: list[str] = []
    failed_requests: list[str] = []
    with sync_playwright() as playwright:
        launch_options = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        }
        if BRAVE.is_file():
            launch_options["executable_path"] = str(BRAVE)
            print(f"Navigateur : Brave ({BRAVE})")
        else:
            print("Navigateur : Chromium Playwright (installez-le avec `uv run playwright install chromium` si nécessaire)")
        browser = playwright.chromium.launch(**launch_options)
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page.on("pageerror", lambda error: browser_errors.append(str(error)))
        page.on("console", lambda msg: browser_errors.append(f"console: {msg.text}") if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.url}: {req.failure}"))

        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError(f"La maquette ne répond pas correctement: {response.status if response else 'aucune réponse'}")
        expect(page.get_by_text("Ma plante en pot", exact=True)).to_be_visible()

        # État normal : mesures, mode auto et trois graphiques avec données.
        expect(page.get_by_text("Votre plante se porte bien", exact=True)).to_be_visible()
        expect(page.get_by_text("46", exact=True)).to_be_visible()
        expect(page.get_by_text("21,8", exact=True)).to_be_visible()
        expect(page.get_by_text("12 840", exact=True)).to_be_visible()
        expect_last_watering_date(page)
        wait_for_chart_data(page)
        screenshot(page, "etat-normal")

        # État urgent : chaque scénario est désormais une page distincte.
        response = page.goto(f"{BASE_URL}/alerte", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /alerte ne répond pas correctement")
        expect(page.get_by_text("Intervention nécessaire", exact=True)).to_be_visible()
        expect(page.get_by_text("URGENT", exact=False).first).to_be_visible()
        expect(page.get_by_text("24", exact=True)).to_be_visible()
        expect(page.get_by_text("Insuffisant", exact=True)).to_be_visible()
        wait_for_chart_data(page)
        screenshot(page, "etat-alerte")

        # État jaune, compris entre l’état normal et l’urgence.
        response = page.goto(f"{BASE_URL}/surveillance", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /surveillance ne répond pas correctement")
        expect(page.get_by_text("Plante à surveiller", exact=True)).to_be_visible()
        expect(page.get_by_text("● À SURVEILLER", exact=True)).to_be_visible()
        expect(page.get_by_text("🟡 Jaune · à surveiller", exact=True)).to_be_visible()
        screenshot(page, "etat-surveillance")

        # Mode auto sur les contrôles, puis capture de la page en état normal.
        response = page.goto(f"{BASE_URL}/controles", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /controles ne répond pas correctement")
        expect(page.get_by_role("button", name="Arroser maintenant")).to_be_visible()
        expect(page.get_by_text("Tester le relais et la pompe", exact=True)).to_be_visible()
        expect(page.get_by_text("Tester le feu tricolore", exact=True)).to_be_visible()
        expect(page.get_by_text("Mode automatique", exact=True)).to_be_visible()
        screenshot(page, "controles-manuels")
        toggle = page.locator(".q-toggle")
        expect(toggle).to_be_visible()
        if toggle.get_attribute("aria-checked") != "true":
            raise AssertionError("Le mode automatique devrait être activé au départ")
        toggle.click()
        assert_notification(page, "Mode automatique désactivé.")
        expect(toggle).to_have_attribute("aria-checked", "false")
        toggle.click()
        assert_notification(page, "Mode automatique activé.")
        expect(toggle).to_have_attribute("aria-checked", "true")

        # Le test pompe est confirmé sans incrémenter le compteur d’arrosage.
        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route / ne répond pas pour vérifier le compteur")
        count_before = current_watering_count(page)
        response = page.goto(f"{BASE_URL}/controles", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /controles ne répond pas pour tester la pompe")
        pump_card = page.locator(".control-card").filter(has_text="Tester le relais et la pompe")
        pump_card.get_by_role("button", name="Lancer le test").click()
        expect(page.get_by_text("Confirmer le test de la pompe ?", exact=True)).to_be_visible()
        confirm_dialog(page)
        assert_notification(page, "Test de la pompe simulé")
        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route / ne répond pas après le test de pompe")
        if current_watering_count(page) != count_before:
            raise AssertionError("Le test de pompe ne doit pas incrémenter le compteur d’arrosage")

        # Un arrosage manuel réussi doit incrémenter le compteur de un.
        response = page.goto(f"{BASE_URL}/controles", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /controles ne répond pas pour tester l’arrosage")
        page.get_by_role("button", name="Arroser maintenant").click()
        expect(page.get_by_text("Confirmer l’arrosage ?", exact=True)).to_be_visible()
        confirm_dialog(page, "confirmation-arrosage")
        assert_notification(page, "Arrosage manuel simulé")
        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route / ne répond pas après l’arrosage manuel")
        if current_watering_count(page) != count_before + 1:
            raise AssertionError("Un arrosage manuel réussi doit ajouter un arrosage au compteur")
        expect_last_watering_date(page)

        # Le test du feu affiche aussi une confirmation avant son animation.
        response = page.goto(f"{BASE_URL}/controles", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /controles ne répond pas pour tester le feu")
        light_card = page.locator(".control-card").filter(has_text="Tester le feu tricolore")
        light_card.get_by_role("button", name="Lancer le test").click()
        expect(page.get_by_text("Confirmer le test du feu ?", exact=True)).to_be_visible()
        confirm_dialog(page)
        assert_notification(page, "Séquence du feu terminée.")
        expect(light_card.get_by_text("état : Test terminé", exact=False)).to_be_visible()

        # Le scénario réservoir vide doit refuser l’action de la pompe.
        response = page.goto(f"{BASE_URL}/controles?reservoir=vide", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /controles?reservoir=vide ne répond pas correctement")
        expect(page.get_by_text("la pompe reste bloquée", exact=False)).to_be_visible()
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.get_by_role("button", name="Arroser maintenant").click()
        assert_notification(page, "Action refusée : niveau d’eau insuffisant.")

        # Enregistrement des paramètres et vérification de leur usage dans le tableau.
        response = page.goto(f"{BASE_URL}/parametres", wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route /parametres ne répond pas correctement")
        expect(page.get_by_text("Paramètres du système", exact=True)).to_be_visible()
        page.get_by_label("Seuil (%)").fill("35")
        page.get_by_label("Seuil (lux)").fill("12000")
        page.get_by_label("Durée (secondes)").fill("2")
        page.get_by_role("button", name="Enregistrer les paramètres").click()
        assert_notification(page, "Paramètres enregistrés dans la maquette.")
        expect(page.get_by_label("Seuil (%)")).to_have_value("35")
        expect(page.get_by_label("Seuil (lux)")).to_have_value("12000")
        expect(page.get_by_label("Durée (secondes)")).to_have_value("2")
        screenshot(page, "parametres")
        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or not response.ok:
            raise AssertionError("La route / ne répond pas correctement après l’enregistrement")
        expect(page.get_by_text("Arrosage sous 35 %", exact=True)).to_be_visible()
        expect(page.get_by_text("Lumière suffisante dès 12 000 lux", exact=True)).to_be_visible()

        browser.close()

    if browser_errors:
        raise AssertionError("Erreurs navigateur/application:\n- " + "\n- ".join(browser_errors))
    # Les échecs de polices distantes n’interrompent pas le rendu des captures;
    # ils sont rapportés pour distinguer une limite réseau d’une erreur d’application.
    if failed_requests:
        print("REQUÊTES ÉCHOUÉES:")
        for item in failed_requests:
            print(f"- {item}")
    print("OK — parcours testés: états normal/jaune/urgent, graphiques, confirmations, arrosage bloqué, compteur, mode automatique, paramètres.")


def test_maquette_integration() -> None:
    """Exerce l’interface réelle et vérifie les six captures produites."""
    run()


if __name__ == "__main__":
    try:
        test_maquette_integration()
    except (AssertionError, FileNotFoundError, PlaywrightTimeoutError) as error:
        print(f"ÉCHEC: {error}", file=sys.stderr)
        raise
