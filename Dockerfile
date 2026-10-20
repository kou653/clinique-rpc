FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installation des packages Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création du dossier data pour SQLite
RUN mkdir -p /app/data

# Ports exposés : gRPC (50051) et REST (8081)
EXPOSE 50051 8081

# Lancement simultané gRPC + REST
CMD ["python", "start_services.py"]
