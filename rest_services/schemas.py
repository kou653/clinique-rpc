"""
schemas.py — Modèles Pydantic pour la passerelle REST (FastAPI).
Aucun champ superflu : respect strict de la demande.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# 1.1 Inscription du Patient
# "stocke l'état civil ainsi que les antécédents de base"
# -----------------------------------------------------------------------------
class RegisterPatientRequest(BaseModel):
    nom: str = Field(..., description="Nom de famille")
    prenom: str = Field(..., description="Prénom")
    date_naissance: str = Field(..., description="Date de naissance (YYYY-MM-DD)")
    sexe: str = Field(..., description="M ou F")
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    antecedents: Optional[List[str]] = Field(default_factory=list)


class PatientResponseModel(BaseModel):
    id_dossier: str
    nom: str
    prenom: str
    date_naissance: str
    sexe: str
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    antecedents: List[str] = []
    statut: str
    message: str


# -----------------------------------------------------------------------------
# 1.2 Prise de RDV Consultation
# -----------------------------------------------------------------------------
class ConsultationRdvRequest(BaseModel):
    id_dossier: str = Field(..., description="Identifiant unique du dossier patient (idDossier)")
    medecin_id: str = Field(..., description="Identifiant du médecin")
    date_rdv: str = Field(..., description="Date et heure de la consultation")
    motif: str = Field(..., description="Motif de la consultation")
    priorite: Optional[str] = "NORMAL"


class ConsultationRdvResponse(BaseModel):
    id_rdv: str
    id_dossier: str
    medecin_id: str
    date_rdv: str
    statut: str
    message: str


# -----------------------------------------------------------------------------
# 1.3 Prise de RDV Laboratoire
# -----------------------------------------------------------------------------
class LabRdvRequest(BaseModel):
    id_dossier: str = Field(..., description="Identifiant du dossier patient (idDossier)")
    medecin_prescripteur_id: str = Field(..., description="Médecin prescripteur")
    analyses_prescrites: List[str] = Field(..., description="Analyses prescrites sur l'ordonnance")
    priorite: Optional[str] = "NORMAL"
    ordonnance_ref: Optional[str] = ""


class LabRdvResponse(BaseModel):
    id_ordre_labo: str
    id_dossier: str
    statut: str
    message: str


# -----------------------------------------------------------------------------
# 1.4 Prise de RDV Radiologie
# -----------------------------------------------------------------------------
class RadioRdvRequest(BaseModel):
    id_dossier: str = Field(..., description="Identifiant du dossier patient (idDossier)")
    medecin_prescripteur_id: str = Field(..., description="Médecin prescripteur")
    types_radio: List[str] = Field(..., description="Liste des types de radio à exécuter")
    priorite: Optional[str] = "NORMAL"
    notes: Optional[str] = ""


class RadioRdvResponse(BaseModel):
    id_ordre_radio: str
    id_dossier: str
    statut: str
    message: str
