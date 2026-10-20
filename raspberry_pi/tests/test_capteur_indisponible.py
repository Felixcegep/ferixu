"""Pannes isolées, reconnexion et absence de mesure inventée."""
from contextlib import contextmanager
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from raspberry_pi import config
from raspberry_pi.capteurs.capteur_supervise import CapteurIndisponible, CapteurSupervise
from raspberry_pi.main import collecter, ouvrir_capteur_i2c
from raspberry_pi.actionneurs import Pompe

MESURE = {'etat': 'suffisant', 'vide': False,
          'horodatage': '2026-10-20T14:30:00+00:00'}


def test_absence_initiale_puis_reconnexion():
    ouvertures = []
    ferme = Mock()
    @contextmanager
    def ouvrir():
        ouvertures.append(True)
        if len(ouvertures) == 1:
            raise OSError('Aucune réponse sur 0x23')
        try:
            yield SimpleNamespace(lire=lambda: MESURE)
        finally:
            ferme()
    capteur = CapteurSupervise('test', 60, ouvrir)
    with pytest.raises(CapteurIndisponible):
        capteur.lire()
    assert not capteur.disponible
    assert capteur.lire() == MESURE
    assert capteur.disponible
    assert len(ouvertures) == 2
    capteur.fermer()
    capteur.fermer()
    ferme.assert_called_once()


@pytest.mark.parametrize('erreur', [OSError('débranché'), ValueError('valeur invalide'),
                                   ModuleNotFoundError('bibliothèque absente')])
def test_perte_en_lecture_invalide_ancienne_mesure_et_libere(erreur):
    lecture = Mock(side_effect=[MESURE, erreur])
    ferme = Mock()
    @contextmanager
    def ouvrir():
        try:
            yield SimpleNamespace(lire=lecture)
        finally:
            ferme()
    capteur = CapteurSupervise('test', 60, ouvrir)
    assert capteur.lire() == MESURE
    with pytest.raises(CapteurIndisponible):
        capteur.lire()
    assert not capteur.disponible
    ferme.assert_called_once()


def test_capteur_absent_ne_bloque_pas_les_autres_et_ne_publie_rien():
    @contextmanager
    def absent():
        raise OSError('Capteur absent')
        yield
    panne = CapteurSupervise('sol', 600, absent)
    sain = SimpleNamespace(lire=lambda: MESURE, periode_lecture=600)
    publicateur = Mock()
    collecter([(panne, config.TOPIC_SOL), (sain, config.TOPIC_EAU)],
              publicateur, None, threading.Event(), une_lecture=True)
    publicateur.publier.assert_called_once_with(config.TOPIC_EAU, MESURE)


def test_reessai_a_la_periode_normale_et_autres_capteurs_continuent(monkeypatch):
    temps = [0.0]
    lectures = []
    @contextmanager
    def absent():
        lectures.append(temps[0])
        raise OSError('Absent')
        yield
    panne = CapteurSupervise('réservoir', 600, absent)
    sain = SimpleNamespace(lire=lambda: {'lux': 1234}, periode_lecture=60)
    publicateur, feu = Mock(), Mock()
    class Attente:
        def is_set(self):
            return temps[0] > 600
        def wait(self, delai):
            temps[0] += delai
    monkeypatch.setattr('raspberry_pi.main.time.monotonic', lambda: temps[0])
    collecter([(panne, config.TOPIC_EAU), (sain, config.TOPIC_LUMIERE)],
              publicateur, feu, Attente())
    assert lectures == [0, 600]
    assert publicateur.publier.call_count == 11
    assert feu.allumer_rouge.call_count == 2
    feu.allumer_vert.assert_not_called()


def test_erreur_feu_ne_stoppe_pas_publication():
    feu = Mock()
    feu.allumer_rouge.side_effect = OSError('GPIO perdu')
    publicateur = Mock()
    capteur = SimpleNamespace(lire=lambda: {**MESURE, 'etat': 'insuffisant', 'vide': True},
                              periode_lecture=600)
    collecter([(capteur, config.TOPIC_EAU)], publicateur, feu, threading.Event(), True)
    publicateur.publier.assert_called_once()
    feu.fermer.assert_called_once()


def test_bus_libere_si_constructeur_capteur_echoue(monkeypatch):
    import sys
    from raspberry_pi import capteurs
    bus = Mock()
    monkeypatch.setitem(sys.modules, 'board', SimpleNamespace(SCL=1, SDA=2))
    monkeypatch.setitem(sys.modules, 'busio', SimpleNamespace(I2C=Mock(return_value=bus)))
    monkeypatch.setattr(capteurs, 'CapteurLumiere', Mock(side_effect=OSError('Non détecté')))
    with pytest.raises(OSError):
        with ouvrir_capteur_i2c('lumiere'):
            pytest.fail('Ne doit pas exposer un pilote invalide')
    bus.deinit.assert_called_once()


def test_interruption_non_masquee_et_ressources_liberees():
    ferme = Mock()
    @contextmanager
    def ouvrir():
        try:
            yield SimpleNamespace(lire=Mock(side_effect=KeyboardInterrupt))
        finally:
            ferme()
    capteur = CapteurSupervise('test', 60, ouvrir)
    try:
        with pytest.raises(KeyboardInterrupt):
            capteur.lire()
    finally:
        capteur.fermer()
    ferme.assert_called_once()


def test_pompe_refuse_erreur_de_lecture_avant_activation(monkeypatch):
    import sys
    relais = Mock()
    monkeypatch.setitem(sys.modules, 'gpiozero', SimpleNamespace(OutputDevice=lambda *a, **k: relais))
    flotteur = SimpleNamespace(lire=Mock(side_effect=CapteurIndisponible('inconnu')))
    pompe = Pompe(17, flotteur, active_high=True)
    with pytest.raises(CapteurIndisponible):
        pompe.arroser()
    relais.on.assert_not_called()
    pompe.fermer()


def test_demarrage_sans_bibliotheques_materielles_continue(monkeypatch, capsys):
    import sys
    from raspberry_pi import main
    monkeypatch.setitem(sys.modules, 'gpiozero', None)
    monkeypatch.setitem(sys.modules, 'board', None)
    monkeypatch.setattr(sys, 'argv', ['collecte', '--lumiere', '--sol', '--une-lecture'])
    publicateur = Mock()
    monkeypatch.setattr(main, 'PublicateurMQTT', Mock(return_value=publicateur))
    assert main.main() == 0
    publicateur.connecter.assert_called_once()
    publicateur.publier.assert_not_called()
    publicateur.deconnecter.assert_called_once()
    erreurs = capsys.readouterr().err
    for composant in ['Feu', 'réservoir', 'luminosité', 'sol']:
        assert composant in erreurs
