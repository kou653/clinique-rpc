"""
accueil_server.py — Serveur gRPC pour le Service Accueil.
Port d'écoute : 50051 (configurable via GRPC_PORT)
Enregistre :
  - AccueilServiceServicer (accueil.proto)
  - AccueilServicer (clinique.proto : pour que Consultation puisse appeler Accueil)
"""

import sys
import os
import logging
from concurrent import futures
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "generated"))

try:
    import accueil_pb2_grpc
    import clinique_pb2_grpc
except ImportError:
    from grpc_services.generated import accueil_pb2_grpc, clinique_pb2_grpc

from grpc_services.accueil_servicer import AccueilServicer, CliniqueAccueilServicer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AccueilServer")

PORT = int(os.getenv("GRPC_PORT", "50051"))


def serve():
    """Démarre le serveur gRPC."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # 1. Enregistre le service Accueil standard
    accueil_pb2_grpc.add_AccueilServiceServicer_to_server(AccueilServicer(), server)
    # 2. Enregistre l'interface Accueil attendue par Consultation (clinique.proto)
    clinique_pb2_grpc.add_AccueilServicer_to_server(CliniqueAccueilServicer(), server)

    server.add_insecure_port(f"0.0.0.0:{PORT}")
    server.start()
    logger.info(f"=== Serveur gRPC Service Accueil démarré sur le port {PORT} ===")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur gRPC demandé...")
        server.stop(0)


if __name__ == "__main__":
    serve()
