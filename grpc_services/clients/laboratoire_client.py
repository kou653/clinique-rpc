"""
laboratoire_client.py — Client gRPC vers le Service Distant Laboratoire.

Flux RPC cible :
    LaboService.CreateLabOrder(LabOrderRequest) returns (LabOrderResponse)

Port par défaut du service Laboratoire : 50053
"""

import os
import logging

logger = logging.getLogger("LaboratoireClient")

EXTERNAL_SERVICES_ENABLED = os.getenv("EXTERNAL_SERVICES_ENABLED", "false").lower() == "true"
LABO_HOST = os.getenv("LABO_SERVICE_HOST", "localhost")
LABO_PORT = int(os.getenv("LABO_SERVICE_PORT", "50053"))


def create_lab_order(order_data: dict) -> dict:
    """
    Appelle le Service Laboratoire distant :
    LaboService.CreateLabOrder(LabOrderRequest)
    """
    if not EXTERNAL_SERVICES_ENABLED:
        logger.info("Service Laboratoire distant désactivé ou en attente de documentation.")
        return {
            "id_ordre_labo": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "EN_ATTENTE",
            "message": "Demande d'analyses transmise au Laboratoire (Service distant en attente de documentation)."
        }

    try:
        import grpc
        # NOTE : Dès réception de la documentation et contrat proto du Laboratoire :
        # from grpc_services.generated import labo_pb2, labo_pb2_grpc
        # channel = grpc.insecure_channel(f"{LABO_HOST}:{LABO_PORT}")
        # stub = labo_pb2_grpc.LaboServiceStub(channel)
        # response = stub.CreateLabOrder(labo_pb2.LabOrderRequest(**order_data))
        # return {"id_ordre_labo": response.id_ordre_labo, "statut": response.statut, "message": response.message}
        return {
            "id_ordre_labo": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "EN_ATTENTE",
            "message": "En attente des contrats proto du Service Laboratoire distant."
        }
    except Exception as exc:
        logger.error(f"Erreur appel distant Laboratoire: {exc}")
        return {
            "id_ordre_labo": "",
            "id_dossier": order_data.get("id_dossier", ""),
            "statut": "ERREUR",
            "message": f"Service Laboratoire indisponible: {exc}"
        }
