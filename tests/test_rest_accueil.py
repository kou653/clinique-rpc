"""
tests/test_rest_accueil.py — Tests d'intégration de la passerelle REST (FastAPI -> gRPC).
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
from concurrent import futures
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "grpc_services", "generated"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from grpc_services.generated import accueil_pb2_grpc
from grpc_services.accueil_servicer import AccueilServicer
from grpc_services import database
from rest_services.gateway import app

client = TestClient(app)
TEST_GRPC_PORT = 50051


@pytest.fixture(scope="session", autouse=True)
def run_grpc_server_for_tests():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    accueil_pb2_grpc.add_AccueilServiceServicer_to_server(AccueilServicer(), server)
    server.add_insecure_port(f"127.0.0.1:{TEST_GRPC_PORT}")
    server.start()
    yield
    server.stop(0)


@pytest.fixture(autouse=True)
def clean_db():
    database.clear_all()
    yield
    database.clear_all()


def test_api_info():
    res = client.get("/api/info")
    assert res.status_code == 200
    assert res.json()["rest_port"] == 8081


def test_1_1_register_patient():
    res = client.post("/v1/accueil/patients", json={
        "nom": "Traore",
        "prenom": "Ousmane",
        "date_naissance": "1992-03-10",
        "sexe": "M",
        "antecedents": ["Diabète"]
    })
    assert res.status_code == 201
    assert res.json()["id_dossier"].startswith("DOS-")


def test_1_2_rdv_consultation():
    # 1. Créer le patient
    reg = client.post("/v1/accueil/patients", json={
        "nom": "Barry", "prenom": "Alpha", "date_naissance": "1980-01-01", "sexe": "M"
    }).json()
    id_dossier = reg["id_dossier"]

    # 2. RDV Consultation (POST /v1/accueil/rdv/consultation)
    res = client.post("/v1/accueil/rdv/consultation", json={
        "id_dossier": id_dossier,
        "medecin_id": "MED-001",
        "date_rdv": "2026-11-10T10:00:00",
        "motif": "Fièvre",
        "priorite": "NORMAL"
    })
    assert res.status_code == 200
    assert res.json()["id_dossier"] == id_dossier
    assert res.json()["statut"] in ["CONFIRME", "EN_ATTENTE"]


def test_1_3_rdv_laboratoire():
    reg = client.post("/v1/accueil/patients", json={
        "nom": "Camara", "prenom": "Fatou", "date_naissance": "1995-05-05", "sexe": "F"
    }).json()
    id_dossier = reg["id_dossier"]

    # RDV Labo (POST /v1/accueil/rdv/laboratoire)
    res = client.post("/v1/accueil/rdv/laboratoire", json={
        "id_dossier": id_dossier,
        "medecin_prescripteur_id": "MED-001",
        "analyses_prescrites": ["NFS", "Palu"],
        "ordonnance_ref": "ORD-123"
    })
    assert res.status_code == 200
    assert res.json()["id_dossier"] == id_dossier
    assert res.json()["statut"] in ["TRANSMIS", "EN_ATTENTE"]


def test_1_4_rdv_radiologie():
    reg = client.post("/v1/accueil/patients", json={
        "nom": "Nguema", "prenom": "Paul", "date_naissance": "1988-08-08", "sexe": "M"
    }).json()
    id_dossier = reg["id_dossier"]

    # RDV Radiologie (POST /v1/accueil/rdv/radiologie)
    res = client.post("/v1/accueil/rdv/radiologie", json={
        "id_dossier": id_dossier,
        "medecin_prescripteur_id": "MED-001",
        "types_radio": ["Radiographie Thorax"],
        "notes": "Face"
    })
    assert res.status_code == 200
    assert res.json()["id_dossier"] == id_dossier
    assert res.json()["statut"] in ["TRANSMIS", "EN_ATTENTE"]
