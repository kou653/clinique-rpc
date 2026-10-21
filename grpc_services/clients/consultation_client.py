"""
consultation_client.py — Client hybride gRPC + REST vers le Service Consultation distant.

Ce client gère automatiquement les deux modes :
  1. Si le serveur de votre collègue est en gRPC : appelle PrendreRDV en gRPC HTTP/2.
  2. Si le serveur distant sur Render est une API REST classique (FastAPI, Flask, Express, Go...)
     qui renvoie UNIMPLEMENTED ou 404 en gRPC binaire : bascule immédiatement et automatiquement
     sur l'appel HTTP/REST (POST /api/rdvs ou POST /v1/rdvs) sans bloquer le système.
"""

import os
import sys
import logging
import httpx
import grpc

sys_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(sys_path, "..", "generated"))

try:
    import clinique_pb2
    import clinique_pb2_grpc
except ImportError:
    from grpc_services.generated import clinique_pb2, clinique_pb2_grpc

logger = logging.getLogger("ConsultationClient")

CONSULTATION_URL = os.getenv("CONSULTATION_SERVICE_URL", "").strip()
CONSULTATION_HOST = os.getenv("CONSULTATION_SERVICE_HOST", "localhost").strip()
CONSULTATION_PORT = os.getenv("CONSULTATION_SERVICE_PORT", "50052").strip()


def get_base_url() -> str:
    """Retourne l'URL de base pour HTTP/REST."""
    if CONSULTATION_URL:
        url = CONSULTATION_URL
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        return url.rstrip("/")
    return f"http://{CONSULTATION_HOST}:{CONSULTATION_PORT}"


def get_channel():
    """Crée le bon canal gRPC (sécurisé SSL si HTTPS/Cloud, ou standard TCP)."""
    target = CONSULTATION_URL if CONSULTATION_URL else f"{CONSULTATION_HOST}:{CONSULTATION_PORT}"

    if target.startswith("https://"):
        host = target.replace("https://", "").rstrip("/")
        if ":" not in host:
            host = f"{host}:443"
        logger.info(f"Ouverture canal gRPC sécurisé vers {host}")
        return grpc.secure_channel(host, grpc.ssl_channel_credentials()), host

    if target.startswith("http://"):
        target = target.replace("http://", "").rstrip("/")

    logger.info(f"Ouverture canal gRPC vers {target}")
    return grpc.insecure_channel(target), target


def notify_appointment_rest(appointment_data: dict) -> dict:
    """
    Appel de secours HTTP REST vers le Service Consultation.
    Tente les routes standards du proto : POST /api/rdvs ou POST /rdvs
    """
    base_url = get_base_url()
    id_dossier = appointment_data.get("id_dossier", "")
    date_rdv = appointment_data.get("date_rdv", "")
    medecin_id = appointment_data.get("medecin_id", "")

    payload = {
        "id_dossier": id_dossier,
        "date_rdv": date_rdv
    }

    routes_to_try = [
        f"{base_url}/api/rdvs",
        f"{base_url}/rdvs",
        f"{base_url}/api/rdv",
        f"{base_url}/PrendreRDV"
    ]

    for route in routes_to_try:
        try:
            logger.info(f"Tentative d'appel REST vers : {route}")
            with httpx.Client(timeout=6.0) as client:
                res = client.post(route, json=payload)
                if res.status_code in [200, 201]:
                    data = res.json()
                    id_rdv = data.get("id_rdv") or data.get("id") or f"RDV-{id_dossier[:8]}"
                    logger.info(f"Succès REST sur {route} ! id_rdv={id_rdv}")
                    return {
                        "id_rdv": str(id_rdv),
                        "id_dossier": id_dossier,
                        "medecin_id": medecin_id,
                        "date_rdv": date_rdv,
                        "statut": "CONFIRME",
                        "message": f"RDV confirmé avec succès par le Service Consultation (REST {route})"
                    }
        except Exception as err:
            logger.debug(f"Route {route} non joignable en REST: {err}")

    return {
        "id_rdv": "",
        "id_dossier": id_dossier,
        "medecin_id": medecin_id,
        "date_rdv": date_rdv,
        "statut": "EN_ATTENTE",
        "message": f"Le serveur distant ({base_url}) n'expose pas PrendreRDV en gRPC ni sur /api/rdvs en REST."
    }


