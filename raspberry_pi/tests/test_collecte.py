"""Tests sans GPIO : décisions, acquisition, erreurs et sécurité du relais."""
import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from raspberry_pi import config
from raspberry_pi.actionneurs import Pompe, FeuTricolore
from raspberry_pi.capteurs import CapteurLumiere, CapteurSol, Flotteur
from raspberry_pi.ingestion.service_ingestion import on_message, enregistrer_mesure
from raspberry_pi.logique_decision import mettre_a_jour_feu_reservoir
from raspberry_pi.main import collecter
from raspberry_pi.mesures import valider_mesure
from raspberry_pi.publication_donnees import PublicateurMQTT

DATE = "2026-10-20T14:30:00+00:00"


def eau(vide=False):
    return {"etat": "insuffisant" if vide else "suffisant",
            "vide": vide, "horodatage": DATE}


@pytest.fixture
def gpio(monkeypatch):
    sorties = []

    def sortie(*args, **kwargs):
        instance = Mock()
        sorties.append(instance)
        return instance

    monkeypatch.setitem(__import__('sys').modules, 'gpiozero',
                        SimpleNamespace(LED=sortie, OutputDevice=sortie,
                                        Button=sortie))
    return sorties


def test_flotteur_lit_et_horodate(gpio):
    flotteur = Flotteur()
    flotteur.bouton.is_pressed = True
    mesure = flotteur.lire()
    assert mesure['etat'] == 'insuffisant'
    valider_mesure(config.TOPIC_EAU, mesure)
    flotteur.bouton.is_pressed = False
    assert flotteur.lire()['etat'] == 'suffisant'
    flotteur.fermer()
    flotteur.bouton.close.assert_called_once()


def test_feu_rouge_prioritaire_et_aucun_vert_sans_autres_mesures():
    feu = Mock()
    mettre_a_jour_feu_reservoir(feu, eau(True))
    feu.allumer_rouge.assert_called_once()
    mettre_a_jour_feu_reservoir(feu, eau(False))
    feu.eteindre.assert_called_once()
    feu.allumer_vert.assert_not_called()
    feu.allumer_jaune.assert_not_called()


def test_feu_libere_toutes_les_broches(gpio):
    feu = FeuTricolore(27, 22, 23)
    feu.allumer_rouge()
    feu.del_rouge.on.assert_called_once()
    feu.del_verte.off.assert_called_once()
    feu.fermer()
    for sortie in gpio:
        sortie.close.assert_called_once()


def test_initialisation_partielle_feu_libere_gpio(monkeypatch):
    rouge = Mock()
    from sys import modules
    monkeypatch.setitem(modules, 'gpiozero', SimpleNamespace(
        LED=Mock(side_effect=[rouge, OSError('GPIO occupé')]))
    )
    with pytest.raises(OSError):
        FeuTricolore(27, 22, 23)
    rouge.close.assert_called_once()


@pytest.mark.parametrize('payload', [b'{', b'\xff', b'[]', b'{}',
    json.dumps({**eau(), 'vide': 0}).encode(),
    json.dumps({**eau(), 'horodatage': '2026-10-20T10:30:00'}).encode(),
    json.dumps({**eau(), 'etat': 'inconnu'}).encode()])
def test_ingestion_rejette_message_et_continue(payload, tmp_path, capsys):
    fichier = tmp_path / 'lectures.jsonl'
    on_message(None, fichier, SimpleNamespace(topic=config.TOPIC_EAU, payload=payload))
    assert not fichier.exists()
    on_message(None, fichier, SimpleNamespace(topic=config.TOPIC_EAU,
                                             payload=json.dumps(eau()).encode()))
    assert json.loads(fichier.read_text()) == eau()
    assert 'non enregistrée' in capsys.readouterr().err


def test_erreur_ecriture_ne_fait_pas_tomber_callback(tmp_path, capsys):
    on_message(None, tmp_path, SimpleNamespace(topic=config.TOPIC_EAU,
                                              payload=json.dumps(eau()).encode()))
    assert 'non enregistrée' in capsys.readouterr().err


def test_conservation_exacte_horodatage_et_valeurs(tmp_path):
    fichier = tmp_path / 'mesures.jsonl'
    enregistrer_mesure(config.TOPIC_EAU, json.dumps(eau()).encode(), fichier)
    assert json.loads(fichier.read_text()) == eau()


@pytest.mark.parametrize('valeur', [True, -1, float('nan'), float('inf'), '123', 10 ** 1000])
def test_lux_invalide_refuse(valeur):
    with pytest.raises(ValueError):
        valider_mesure(config.TOPIC_LUMIERE, {'lux': valeur, 'horodatage': DATE})


