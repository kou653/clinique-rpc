"""
start_services.py — Lance le serveur gRPC (50051) et la Gateway REST (8081) dans un seul processus.
"""

import sys
import os
import threading
import time
import logging
import uvicorn
from concurrent import futures
import grpc

# Définir le PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(ROOT_DIR, "grpc_services", "generated")
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, GEN_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Launcher")

try:
    import accueil_pb2_grpc
    import clinique_pb2_grpc
except ImportError:
    from grpc_services.generated import accueil_pb2_grpc, clinique_pb2_grpc

from grpc_services.accueil_servicer import AccueilServicer, CliniqueAccueilServicer
from rest_services.gateway import app

GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
REST_PORT = int(os.getenv("REST_PORT", "8081"))


def run_grpc():
    """Démarre le serveur gRPC sur le port configuré."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    accueil_pb2_grpc.add_AccueilServiceServicer_to_server(AccueilServicer(), server)
    clinique_pb2_grpc.add_AccueilServicer_to_server(CliniqueAccueilServicer(), server)
    server.add_insecure_port(f"0.0.0.0:{GRPC_PORT}")
    server.start()
    logger.info(f"Serveur gRPC démarré sur 0.0.0.0:{GRPC_PORT}")
    try:
        server.wait_for_termination()
    except Exception:
        server.stop(0)


def run_rest():
    """Démarre la Gateway REST FastAPI sur le port 8081."""
    logger.info(f"Passerelle REST démarrée sur http://localhost:{REST_PORT}")
    logger.info(f"Interface Web disponible sur : http://localhost:{REST_PORT}")
    logger.info(f"Swagger API disponible sur   : http://localhost:{REST_PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=REST_PORT, log_level="info")


if __name__ == "__main__":
    print("=" * 60)
    print("  Démarrage du Service Accueil (Clinique Espoir)")
    print(f"  - gRPC Core    : localhost:{GRPC_PORT}")
    print(f"  - REST Gateway : http://localhost:{REST_PORT}")
    print("=" * 60)

    # 1. Lancer gRPC dans un thread en tâche de fond
    grpc_thread = threading.Thread(target=run_grpc, daemon=True)
    grpc_thread.start()

    # Petite pause pour s'assurer que gRPC est prêt
    time.sleep(1)

    # 2. Lancer la gateway REST (processus principal)
    try:
        run_rest()
    except KeyboardInterrupt:
        print("\nArrêt des services.")
