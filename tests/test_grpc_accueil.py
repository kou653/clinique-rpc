"""
tests/test_grpc_accueil.py — Tests unitaires pour la logique gRPC.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "grpc_services", "generated"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from grpc_services import database
from grpc_services.accueil_servicer import AccueilServicer
from grpc_services.generated import accueil_pb2


@pytest.fixture(autouse=True)
def setup_teardown():
    database.clear_all()
    yield
    database.clear_all()


def test_register_patient_success():
    servicer = AccueilServicer()
    request = accueil_pb2.RegisterPatientRequest(
        nom="Diallo",
        prenom="Mamadou",
        date_naissance="1990-01-01",
        sexe="M",
        adresse="Conakry",
        telephone="+224620000000",
        antecedents=["Asthme"]
    )
    response = servicer.RegisterPatient(request, None)
    assert response.statut == "ENREGISTRE"
    assert response.id_dossier.startswith("DOS-")
    assert response.nom == "Diallo"


def test_book_consultation():
    servicer = AccueilServicer()
    reg = servicer.RegisterPatient(accueil_pb2.RegisterPatientRequest(
        nom="Kouame", prenom="Aya", date_naissance="1995-04-12", sexe="F"
    ), None)

    apt_req = accueil_pb2.AppointmentRequest(
        id_dossier=reg.id_dossier,
        medecin_id="MED-001",
        date_rdv="2026-11-05T09:00:00",
        motif="Contrôle général"
    )
    res = servicer.BookConsultation(apt_req, None)
    assert res.id_dossier == reg.id_dossier
    assert res.statut in ["CONFIRME", "EN_ATTENTE"]


def test_book_lab_order():
    servicer = AccueilServicer()
    reg = servicer.RegisterPatient(accueil_pb2.RegisterPatientRequest(
        nom="Sow", prenom="Aissatou", date_naissance="1998-12-05", sexe="F"
    ), None)

    lab_req = accueil_pb2.LabOrderRequest(
        id_dossier=reg.id_dossier,
        medecin_prescripteur_id="MED-001",
        analyses_prescrites=["NFS", "Glycémie"],
        ordonnance_ref="ORD-01"
    )
    res = servicer.BookLabOrder(lab_req, None)
    assert res.id_dossier == reg.id_dossier
    assert res.statut in ["TRANSMIS", "EN_ATTENTE"]


def test_book_radio_order():
    servicer = AccueilServicer()
    reg = servicer.RegisterPatient(accueil_pb2.RegisterPatientRequest(
        nom="Barry", prenom="Alpha", date_naissance="1980-08-15", sexe="M"
    ), None)

    rad_req = accueil_pb2.RadioOrderRequest(
        id_dossier=reg.id_dossier,
        medecin_prescripteur_id="MED-001",
        types_radio=["Thorax", "Échographie"],
        notes="Face et profil"
    )
    res = servicer.BookRadioOrder(rad_req, None)
    assert res.id_dossier == reg.id_dossier
    assert res.statut in ["TRANSMIS", "EN_ATTENTE"]
