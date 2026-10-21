"""
gateway.py — Passerelle REST (FastAPI) pour le Service Accueil (Port 8081).
Respecte à la lettre les spécifications :
  - 1.1 Inscription Patient  : POST /v1/accueil/patients
  - 1.2 RDV Consultation     : POST /v1/accueil/rdv/consultation
  - 1.3 RDV Laboratoire      : POST /v1/accueil/rdv/laboratoire
  - 1.4 RDV Radiologie       : POST /v1/accueil/rdv/radiologie
"""

import os
import sys
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "grpc_services", "generated"))

try:
    import accueil_pb2
    import accueil_pb2_grpc
except ImportError:
    from grpc_services.generated import accueil_pb2, accueil_pb2_grpc

from grpc_services import database
from grpc_services.clients import laboratoire_client
from rest_services.schemas import (
    RegisterPatientRequest,
    PatientResponseModel,
    ConsultationRdvRequest,
    ConsultationRdvResponse,
    LabRdvRequest,
    LabRdvResponse,
    RadioRdvRequest,
    RadioRdvResponse,
    LabResultResponse,
    ObservationsPayload,
    PrescriptionsPayload,
    DossierUpdateResponse,
)

app = FastAPI(
    title="Service Accueil — Clinique Espoir",
    description="Passerelle REST branchée sur le serveur gRPC (50051).",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GRPC_HOST = os.getenv("GRPC_HOST", "localhost")
GRPC_PORT = os.getenv("GRPC_PORT", "50051")
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


def get_grpc_stub() -> accueil_pb2_grpc.AccueilServiceStub:
    channel = grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}")
    return accueil_pb2_grpc.AccueilServiceStub(channel)


@app.get("/", tags=["Interface"])
def root():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Service Accueil", "grpc_port": 50051, "rest_port": 8081}


@app.get("/api/info", tags=["Info"])
def api_info():
    return {
        "service": "Service Accueil",
        "grpc_server": f"{GRPC_HOST}:{GRPC_PORT}",
        "rest_port": 8081,
        "docs_url": "/docs"
    }


# =============================================================================
# 1.1 Inscription du Patient
# Mapped REST : POST /v1/accueil/patients
# =============================================================================
@app.post(
    "/v1/accueil/patients",
    response_model=PatientResponseModel,
    status_code=status.HTTP_201_CREATED,
    tags=["1.1 Inscription Patient"]
)
def register_patient(payload: RegisterPatientRequest):
    stub = get_grpc_stub()
    try:
        grpc_request = accueil_pb2.RegisterPatientRequest(
            nom=payload.nom,
            prenom=payload.prenom,
            date_naissance=payload.date_naissance,
            sexe=payload.sexe,
            adresse=payload.adresse or "",
            telephone=payload.telephone or "",
            antecedents=payload.antecedents or []
        )
        grpc_response = stub.RegisterPatient(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"Erreur gRPC: {e}")

    if grpc_response.statut == "ERREUR":
        raise HTTPException(status_code=400, detail=grpc_response.message)

    return PatientResponseModel(
        id_dossier=grpc_response.id_dossier,
        nom=grpc_response.nom,
        prenom=grpc_response.prenom,
        date_naissance=grpc_response.date_naissance,
        sexe=grpc_response.sexe,
        adresse=grpc_response.adresse,
        telephone=grpc_response.telephone,
        antecedents=list(grpc_response.antecedents),
        statut=grpc_response.statut,
        message=grpc_response.message
    )


@app.get(
    "/v1/accueil/patients/{id_dossier}",
    response_model=PatientResponseModel,
    tags=["1.1 Inscription Patient"]
)
def get_patient(id_dossier: str):
    stub = get_grpc_stub()
    try:
        grpc_request = accueil_pb2.GetPatientRequest(id_dossier=id_dossier)
        grpc_response = stub.GetPatient(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"Erreur gRPC: {e}")

    if grpc_response.statut == "ERREUR":
        raise HTTPException(status_code=404, detail=grpc_response.message)

    return PatientResponseModel(
        id_dossier=grpc_response.id_dossier,
        nom=grpc_response.nom,
        prenom=grpc_response.prenom,
        date_naissance=grpc_response.date_naissance,
        sexe=grpc_response.sexe,
        adresse=grpc_response.adresse,
        telephone=grpc_response.telephone,
        antecedents=list(grpc_response.antecedents),
        statut=grpc_response.statut,
        message=grpc_response.message
    )


@app.get(
    "/v1/accueil/patients",
    response_model=List[PatientResponseModel],
    tags=["1.1 Inscription Patient"]
)
def list_patients():
    patients = database.list_patients()
    return [
        PatientResponseModel(
            id_dossier=p.get("id_dossier", ""),
            nom=p.get("nom", ""),
            prenom=p.get("prenom", ""),
            date_naissance=p.get("date_naissance", ""),
            sexe=p.get("sexe", ""),
            adresse=p.get("adresse", ""),
            telephone=p.get("telephone", ""),
            antecedents=p.get("antecedents", []),
            statut="ENREGISTRE",
            message=""
        )
        for p in patients
    ]


