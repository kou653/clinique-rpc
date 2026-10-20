"""
consultation_client.py — Client gRPC vers le Service Distant Consultation.

Flux RPC cible :
    ConsultationService.NotifyAppointment(AppointmentRequest) returns (AppointmentResponse)

Port par défaut du service Consultation : 50052
Géré gracieusement en attendant la documentation du service Consultation.
"""

import os
import logging

logger = logging.getLogger("ConsultationClient")

EXTERNAL_SERVICES_ENABLED = os.getenv("EXTERNAL_SERVICES_ENABLED", "false").lower() == "true"
CONSULTATION_HOST = os.getenv("CONSULTATION_SERVICE_HOST", "localhost")
CONSULTATION_PORT = int(os.getenv("CONSULTATION_SERVICE_PORT", "50052"))


def notify_appointment(appointment_data: dict) -> dict:
    """
    Appelle le Service Consultation distant :
    ConsultationService.NotifyAppointment(AppointmentRequest)
    """
    if not EXTERNAL_SERVICES_ENABLED:
        logger.info("Service Consultation distant désactivé ou en attente de documentation.")
        return {
            "id_rdv": "",
            "id_dossier": appointment_data.get("id_dossier", ""),
            "medecin_id": appointment_data.get("medecin_id", ""),
            "date_rdv": appointment_data.get("date_rdv", ""),
            "statut": "EN_ATTENTE",
            "message": "Demande transmise au Service Consultation (Service distant en attente de documentation)."
        }

    try:
        import grpc
        # NOTE : Dès réception du proto de Consultation, importer le stub ici :
        # from grpc_services.generated import consultation_pb2, consultation_pb2_grpc
        # channel = grpc.insecure_channel(f"{CONSULTATION_HOST}:{CONSULTATION_PORT}")
        # stub = consultation_pb2_grpc.ConsultationServiceStub(channel)
        # response = stub.NotifyAppointment(consultation_pb2.AppointmentRequest(**appointment_data))
        # return {"id_rdv": response.id_rdv, "statut": response.statut, "message": response.message}
        return {
            "id_rdv": "",
            "id_dossier": appointment_data.get("id_dossier", ""),
            "medecin_id": appointment_data.get("medecin_id", ""),
            "date_rdv": appointment_data.get("date_rdv", ""),
            "statut": "EN_ATTENTE",
            "message": "En attente des contrats proto du Service Consultation distant."
        }
    except Exception as exc:
        logger.error(f"Erreur appel distant Consultation: {exc}")
        return {
            "id_rdv": "",
            "id_dossier": appointment_data.get("id_dossier", ""),
            "medecin_id": appointment_data.get("medecin_id", ""),
            "date_rdv": appointment_data.get("date_rdv", ""),
            "statut": "ERREUR",
            "message": f"Service Consultation indisponible: {exc}"
        }
