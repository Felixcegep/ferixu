"""Callbacks de la démo : import sans connexion et enregistrement JSONL."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

CHEMIN = Path(__file__).resolve().parents[1] / 'ingestion' / 'service_ingestion.py'


@pytest.fixture
def ingestion(monkeypatch, tmp_path):
    import paho.mqtt.client as mqtt
    creer_client = Mock(side_effect=AssertionError('Connexion pendant un import'))
    monkeypatch.setattr(mqtt, 'Client', creer_client)
    spec = importlib.util.spec_from_file_location('ingestion_test', CHEMIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    creer_client.assert_not_called()
    monkeypatch.setattr(module, 'FICHIER_DONNEES', tmp_path / 'lectures.jsonl')
    return module


def test_horodatage_conserve(ingestion):
    mesure = {'etat': 'insuffisant', 'vide': True,
              'horodatage': '2026-10-20T14:00:00+00:00'}
    ingestion.on_message(None, None, SimpleNamespace(payload=json.dumps(mesure).encode()))
    assert json.loads(ingestion.FICHIER_DONNEES.read_text()) == mesure


@pytest.mark.parametrize('payload', [b'{', b'\xff', b'[]', b'{}'])
def test_message_invalide_ignore(ingestion, payload):
    ingestion.on_message(None, None, SimpleNamespace(payload=payload))
    assert not ingestion.FICHIER_DONNEES.exists()


def test_erreur_ecriture_signalee(ingestion, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(ingestion, 'FICHIER_DONNEES', tmp_path)
    ingestion.on_message(None, None, SimpleNamespace(payload=b'{"horodatage":"date"}'))
    assert "Impossible d'enregistrer" in capsys.readouterr().out


def test_abonnement_refait_a_la_connexion(ingestion):
    client = Mock()
    ingestion.on_connect(client, None, None, SimpleNamespace(is_failure=False), None)
    client.subscribe.assert_any_call(ingestion.config.TOPIC_EAU)
    client.subscribe.assert_any_call(ingestion.config.TOPIC_LUMIERE)
    assert client.subscribe.call_count == 2


def test_luminosite_enregistree_avec_horodatage(ingestion):
    mesure = {'lux': 12345.0, 'horodatage': '2026-10-20T14:00:00+00:00'}
    ingestion.on_message(None, None, SimpleNamespace(
        topic=ingestion.config.TOPIC_LUMIERE, payload=json.dumps(mesure).encode()))
    assert json.loads(ingestion.FICHIER_DONNEES.read_text()) == mesure