# =============================================================================
# 1.2 Prise de RDV Consultation
# Mapped REST : POST /v1/accueil/rdv/consultation
# Flux RPC : ConsultationService.NotifyAppointment(AppointmentRequest) returns (AppointmentResponse)
# =============================================================================
@app.post(
    "/v1/accueil/rdv/consultation",
    response_model=ConsultationRdvResponse,
    status_code=status.HTTP_200_OK,
    tags=["1.2 RDV Consultation"]
)
def book_consultation(payload: ConsultationRdvRequest):
    stub = get_grpc_stub()
    try:
        grpc_request = accueil_pb2.AppointmentRequest(
            id_dossier=payload.id_dossier,
            medecin_id=payload.medecin_id,
            date_rdv=payload.date_rdv,
            motif=payload.motif,
            priorite=payload.priorite or "NORMAL"
        )
        grpc_response = stub.BookConsultation(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"Erreur gRPC: {e}")

    if grpc_response.statut == "ERREUR":
        raise HTTPException(status_code=404, detail=grpc_response.message)

    return ConsultationRdvResponse(
        id_rdv=grpc_response.id_rdv,
        id_dossier=grpc_response.id_dossier,
        medecin_id=grpc_response.medecin_id,
        date_rdv=grpc_response.date_rdv,
        statut=grpc_response.statut,
        message=grpc_response.message
    )


# =============================================================================
# 1.3 Prise de RDV Laboratoire
# Mapped REST : POST /v1/accueil/rdv/laboratoire
# Flux RPC : LaboService.CreateLabOrder(LabOrderRequest) returns (LabOrderResponse)
# =============================================================================
@app.post(
    "/v1/accueil/rdv/laboratoire",
    response_model=LabRdvResponse,
    status_code=status.HTTP_200_OK,
    tags=["1.3 RDV Laboratoire"]
)
def book_laboratoire(payload: LabRdvRequest):
    stub = get_grpc_stub()
    try:
        grpc_request = accueil_pb2.LabOrderRequest(
            id_dossier=payload.id_dossier,
            medecin_prescripteur_id=payload.medecin_prescripteur_id,
            analyses_prescrites=payload.analyses_prescrites,
            priorite=payload.priorite or "NORMAL",
            ordonnance_ref=payload.ordonnance_ref or ""
        )
        grpc_response = stub.BookLabOrder(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"Erreur gRPC: {e}")

    if grpc_response.statut == "ERREUR":
        raise HTTPException(status_code=404, detail=grpc_response.message)

    return LabRdvResponse(
        id_ordre_labo=grpc_response.id_ordre_labo,
        id_dossier=grpc_response.id_dossier,
        statut=grpc_response.statut,
        message=grpc_response.message
    )


@app.get(
    "/v1/accueil/labo/resultats/{patient_id}",
    response_model=LabResultResponse,
    tags=["1.3 RDV Laboratoire"]
)
def get_lab_result(patient_id: int):
    """
    Interroge le Service Laboratoire distant en gRPC via ObtenirResultat(RequeteResultat).
    """
    res = laboratoire_client.obtenir_resultat_labo(patient_id)
    return LabResultResponse(
        ok=res.get("ok", False),
        patient_id=res.get("patient_id", patient_id),
        analyse=res.get("analyse", ""),
        valeur=res.get("valeur", ""),
        statut=res.get("statut", ""),
        message=res.get("message", "")
    )


# =============================================================================
# 1.4 Prise de RDV Radiologie
# Mapped REST : POST /v1/accueil/rdv/radiologie
# Flux RPC : RadioService.CreateRadioOrder(RadioOrderRequest) returns (RadioOrderResponse)
# =============================================================================
@app.post(
    "/v1/accueil/rdv/radiologie",
    response_model=RadioRdvResponse,
    status_code=status.HTTP_200_OK,
    tags=["1.4 RDV Radiologie"]
)
def book_radiologie(payload: RadioRdvRequest):
    stub = get_grpc_stub()
    try:
        grpc_request = accueil_pb2.RadioOrderRequest(
            id_dossier=payload.id_dossier,
            medecin_prescripteur_id=payload.medecin_prescripteur_id,
            types_radio=payload.types_radio,
            priorite=payload.priorite or "NORMAL",
            notes=payload.notes or ""
        )
        grpc_response = stub.BookRadioOrder(grpc_request)
    except grpc.RpcError as e:
        raise HTTPException(status_code=503, detail=f"Erreur gRPC: {e}")

    if grpc_response.statut == "ERREUR":
        raise HTTPException(status_code=404, detail=grpc_response.message)

    return RadioRdvResponse(
        id_ordre_radio=grpc_response.id_ordre_radio,
        id_dossier=grpc_response.id_dossier,
        statut=grpc_response.statut,
        message=grpc_response.message
    )


# =============================================================================
# MàJ Dossier : Observations et Prescriptions (depuis Consultation ou Web)
# =============================================================================
@app.post(
    "/v1/accueil/patients/{id_dossier}/observations",
    response_model=DossierUpdateResponse,
    tags=["Dossier Médical"]
)
def add_patient_observations(id_dossier: str, payload: ObservationsPayload):
    """
    Ajoute des observations médicales au dossier du patient dans la base de données.
    """
    ok = database.add_observations(id_dossier, payload.observations)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dossier patient '{id_dossier}' introuvable."
        )
    return DossierUpdateResponse(
        ok=True,
        id_dossier=id_dossier,
        message=f"{len(payload.observations)} observation(s) ajoutée(s) avec succès."
    )


@app.post(
    "/v1/accueil/patients/{id_dossier}/prescriptions",
    response_model=DossierUpdateResponse,
    tags=["Dossier Médical"]
)
def add_patient_prescriptions(id_dossier: str, payload: PrescriptionsPayload):
    """
    Ajoute des prescriptions médicales au dossier du patient dans la base de données.
    """
    ok = database.add_prescriptions(id_dossier, payload.prescriptions)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dossier patient '{id_dossier}' introuvable."
        )
    return DossierUpdateResponse(
        ok=True,
        id_dossier=id_dossier,
        message=f"{len(payload.prescriptions)} prescription(s) ajoutée(s) avec succès."
    )
