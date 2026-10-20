# Clinique Espoir — Service Accueil (gRPC & REST)

## 1. Description du Service Accueil
Le Service Accueil est le point d'entrée pour la gestion des patients et la transmission des demandes vers les services spécialisés distants de la clinique.

- **Port gRPC Core :** `50051`
- **Passerelle REST Gateway :** `:8081`

---

## 2. Spécification des Opérations (Selon exigences exactes)

### 1.1 Inscription du Patient
- **Service Appelé :** `Service Accueil (Interne)`
- **Description :** Enregistre un nouveau patient, génère un `idDossier` unique et stocke l'état civil ainsi que les antécédents de base.
- **Flux RPC :** `AccueilService.RegisterPatient(RegisterPatientRequest) returns (PatientResponse)`
- **Mapped REST :** `POST /v1/accueil/patients`

### 1.2 Prise de RDV Consultation
- **Service Appelé :** `Service Consultation (Distant)`
- **Description :** Planifie une consultation avec un médecin. L'Accueil transmet la demande au service Consultation qui ajoute le patient à sa liste d'attente/notification active.
- **Flux RPC Distant :** `ConsultationService.NotifyAppointment(AppointmentRequest) returns (AppointmentResponse)`
- **Mapped REST :** `POST /v1/accueil/rdv/consultation`

### 1.3 Prise de RDV Laboratoire
- **Service Appelé :** `Service Laboratoire (Distant)`
- **Description :** Lorsque le patient revient à l'accueil avec une ordonnance, l'Accueil enregistre les analyses prescrites et notifie le service Laboratoire.
- **Flux RPC Distant :** `LaboService.CreateLabOrder(LabOrderRequest) returns (LabOrderResponse)`
- **Mapped REST :** `POST /v1/accueil/rdv/laboratoire`

### 1.4 Prise de RDV Radiologie
- **Service Appelé :** `Service Radiologie (Distant)`
- **Description :** Enregistre le passage du patient pour des actes d'imagerie et transmet la liste des types de radio à exécuter au service Radiologie.
- **Flux RPC Distant :** `RadioService.CreateRadioOrder(RadioOrderRequest) returns (RadioOrderResponse)`
- **Mapped REST :** `POST /v1/accueil/rdv/radiologie`

---

## 3. Communication avec les 3 Services Distants

Les trois services (Consultation, Laboratoire, Radiologie) sont **distants**. Leurs clients respectifs sont configurés dans `grpc_services/clients/` :
- `consultation_client.py` (port distant par défaut : `50052`)
- `laboratoire_client.py` (port distant par défaut : `50053`)
- `radiologie_client.py` (port distant par défaut : `50054`)

**Gestion de l'attente de documentation :**
Tant que vos collègues n'ont pas encore fourni leurs routes et contrats :
1. Les requêtes de l'Accueil vers ces 3 services renvoient immédiatement un statut `EN_ATTENTE` avec un message d'accusé de réception explicite.
2. Le système ne plante pas et n'est pas bloqué.
3. Dès réception de leurs fichiers `.proto`, il suffira de basculer la variable d'environnement :
   ```powershell
   $env:EXTERNAL_SERVICES_ENABLED="true"
   ```

---

## 4. Lancement

```powershell
python start_services.py
```

Accès à l'interface épurée :
👉 **http://localhost:8081**

Documentation interactive OpenAPI / Swagger :
👉 **http://localhost:8081/docs**

---

## 5. Tests de validation

```powershell
python -m pytest tests -v
```
Tous les tests sont passés avec succès (9/9).
