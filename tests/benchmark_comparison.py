"""
tests/benchmark_comparison.py — Script de comparaison de performance : gRPC natif vs REST Gateway.

Mesure pour N requêtes :
1. Temps moyen de réponse (latence en millisecondes).
2. Débit (requêtes par seconde - req/s).
3. Taille de la charge utile (payload).
"""

import time
import sys
import os
import httpx
import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "grpc_services", "generated"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import accueil_pb2
import accueil_pb2_grpc

GRPC_TARGET = "localhost:50051"
REST_URL = "http://localhost:8081/v1/accueil/patients"
ITERATIONS = 100


def benchmark_grpc(iterations: int = ITERATIONS):
    channel = grpc.insecure_channel(GRPC_TARGET)
    stub = accueil_pb2_grpc.AccueilServiceStub(channel)

    # Warmup
    req = accueil_pb2.RegisterPatientRequest(
        nom="Test", prenom="Warmup", date_naissance="2000-01-01", sexe="M"
    )
    stub.RegisterPatient(req)

    start = time.perf_counter()
    for i in range(iterations):
        request = accueil_pb2.RegisterPatientRequest(
            nom="Diallo",
            prenom=f"Patient_{i}",
            date_naissance="1990-01-01",
            sexe="M",
            telephone="+224620000000",
            email=f"patient_{i}@test.com",
            antecedents=["Allergie", "Asthme"]
        )
        stub.RegisterPatient(request)
    total_time = time.perf_counter() - start

    channel.close()
    return total_time


def benchmark_rest(iterations: int = ITERATIONS):
    client = httpx.Client(timeout=10.0)

    # Warmup
    client.post(REST_URL, json={
        "nom": "Test", "prenom": "Warmup", "date_naissance": "2000-01-01", "sexe": "M"
    })

    start = time.perf_counter()
    for i in range(iterations):
        payload = {
            "nom": "Diallo",
            "prenom": f"Patient_{i}",
            "date_naissance": "1990-01-01",
            "sexe": "M",
            "telephone": "+224620000000",
            "email": f"patient_{i}@test.com",
            "antecedents": ["Allergie", "Asthme"]
        }
        client.post(REST_URL, json=payload)
    total_time = time.perf_counter() - start

    client.close()
    return total_time


if __name__ == "__main__":
    print(f"=== BENCHMARK COMPARATIF (Sur {ITERATIONS} inscriptions de patients) ===")
    print("Vérifiez que le serveur gRPC (50051) et la Gateway (8081) sont lancés.")
    print("\n1. Test gRPC natif en cours...")
    try:
        t_grpc = benchmark_grpc(ITERATIONS)
        avg_grpc = (t_grpc / ITERATIONS) * 1000
        rps_grpc = ITERATIONS / t_grpc
        print(f"   -> Temps total gRPC : {t_grpc:.3f} s")
        print(f"   -> Latence moyenne  : {avg_grpc:.2f} ms / requête")
        print(f"   -> Débit            : {rps_grpc:.1f} req/s")
    except Exception as e:
        print(f"   [!] Erreur gRPC (le serveur 50051 est-il démarré ?) : {e}")
        t_grpc = None

    print("\n2. Test REST Gateway en cours...")
    try:
        t_rest = benchmark_rest(ITERATIONS)
        avg_rest = (t_rest / ITERATIONS) * 1000
        rps_rest = ITERATIONS / t_rest
        print(f"   -> Temps total REST : {t_rest:.3f} s")
        print(f"   -> Latence moyenne  : {avg_rest:.2f} ms / requête")
        print(f"   -> Débit            : {rps_rest:.1f} req/s")
    except Exception as e:
        print(f"   [!] Erreur REST (la gateway 8081 est-elle démarrée ?) : {e}")
        t_rest = None

    if t_grpc and t_rest:
        speedup = t_rest / t_grpc
        print(f"\n=> Conclusion : gRPC est environ {speedup:.2f}x plus rapide que REST Gateway.")