def _format_grpc_error(code: grpc.StatusCode, details: str, target: str) -> str:
    """Traduit les erreurs gRPC en messages clairs selon le sujet d'évaluation."""
    if code == grpc.StatusCode.DEADLINE_EXCEEDED:
        return f"Délai d'attente dépassé (DEADLINE_EXCEEDED) lors de l'appel à Consultation ({target})."
    elif code == grpc.StatusCode.NOT_FOUND:
        return f"Ressource non trouvée (NOT_FOUND) sur le service Consultation ({target})."
    elif code == grpc.StatusCode.UNAVAILABLE:
        return f"Service Consultation indisponible ou hors-ligne (UNAVAILABLE sur {target})."
    elif code == grpc.StatusCode.UNIMPLEMENTED:
        return f"Fonction non implémentée (UNIMPLEMENTED) sur le service Consultation ({target})."
    return f"Erreur gRPC Consultation ({code}): {details}"


def notify_appointment(appointment_data: dict) -> dict:
    """
    Appelle le Service Consultation distant.
    Stratégie :
      1. Tente gRPC en premier avec timeout strict (5.0s).
      2. Intercepte précisément DEADLINE_EXCEEDED, NOT_FOUND, UNAVAILABLE, etc.
      3. Si UNIMPLEMENTED (serveur web REST), bascule automatiquement en REST !
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
            response = stub.PrendreRDV(request, timeout=5.0)

            logger.info(f"Réponse reçue de Consultation via gRPC ! id_rdv={response.id_rdv}")
            return {
                "id_rdv": response.id_rdv,
                "id_dossier": id_dossier,
                "medecin_id": medecin_id,
                "date_rdv": date_rdv,
                "statut": "CONFIRME",
                "message": f"RDV confirmé avec succès par le Service Consultation (gRPC id_rdv: {response.id_rdv})"
            }

    except grpc.RpcError as rpc_error:
        code = rpc_error.code() if hasattr(rpc_error, "code") else grpc.StatusCode.UNKNOWN
        details = rpc_error.details() if hasattr(rpc_error, "details") else str(rpc_error)
        err_msg = _format_grpc_error(code, details, target_display)
        logger.warning(err_msg)

        # Si le serveur répond avec une erreur de protocole HTTP/REST
        # (ex: 405 Method Not Allowed, 404 Not Found, UNIMPLEMENTED, UNAVAILABLE),
        # c'est que le service déployé sur Render est une API REST FastAPI/Uvicorn et non un serveur gRPC natif.
        # On bascule immédiatement et en toute transparence sur l'API REST de Consultation !
        is_rest_server = (
            code in [grpc.StatusCode.UNIMPLEMENTED, grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.UNKNOWN]
            or "UNIMPLEMENTED" in str(rpc_error)
            or "405" in str(details)
            or "404" in str(details)
            or "http2 header" in str(details).lower()
        )

        if is_rest_server:
            logger.info("Détection d'un serveur REST sur l'URL Consultation -> Bascule transparente sur l'API REST (/api/rdvs)...")
            rest_res = notify_appointment_rest(appointment_data)
            if rest_res.get("statut") == "CONFIRME":
                return rest_res

        return {
            "id_rdv": "",
            "id_dossier": id_dossier,
            "medecin_id": medecin_id,
            "date_rdv": date_rdv,
            "statut": "EN_ATTENTE",
            "message": err_msg
        }

    except Exception as exc:
        logger.error(f"Erreur inattendue vers Consultation: {exc}")
        return {
            "id_rdv": "",
            "id_dossier": id_dossier,
            "medecin_id": medecin_id,
            "date_rdv": date_rdv,
            "statut": "EN_ATTENTE",
            "message": f"Erreur de communication avec Consultation: {exc}"
        }
