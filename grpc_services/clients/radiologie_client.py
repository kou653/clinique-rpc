"""
radiologie_client.py — Client gRPC vers le Service Distant Radiologie.

Flux RPC cible :
    RadioService.CreateRadioOrder(RadioOrderRequest) returns (RadioOrderResponse)

Port par défaut du service Radiologie : 50054
"""

import os
import logging

logger = logging.getLogger("RadiologieClient")

EXTERNAL_SERVICES_ENABLED = os.getenv("EXTERNAL_SERVICES_ENABLED", "false").lower() == "true"
RADIO_HOST = os.getenv("RADIO_SERVICE_HOST", "localhost")
RADIO_PORT = int(os.getenv("RADIO_SERVICE_PORT", "50054"))


def create_radio_order(order_data: dict) -> dict:
    """
    Appelle le Service Radiologie distant :
    RadioService.CreateRadioOrder(RadioOrderRequest)
    """
    if not EXTERNAL_SERVICES_ENABLED:
        logger.info("Service Radiologie distant désactivé ou en attente de documentation.")
        return {
            "id_ordre_radio": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "EN_ATTENTE",
            "message": "Demande d'examens transmise à la Radiologie (Service distant en attente de documentation)."
        }

    try:
        import grpc
        # NOTE : Dès réception de la documentation et contrat proto de la Radiologie :
        # from grpc_services.generated import radio_pb2, radio_pb2_grpc
        # channel = grpc.insecure_channel(f"{RADIO_HOST}:{RADIO_PORT}")
        # stub = radio_pb2_grpc.RadioServiceStub(channel)
        # response = stub.CreateRadioOrder(radio_pb2.RadioOrderRequest(**order_data))
        # return {"id_ordre_radio": response.id_ordre_radio, "statut": response.statut, "message": response.message}
        return {
            "id_ordre_radio": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "EN_ATTENTE",
            "message": "En attente des contrats proto du Service Radiologie distant."
        }
    except Exception as exc:
        logger.error(f"Erreur appel distant Radiologie: {exc}")
        return {
            "id_ordre_radio": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "ERREUR",
            "message": f"Service Radiologie indisponible: {exc}"
        }