def test_bh1750_et_sol_sans_materiel(monkeypatch):
    from sys import modules
    monkeypatch.setitem(modules, 'adafruit_bh1750',
                        SimpleNamespace(BH1750=lambda bus: SimpleNamespace(lux=12000)))
    monkeypatch.setitem(modules, 'adafruit_seesaw', SimpleNamespace())
    monkeypatch.setitem(modules, 'adafruit_seesaw.seesaw', SimpleNamespace(
        Seesaw=lambda bus, addr: SimpleNamespace(get_temp=lambda: 22,
                                                moisture_read=lambda: 600)))
    lumiere = CapteurLumiere(object())
    assert lumiere.periode_lecture == 60
    assert lumiere.lire()['lux'] == 12000
    sol = CapteurSol(object())
    assert sol.periode_lecture == 600
    mesure = sol.lire()
    assert 'humidite_pct' not in mesure
    assert mesure['temperature_c'] == 22
    assert mesure['humidite_brute'] == 600
    sol = CapteurSol(object(), 200, 1000)
    assert sol.lire()['humidite_pct'] == 50
    sol.capteur.moisture_read = lambda: 1001
    with pytest.raises(ValueError, match='calibration'):
        sol.lire()


def test_ordonnanceur_respecte_60_et_600_secondes(monkeypatch):
    temps = [0.0]
    arret = threading.Event()
    comptes = {'eau': 0, 'lumiere': 0}
    appels = []
    class Attente:
        def is_set(self):
            return arret.is_set()
        def wait(self, delai):
            temps[0] += delai
            if temps[0] > 600:
                arret.set()
    def lire(nom):
        comptes[nom] += 1
        appels.append((nom, temps[0]))
        return eau() if nom == 'eau' else {'lux': 10000, 'horodatage': DATE}
    monkeypatch.setattr('raspberry_pi.main.time.monotonic', lambda: temps[0])
    taches = [(SimpleNamespace(periode_lecture=600, lire=lambda: lire('eau')), config.TOPIC_EAU),
              (SimpleNamespace(periode_lecture=60, lire=lambda: lire('lumiere')), config.TOPIC_LUMIERE)]
    collecter(taches, Mock(), Mock(), Attente())
    assert comptes == {'eau': 2, 'lumiere': 11}
    assert [t for n, t in appels if n == 'eau'] == [0, 600]
    assert [t for n, t in appels if n == 'lumiere'] == list(range(0, 601, 60))


def test_decision_appliquee_meme_si_mqtt_echoue():
    feu = Mock()
    publicateur = Mock()
    publicateur.publier.side_effect = ConnectionError('Broker déconnecté')
    with pytest.raises(ConnectionError):
        collecter([(SimpleNamespace(periode_lecture=600, lire=lambda: eau(True)),
                    config.TOPIC_EAU)], publicateur, feu, threading.Event(), True)
    feu.allumer_rouge.assert_called_once()


def test_publicateur_refuse_hors_connexion_et_payload_invalide():
    publicateur = PublicateurMQTT('test-sans-reseau')
    with pytest.raises(ConnectionError):
        publicateur.publier(config.TOPIC_EAU, eau())
    with pytest.raises(ValueError):
        publicateur.publier(config.TOPIC_EAU, {'vide': False})


@pytest.mark.parametrize('mesure', [eau(True), {'etat': 'suffisant'}, {}])
def test_pompe_refuse_eau_insuffisante_ou_invalide(gpio, mesure):
    pompe = Pompe(17, SimpleNamespace(lire=lambda: mesure), active_high=True)
    with pytest.raises(RuntimeError):
        pompe.arroser()
    pompe.relais.on.assert_not_called()
    pompe.fermer()


@pytest.mark.parametrize('duree', [0, -1, 3.1, True, float('nan')])
def test_pompe_refuse_duree_invalide(gpio, duree):
    pompe = Pompe(17, SimpleNamespace(lire=lambda: eau(), eau=True), active_high=True)
    with pytest.raises(ValueError):
        pompe.arroser(duree)
    pompe.relais.on.assert_not_called()
    pompe.fermer()


def test_pompe_coupe_sur_erreur_capteur_et_relit_apres(gpio):
    lectures = Mock(return_value=eau())
    class FlotteurEnErreur:
        lire = lectures
        @property
        def eau(self):
            raise OSError('Lecture perdue')
    pompe = Pompe(17, FlotteurEnErreur(), active_high=True)
    with pytest.raises(OSError):
        pompe.arroser()
    pompe.relais.off.assert_called_once()
    assert lectures.call_count == 2
    pompe.fermer()


def test_pompe_fin_de_duree_et_arret_definitif(gpio, monkeypatch):
    lectures = Mock(return_value=eau())
    pompe = Pompe(17, SimpleNamespace(lire=lectures, eau=True), active_high=True)
    monkeypatch.setattr('raspberry_pi.actionneurs.pompe.time.monotonic',
                        Mock(side_effect=[0, 3]))
    resultat = pompe.arroser()
    assert resultat == {'avant': eau(), 'apres': eau()}
    pompe.relais.on.assert_called_once()
    pompe.relais.off.assert_called_once()
    pompe.fermer()
    with pytest.raises(RuntimeError):
        pompe.arroser()
    pompe.relais.close.assert_called_once()
