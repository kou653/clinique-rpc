"""
consultation_client.py — Client gRPC connecté au Service Consultation distant.

Supporte :
  - Adresse host:port standard (ex: localhost:50052, 192.168.1.50:50051)
  - URL Cloud sécurisée gRPC (ex: https://consultation-service.onrender.com ou .up.railway.app)
  - Tunnel ngrok TCP (ex: 0.tcp.eu.ngrok.io:12345)
"""

import os
import sys
import logging
import grpc

sys_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(sys_path, "..", "generated"))

try:
    import clinique_pb2
    import clinique_pb2_grpc
except ImportError:
    from grpc_services.generated import clinique_pb2, clinique_pb2_grpc

logger = logging.getLogger("ConsultationClient")

# Configuration flexible via variables d'environnement
CONSULTATION_URL = os.getenv("CONSULTATION_SERVICE_URL", "").strip()
CONSULTATION_HOST = os.getenv("CONSULTATION_SERVICE_HOST", "localhost").strip()
CONSULTATION_PORT = os.getenv("CONSULTATION_SERVICE_PORT", "50052").strip()


def get_channel():
    """Crée le bon canal gRPC (sécurisé SSL si HTTPS/Cloud, ou standard insecure)."""
    target = CONSULTATION_URL if CONSULTATION_URL else f"{CONSULTATION_HOST}:{CONSULTATION_PORT}"

    # Si c'est une URL https:// (ex: Render, Railway, Cloud)
    if target.startswith("https://"):
        host = target.replace("https://", "").rstrip("/")
        # Le port par défaut en HTTPS est 443
        if ":" not in host:
            host = f"{host}:443"
        logger.info(f"Ouverture canal gRPC sécurisé (SSL/TLS) vers {host}")
        credentials = grpc.ssl_channel_credentials()
        return grpc.secure_channel(host, credentials), host

    # Si c'est http://
    if target.startswith("http://"):
        target = target.replace("http://", "").rstrip("/")

    logger.info(f"Ouverture canal gRPC non chiffré vers {target}")
    return grpc.insecure_channel(target), target


def notify_appointment(appointment_data: dict) -> dict:
    """
    Appelle directement le Service Consultation distant via gRPC :
    Consultation.PrendreRDV(PrendreRDVRequest)
    """
    id_dossier = appointment_data.get("id_dossier", "")
    date_rdv = appointment_data.get("date_rdv", "")
    medecin_id = appointment_data.get("medecin_id", "")

    try:
        channel, target_display = get_channel()
        with channel:
            stub = clinique_pb2_grpc.ConsultationStub(channel)
            request = clinique_pb2.PrendreRDVRequest(
                id_dossier=id_dossier,
                date_rdv=date_rdv
            )
            response = stub.PrendreRDV(request, timeout=6.0)

            logger.info(f"Réponse reçue de Consultation! id_rdv={response.id_rdv}")
            return {
                "id_rdv": response.id_rdv,
                "id_dossier": id_dossier,
                "medecin_id": medecin_id,
                "date_rdv": date_rdv,
                "statut": "CONFIRME",
                "message": f"RDV confirmé avec succès par le Service Consultation (id_rdv: {response.id_rdv})"
            }

    except grpc.RpcError as rpc_error:
        code = rpc_error.code() if hasattr(rpc_error, "code") else "UNKNOWN"
        details = rpc_error.details() if hasattr(rpc_error, "details") else str(rpc_error)
        logger.warning(f"Consultation distant ({target_display}) indisponible ({code}): {details}")
        
        return {
            "id_rdv": "",
            "id_dossier": id_dossier,
            "medecin_id": medecin_id,
            "date_rdv": date_rdv,
            "statut": "EN_ATTENTE",
            "message": f"Consultation ({target_display}) n'a pas répondu ({code}). Demande mise en attente."
        }
    except Exception as exc:
        logger.error(f"Erreur gRPC vers Consultation: {exc}")
        return {
            "id_rdv": "",
            "id_dossier": id_dossier,
            "medecin_id": medecin_id,
            "date_rdv": date_rdv,
            "statut": "ERREUR",
            "message": f"Erreur communication Consultation: {exc}"
        }
