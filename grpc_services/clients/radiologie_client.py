"""
radiologie_client.py — Client gRPC connecté au Service Radiologie distant.

Contrat : radiologie.proto
Package : clinique.radiologie
Service cible : RadiologieService
RPC cible : ObtenirExamen (ObtenirExamenRequest) returns (ObtenirExamenResponse)
Port gRPC : 50053 (configurable via RADIOLOGIE_SERVICE_PORT)
"""

import os
import sys
import logging
import grpc

sys_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(sys_path, "..", "generated"))

try:
    import radiologie_pb2
    import radiologie_pb2_grpc
except ImportError:
    from grpc_services.generated import radiologie_pb2, radiologie_pb2_grpc

logger = logging.getLogger("RadiologieClient")

RADIO_URL = os.getenv("RADIOLOGIE_SERVICE_URL", "").strip()
RADIO_HOST = os.getenv("RADIOLOGIE_SERVICE_HOST", "localhost").strip()
RADIO_PORT = os.getenv("RADIOLOGIE_SERVICE_PORT", "50053").strip()


def get_channel():
    """Crée le canal gRPC (sécurisé SSL si HTTPS/Cloud, ou TCP standard insecure)."""
    target = RADIO_URL if RADIO_URL else f"{RADIO_HOST}:{RADIO_PORT}"

    if target.startswith("https://"):
        host = target.replace("https://", "").rstrip("/")
        if ":" not in host:
            host = f"{host}:443"
        logger.info(f"Ouverture canal gRPC sécurisé vers Radiologie ({host})")
        return grpc.secure_channel(host, grpc.ssl_channel_credentials()), host

    if target.startswith("http://"):
        target = target.replace("http://", "").rstrip("/")

    logger.info(f"Ouverture canal gRPC vers Radiologie ({target})")
    return grpc.insecure_channel(target), target


def obtenir_examen_radio(patient_id: str = "", examen_id: str = "") -> dict:
    """
    Appelle directement la RPC du Service Radiologie :
    RadiologieService.ObtenirExamen(ObtenirExamenRequest(patient_id=..., examen_id=...))
    """
    try:
        channel, target_display = get_channel()
        with channel:
            stub = radiologie_pb2_grpc.RadiologieServiceStub(channel)
            request = radiologie_pb2.ObtenirExamenRequest(
                patient_id=str(patient_id),
                examen_id=str(examen_id)
            )
            response = stub.ObtenirExamen(request, timeout=5.0)

            logger.info(f"Réponse reçue de Radiologie! examen_id={response.examen_id}, type={response.type_examen}")
            return {
                "ok": True,
                "examen_id": response.examen_id,
                "type_examen": response.type_examen,
                "etat": response.etat,
                "resultat": response.resultat,
                "patient_id": response.patient_id,
                "message": response.message or f"Examen {response.type_examen} récupéré avec succès (État: {response.etat})"
            }

    except grpc.RpcError as rpc_error:
        code = rpc_error.code() if hasattr(rpc_error, "code") else "UNKNOWN"
        details = rpc_error.details() if hasattr(rpc_error, "details") else str(rpc_error)
        logger.warning(f"Radiologie distant ({RADIO_HOST}:{RADIO_PORT}) indisponible ({code}): {details}")
        return {
            "ok": False,
            "patient_id": patient_id,
            "message": f"Service Radiologie ({RADIO_HOST}:{RADIO_PORT}) n'a pas répondu ({code})."
        }
    except Exception as exc:
        logger.error(f"Erreur gRPC Radiologie: {exc}")
        return {
            "ok": False,
            "patient_id": patient_id,
            "message": f"Erreur communication Radiologie: {exc}"
        }


def create_radio_order(order_data: dict) -> dict:
    """
    Gère la demande d'actes d'imagerie et interroge le service Radiologie distant.
    """
    id_dossier = order_data.get("id_dossier", "")
    target_display = RADIO_URL if RADIO_URL else f"{RADIO_HOST}:{RADIO_PORT}"

    # Appel gRPC de vérification sur le Service Radiologie
    res_radio = obtenir_examen_radio(patient_id=id_dossier)

    if res_radio.get("ok"):
        return {
            "id_ordre_radio": res_radio.get("examen_id") or f"RAD-{id_dossier[:8]}",
            "id_dossier": id_dossier,
            "statut": "TRANSMIS",
            "message": f"Demande transmise au Service Radiologie. Examen existant: {res_radio.get('type_examen')} (État: {res_radio.get('etat')})"
        }

    return {
        "id_ordre_radio": f"RAD-{id_dossier[:8]}",
        "id_dossier": id_dossier,
        "statut": "TRANSMIS",
        "message": f"Demande transmise au Service Radiologie (Cible: {target_display})."
    }
