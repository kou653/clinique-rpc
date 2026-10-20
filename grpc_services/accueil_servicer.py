"""
accueil_servicer.py — Implémentation du servicer gRPC pour AccueilService.
"""

import sys
import os
import uuid
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "generated"))

try:
    import accueil_pb2
    import accueil_pb2_grpc
except ImportError:
    from grpc_services.generated import accueil_pb2, accueil_pb2_grpc

from grpc_services import database
from grpc_services.clients import consultation_client, laboratoire_client, radiologie_client

logger = logging.getLogger("AccueilServicer")


class AccueilServicer(accueil_pb2_grpc.AccueilServiceServicer):
    """
    Implémentation des RPCs du Service Accueil.
    """

    # -------------------------------------------------------------------------
    # 1.1 Inscription du Patient (Service Accueil Interne)
    # -------------------------------------------------------------------------
    def RegisterPatient(self, request, context):
        if not request.nom or not request.prenom:
            return accueil_pb2.PatientResponse(
                statut="ERREUR",
                message="Le nom et le prénom sont obligatoires pour l'inscription."
            )

        patient_dict = {
            "nom": request.nom,
            "prenom": request.prenom,
            "date_naissance": request.date_naissance,
            "sexe": request.sexe,
            "adresse": request.adresse,
            "telephone": request.telephone,
            "antecedents": list(request.antecedents)
        }

        id_dossier = database.save_patient(patient_dict)
        saved = database.get_patient(id_dossier)

        return accueil_pb2.PatientResponse(
            id_dossier=id_dossier,
            nom=saved.get("nom", ""),
            prenom=saved.get("prenom", ""),
            date_naissance=saved.get("date_naissance", ""),
            sexe=saved.get("sexe", ""),
            adresse=saved.get("adresse", ""),
            telephone=saved.get("telephone", ""),
            antecedents=saved.get("antecedents", []),
            statut="ENREGISTRE",
            message=f"Patient {saved.get('prenom')} {saved.get('nom')} enregistré avec succès."
        )

    def GetPatient(self, request, context):
        patient = database.get_patient(request.id_dossier)
        if not patient:
            return accueil_pb2.PatientResponse(
                id_dossier=request.id_dossier,
                statut="ERREUR",
                message=f"Dossier {request.id_dossier} introuvable."
            )

        return accueil_pb2.PatientResponse(
            id_dossier=patient.get("id_dossier", ""),
            nom=patient.get("nom", ""),
            prenom=patient.get("prenom", ""),
            date_naissance=patient.get("date_naissance", ""),
            sexe=patient.get("sexe", ""),
            adresse=patient.get("adresse", ""),
            telephone=patient.get("telephone", ""),
            antecedents=patient.get("antecedents", []),
            statut="TROUVE",
            message="Patient trouvé."
        )

    # -------------------------------------------------------------------------
    # 1.2 Prise de RDV Consultation (Service Distant Consultation)
    # -------------------------------------------------------------------------
    def BookConsultation(self, request, context):
        patient = database.get_patient(request.id_dossier)
        if not patient:
            return accueil_pb2.AppointmentResponse(
                id_dossier=request.id_dossier,
                statut="ERREUR",
                message=f"Dossier {request.id_dossier} introuvable."
            )

        req_data = {
            "id_dossier": request.id_dossier,
            "medecin_id": request.medecin_id,
            "date_rdv": request.date_rdv,
            "motif": request.motif,
            "priorite": request.priorite or "NORMAL"
        }

        result = consultation_client.notify_appointment(req_data)
        id_rdv = result.get("id_rdv") or f"RDV-{uuid.uuid4()}"

        return accueil_pb2.AppointmentResponse(
            id_rdv=id_rdv,
            id_dossier=request.id_dossier,
            medecin_id=request.medecin_id,
            date_rdv=request.date_rdv,
            statut=result.get("statut", "EN_ATTENTE"),
            message=result.get("message", "Demande transmise au Service Consultation.")
        )

    # -------------------------------------------------------------------------
    # 1.3 Prise de RDV Laboratoire (Service Distant Laboratoire)
    # -------------------------------------------------------------------------
    def BookLabOrder(self, request, context):
        patient = database.get_patient(request.id_dossier)
        if not patient:
            return accueil_pb2.LabOrderResponse(
                id_dossier=request.id_dossier,
                statut="ERREUR",
                message=f"Dossier {request.id_dossier} introuvable."
            )

        req_data = {
            "id_dossier": request.id_dossier,
            "medecin_prescripteur_id": request.medecin_prescripteur_id,
            "analyses_prescrites": list(request.analyses_prescrites),
            "priorite": request.priorite or "NORMAL",
            "ordonnance_ref": request.ordonnance_ref
        }

        result = laboratoire_client.create_lab_order(req_data)
        id_ordre = result.get("id_ordre_labo") or f"LAB-{uuid.uuid4()}"

        return accueil_pb2.LabOrderResponse(
            id_ordre_labo=id_ordre,
            id_dossier=request.id_dossier,
            statut=result.get("statut", "EN_ATTENTE"),
            message=result.get("message", "Demande transmise au Service Laboratoire.")
        )

    # -------------------------------------------------------------------------
    # 1.4 Prise de RDV Radiologie (Service Distant Radiologie)
    # -------------------------------------------------------------------------
    def BookRadioOrder(self, request, context):
        patient = database.get_patient(request.id_dossier)
        if not patient:
            return accueil_pb2.RadioOrderResponse(
                id_dossier=request.id_dossier,
                statut="ERREUR",
                message=f"Dossier {request.id_dossier} introuvable."
            )

        req_data = {
            "id_dossier": request.id_dossier,
            "medecin_prescripteur_id": request.medecin_prescripteur_id,
            "types_radio": list(request.types_radio),
            "priorite": request.priorite or "NORMAL",
            "notes": request.notes
        }

        result = radiologie_client.create_radio_order(req_data)
        id_ordre = result.get("id_ordre_radio") or f"RAD-{uuid.uuid4()}"

        return accueil_pb2.RadioOrderResponse(
            id_ordre_radio=id_ordre,
            id_dossier=request.id_dossier,
            statut=result.get("statut", "EN_ATTENTE"),
            message=result.get("message", "Demande transmise au Service Radiologie.")
        )
