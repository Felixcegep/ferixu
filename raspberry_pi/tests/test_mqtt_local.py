"""Essai réel publisher → Mosquitto → ingestion → JSONL, capteurs simulés."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from uuid import uuid4

import pytest

from raspberry_pi import config
from raspberry_pi.publication_donnees import PublicateurMQTT


@pytest.mark.skipif(shutil.which('mosquitto') is None, reason='Mosquitto non installé')
def test_broker_local_enregistrement_et_message_invalide(tmp_path, monkeypatch):
    # Un broker isolé : aucun changement au service Mosquitto de la machine.
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    configuration = tmp_path / 'mosquitto.conf'
    configuration.write_text(f'listener {port} 127.0.0.1\nallow_anonymous true\npersistence false\n')
    sortie = tmp_path / 'lectures.jsonl'
    racine = Path(__file__).resolve().parents[2]
    environnement = dict(os.environ, MQTT_HOTE='127.0.0.1', MQTT_PORT=str(port),
                          MQTT_UTILISATEUR='', MQTT_MOT_DE_PASSE='')
    monkeypatch.setattr(config, 'MQTT_HOTE', '127.0.0.1')
    monkeypatch.setattr(config, 'MQTT_PORT', port)
    monkeypatch.setattr(config, 'MQTT_UTILISATEUR', '')
    monkeypatch.setattr(config, 'MQTT_MOT_DE_PASSE', '')
    publicateur = PublicateurMQTT(f'test-publicateur-{uuid4().hex}')
    ingestion = None
    with (tmp_path / 'broker.log').open('w+') as log_broker, (tmp_path / 'ingestion.log').open('w+') as log_ingestion:
        broker = subprocess.Popen(['mosquitto', '-c', str(configuration)],
                                  stdout=log_broker, stderr=subprocess.STDOUT)
        try:
            fin = time.monotonic() + 5
            while True:
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.1):
                        break
                except OSError:
                    if broker.poll() is not None or time.monotonic() > fin:
                        pytest.fail('Broker non démarré : ' + (tmp_path / 'broker.log').read_text())
                    time.sleep(0.02)
            ingestion = subprocess.Popen(
                [sys.executable, '-m', 'raspberry_pi.ingestion.service_ingestion', '--fichier', str(sortie)],
                cwd=racine, env=environnement, stdout=log_ingestion, stderr=subprocess.STDOUT)
            fin = time.monotonic() + 5
            while 'Ingestion prête' not in (tmp_path / 'ingestion.log').read_text():
                if ingestion.poll() is not None or time.monotonic() > fin:
                    pytest.fail('Ingestion non prête : ' + (tmp_path / 'ingestion.log').read_text())
                time.sleep(0.02)
            publicateur.connecter()
            # Contournement intentionnel de la validation pour tester le subscriber.
            resultat = publicateur._client.publish(config.TOPIC_EAU, b'{', qos=1)
            resultat.wait_for_publish(timeout=3)
            attendues = []
            for index in range(12):
                mesure = {'etat': 'insuffisant' if index % 2 else 'suffisant',
                          'vide': bool(index % 2),
                          'horodatage': f'2026-10-20T14:30:{index:02d}+00:00'}
                attendues.append(mesure)
                publicateur.publier(config.TOPIC_EAU, mesure)
            for topic, valeurs in [(config.TOPIC_LUMIERE, {'lux': 12345.0}),
                                   (config.TOPIC_SOL, {'temperature_c': 22.5,
                                                      'humidite_brute': 600,
                                                      'humidite_pct': 50})]:
                mesure = dict(valeurs, horodatage='2026-10-20T14:31:00+00:00')
                attendues.append(mesure)
                publicateur.publier(topic, mesure)
            fin = time.monotonic() + 5
            while True:
                lignes = sortie.read_text().splitlines() if sortie.exists() else []
                if len(lignes) >= len(attendues):
                    break
                if time.monotonic() > fin:
                    pytest.fail('Messages manquants : ' + (tmp_path / 'ingestion.log').read_text())
                time.sleep(0.02)
            assert [json.loads(ligne) for ligne in lignes] == attendues
            assert ingestion.poll() is None
            assert 'Mesure non enregistrée' in (tmp_path / 'ingestion.log').read_text()
        finally:
            publicateur.deconnecter()
            if ingestion is not None:
                ingestion.terminate()
                ingestion.wait(timeout=5)
            broker.terminate()
            broker.wait(timeout=5)
