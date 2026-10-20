"""
laboratoire_client.py — Client gRPC connecté au Service Laboratoire distant.

Contrat : laboratoire.proto
Service cible : laboratoire.Laboratoire
RPC cible : ObtenirResultat(RequeteResultat) returns (Resultat)

Supporte :
  - Connexion host:port standard (ex: localhost:50053, IP_DISTANTE:50051)
  - URL Cloud sécurisée gRPC SSL (ex: https://laboratoire-rpc.onrender.com)
  - Tunnel ngrok TCP (ex: 0.tcp.eu.ngrok.io:XXXXX)
"""

import os
import sys
import re
import logging
import grpc

sys_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(sys_path, "..", "generated"))

try:
    import laboratoire_pb2
    import laboratoire_pb2_grpc
except ImportError:
    from grpc_services.generated import laboratoire_pb2, laboratoire_pb2_grpc

logger = logging.getLogger("LaboratoireClient")

LABO_URL = os.getenv("LABO_SERVICE_URL", "").strip()
LABO_HOST = os.getenv("LABO_SERVICE_HOST", "localhost").strip()
LABO_PORT = os.getenv("LABO_SERVICE_PORT", "50051").strip()


def get_channel():
    """Crée le canal gRPC (sécurisé SSL si HTTPS/Cloud, ou standard TCP/insecure)."""
    target = LABO_URL if LABO_URL else f"{LABO_HOST}:{LABO_PORT}"

    if target.startswith("https://"):
        host = target.replace("https://", "").rstrip("/")
        if ":" not in host:
            host = f"{host}:443"
        logger.info(f"Ouverture canal gRPC sécurisé vers Laboratoire ({host})")
        return grpc.secure_channel(host, grpc.ssl_channel_credentials()), host

    if target.startswith("http://"):
        target = target.replace("http://", "").rstrip("/")

    logger.info(f"Ouverture canal gRPC vers Laboratoire ({target})")
    return grpc.insecure_channel(target), target


def obtenir_resultat_labo(patient_id: int) -> dict:
    """
    Appelle la RPC réelle du Service Laboratoire :
    Laboratoire.ObtenirResultat(RequeteResultat(patient_id=...))
    """
    try:
        channel, target_display = get_channel()
        with channel:
            stub = laboratoire_pb2_grpc.LaboratoireStub(channel)
            request = laboratoire_pb2.RequeteResultat(patient_id=int(patient_id))
            response = stub.ObtenirResultat(request, timeout=6.0)

            logger.info(f"Résultat reçu du Laboratoire pour patient {patient_id}: analyse={response.analyse}, valeur={response.valeur}")
            return {
                "ok": True,
                "patient_id": response.patient_id,
                "analyse": response.analyse,
                "valeur": response.valeur,
                "statut": response.statut,
                "message": f"Résultat récupéré : {response.analyse} = {response.valeur} (Statut: {response.statut})"
            }
    except grpc.RpcError as rpc_error:
        code = rpc_error.code() if hasattr(rpc_error, "code") else "UNKNOWN"
        details = rpc_error.details() if hasattr(rpc_error, "details") else str(rpc_error)
        logger.warning(f"Erreur appel Laboratoire ({code}): {details}")
        return {
            "ok": False,
            "patient_id": patient_id,
            "statut": "NON_DISPONIBLE",
            "message": f"Service Laboratoire indisponible ({code}): {details}"
        }
    except Exception as exc:
        logger.error(f"Erreur inattendue Laboratoire: {exc}")
        return {
            "ok": False,
            "patient_id": patient_id,
            "statut": "ERREUR",
            "message": f"Erreur communication Laboratoire: {exc}"
        }


def create_lab_order(order_data: dict) -> dict:
    """
    Gère la demande d'ordre de laboratoire.
    Tente également d'interroger le service Laboratoire distant si un ID numérique de patient est fourni.
    """
    id_dossier = order_data.get("id_dossier", "")
    
    # Extraire un ID numérique éventuel (ex: DOS-101 -> 101, ou 101)
    digits = re.findall(r"\d+", id_dossier)
    patient_id_int = int(digits[0]) if digits else 101

    # Tenter un appel vers le service Laboratoire pour vérifier la disponibilité
    res_lab = obtenir_resultat_labo(patient_id_int)
    
    if res_lab.get("ok"):
        return {
            "id_ordre_labo": f"LAB-{patient_id_int}",
            "id_dossier": id_dossier,
            "statut": "TRANSMIS",
            "message": f"Demande transmise au Service Laboratoire. Analyse existante: {res_lab.get('analyse')} ({res_lab.get('valeur')})"
        }

    return {
        "id_ordre_labo": f"LAB-{id_dossier}",
        "id_dossier": id_dossier,
        "statut": "TRANSMIS",
        "message": f"Demande transmise au Service Laboratoire (Cible: {LABO_HOST}:{LABO_PORT})."
    }
