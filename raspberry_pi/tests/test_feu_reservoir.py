"""Vérification logicielle d'EF12 avec GPIO et composants simulés."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

RACINE_PI = Path(__file__).resolve().parents[1]


@pytest.fixture
def programme(monkeypatch):
    monkeypatch.syspath_prepend(str(RACINE_PI))
    spec = importlib.util.spec_from_file_location('config', RACINE_PI / 'config.py')
    configuration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(configuration)
    monkeypatch.setitem(sys.modules, 'config', configuration)
    gpio = Mock()
    monkeypatch.setitem(sys.modules, 'gpiozero', SimpleNamespace(Button=Mock(), TrafficLights=gpio))
    # Charger le main comme pour python main.py, sans lancer son point d'entrée.
    spec = importlib.util.spec_from_file_location('collecte_demo', RACINE_PI / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(sys.modules['actionneurs.feu_tricolore'], 'TrafficLights', gpio)
    return module, gpio


def test_reservoir_insuffisant_declenche_rouge(programme):
    module, _ = programme
    feu = Mock()
    module.mettre_a_jour_feu(feu, {'etat': 'insuffisant', 'vide': True})
    feu.allumer_rouge.assert_called_once()
    feu.allumer_vert.assert_not_called()


def test_reservoir_suffisant_eteint_sans_deduire_vert(programme):
    module, _ = programme
    feu = Mock()
    module.mettre_a_jour_feu(feu, {'etat': 'suffisant', 'vide': False})
    feu.eteindre.assert_called_once()
    feu.allumer_vert.assert_not_called()
    feu.allumer_jaune.assert_not_called()


@pytest.mark.parametrize('mesure', [{}, {'etat': 'suffisant', 'vide': True}])
def test_mesure_invalide_ne_declenche_pas_de_couleur(programme, mesure):
    module, _ = programme
    feu = Mock()
    with pytest.raises(ValueError):
        module.mettre_a_jour_feu(feu, mesure)
    assert not feu.mock_calls


def test_publication_conserve_horodatage_et_vide_liste(programme):
    import threading
    module, _ = programme
    mesure = {'etat': 'insuffisant', 'vide': True,
              'horodatage': '2026-10-20T14:00:00+00:00'}
    module.verrou = threading.Lock()
    module.arret = threading.Event()
    module.arret.set()
    module.mesures_en_attente = [mesure]
    module.publicateur = Mock()
    # L'arrêt doit vider les acquisitions restantes, sans attendre 10 secondes.
    module.boucle_publication()
    module.publicateur.publier.assert_called_once_with(module.config.TOPIC_EAU, mesure)
    assert module.mesures_en_attente == []
    module.boucle_publication()
    assert module.publicateur.publier.call_count == 1


def test_erreur_mqtt_signale_arret_du_thread_principal(programme):
    import threading
    module, _ = programme
    module.verrou = threading.Lock()
    module.arret = Mock()
    module.arret.wait.return_value = False
    module.mesures_en_attente = [{'etat': 'insuffisant'}]
    module.publicateur = Mock()
    module.publicateur.publier.side_effect = ConnectionError('Broker inaccessible')
    module.boucle_publication()
    module.arret.set.assert_called_once()
    module.arret.wait.assert_called_once_with(module.config.PERIODE_PUBLICATION)


def test_feu_eteint_et_libere_gpio(programme):
    module, gpio = programme
    feu = module.FeuCirculation(23, 22, 27)
    gpio.assert_called_once_with(red=23, amber=22, green=27)
    feu.allumer_rouge()
    assert gpio.return_value.value == (1, 0, 0)
    feu.fermer()
    gpio.return_value.off.assert_called_once()
    gpio.return_value.close.assert_called_once()


def test_erreur_connexion_libere_feu_et_flotteur(programme, monkeypatch):
    module, _ = programme
    flotteur, feu, publicateur = Mock(), Mock(), Mock()
    monkeypatch.setattr(module, 'Flotteur', Mock(return_value=flotteur))
    monkeypatch.setattr(module, 'FeuCirculation', Mock(return_value=feu))
    monkeypatch.setattr(module, 'PublicateurMQTT', Mock(return_value=publicateur))
    publicateur.connecter.side_effect = ConnectionError('Broker inaccessible')
    with pytest.raises(ConnectionError):
        module.main()
    publicateur.deconnecter.assert_called_once()
    feu.fermer.assert_called_once()
    flotteur.fermer.assert_called_once()


def test_arret_attend_thread_avant_liberation(programme, monkeypatch):
    module, _ = programme
    flotteur, feu, publicateur, arret, thread = Mock(), Mock(), Mock(), Mock(), Mock()
    arret.is_set.return_value = True
    thread.ident = 1
    monkeypatch.setattr(module, 'Flotteur', Mock(return_value=flotteur))
    monkeypatch.setattr(module, 'FeuCirculation', Mock(return_value=feu))
    monkeypatch.setattr(module, 'PublicateurMQTT', Mock(return_value=publicateur))
    monkeypatch.setattr(module.threading, 'Event', Mock(return_value=arret))
    monkeypatch.setattr(module.threading, 'Thread', Mock(return_value=thread))
    appels = Mock()
    for objet, nom in [(thread, 'thread'), (feu, 'feu'), (flotteur, 'flotteur'),
                       (publicateur, 'mqtt')]:
        appels.attach_mock(objet, nom)
    module.main()
    noms = [appel[0] for appel in appels.mock_calls]
    assert noms.index('thread.join') < noms.index('mqtt.deconnecter')
    assert noms.index('thread.join') < noms.index('feu.fermer')
    thread.join.assert_called_once()
    feu.fermer.assert_called_once()
    flotteur.fermer.assert_called_once()


def test_acquisition_principale_et_publication_dans_thread_distinct(programme, monkeypatch):
    import threading
    module, _ = programme
    principal = threading.get_ident()
    lectures, publications = [], []
    mesure = {'etat': 'insuffisant', 'vide': True,
              'horodatage': '2026-10-20T14:00:00+00:00'}
    flotteur, feu, publicateur = Mock(), Mock(), Mock()
    flotteur.periode_lecture = 0.001
    def lire():
        lectures.append(threading.get_ident())
        if len(lectures) > 2:
            raise KeyboardInterrupt
        return mesure.copy()
    def publier(topic, payload):
        publications.append((threading.get_ident(), payload.copy()))
    flotteur.lire.side_effect = lire
    publicateur.publier.side_effect = publier
    monkeypatch.setattr(module, 'Flotteur', Mock(return_value=flotteur))
    monkeypatch.setattr(module, 'FeuCirculation', Mock(return_value=feu))
    monkeypatch.setattr(module, 'PublicateurMQTT', Mock(return_value=publicateur))
    monkeypatch.setattr(module.config, 'PERIODE_PUBLICATION', 0.001)
    module.main()
    assert all(ident == principal for ident in lectures)
    assert len(publications) == 2
    assert all(ident != principal for ident, payload in publications)
    assert all(payload == mesure for ident, payload in publications)
    assert feu.allumer_rouge.call_count == 2
    feu.fermer.assert_called_once()
    publicateur.deconnecter.assert_called_once()


def test_pilotes_i2c_recoivent_bus_et_heritent_capteur(programme, monkeypatch):
    from capteurs import Capteur, CapteurLumiere, SoilSensor
    bus = object()
    creer_lumiere = Mock(return_value=SimpleNamespace(lux=12345))
    creer_sol = Mock(return_value=SimpleNamespace(get_temp=lambda: 22,
                                                  moisture_read=lambda: 600))
    monkeypatch.setitem(sys.modules, 'adafruit_bh1750', SimpleNamespace(BH1750=creer_lumiere))
    monkeypatch.setitem(sys.modules, 'adafruit_seesaw', SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'adafruit_seesaw.seesaw', SimpleNamespace(Seesaw=creer_sol))
    lumiere = CapteurLumiere(bus)
    sol = SoilSensor(bus)
    assert isinstance(lumiere, Capteur) and isinstance(sol, Capteur)
    creer_lumiere.assert_called_once_with(bus)
    creer_sol.assert_called_once_with(bus, addr=0x36)
    assert lumiere.periode_lecture == 60
    assert sol.periode_lecture == 600
    assert lumiere.lire()['lux'] == 12345
    mesure = sol.lire()
    assert mesure['temperature_c'] == 22
    assert mesure['humidite_brute'] == 600
    assert 'humidite_pct' not in mesure
    assert mesure['horodatage'].endswith('+00:00')
