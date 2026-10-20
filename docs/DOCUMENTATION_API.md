# Documentation d'Intégration — Service Accueil (Clinique Espoir)

Cette documentation décrit toutes les routes, fonctions et données échangées avec le Service Accueil.

---

## 1. Informations de Connexion

- Protocole gRPC Core : localhost:50051 (ou adresse ngrok TCP fournie)
- Passerelle REST HTTP : http://localhost:8081 (ou adresse ngrok HTTPS fournie)
- Interface de test Swagger UI : http://localhost:8081/docs

---

## 2. Fonctions gRPC (Pour Consultation, Laboratoire, Radiologie)

### A. Récupérer les données des patients : GetPatientsByIDs
Utilisé par le Service Consultation pour obtenir le nom et prénom des patients.

- Service gRPC à appeler : clinique.Accueil
- Méthode RPC : GetPatientsByIDs(PatientsRequest) returns (PatientsResponse)

Données à envoyer (PatientsRequest) :
- id_dossiers : liste de chaînes contenant les identifiants des dossiers (Exemple : ["DOS-1A2B3C4D", "DOS-9E8F7A6B"])

Données reçues en retour (PatientsResponse) :
- patients : liste d'objets Patient contenant :
  - id_dossier (chaîne, ex: "DOS-1A2B3C4D")
  - nom (chaîne, ex: "Dupont")
  - prenom (chaîne, ex: "Jean")

---

### B. Enregistrer les observations d'une consultation : RenseignerObservations
Utilisé par le Service Consultation à la fin d'une consultation.

- Service gRPC à appeler : clinique.Accueil
- Méthode RPC : RenseignerObservations(ObservationsRequest) returns (Ack)

Données à envoyer (ObservationsRequest) :
- id_dossier (chaîne, obligatoire) : identifiant unique du patient (Exemple : "DOS-1A2B3C4D")
- observations (liste de chaînes, obligatoire) : notes médicales du médecin (Exemple : ["Patient en bonne forme", "Tension artérielle 12/8"])

Données reçues en retour (Ack) :
- ok (booléen) : true si enregistré avec succès, false en cas d'erreur
- message (chaîne) : "Observations enregistrées avec succès dans le dossier patient"

---

### C. Enregistrer les prescriptions médicales : RenseignerPrescription
Utilisé par le Service Consultation pour ajouter des ordonnances au dossier du patient.

- Service gRPC à appeler : clinique.Accueil
- Méthode RPC : RenseignerPrescription(PrescriptionRequest) returns (Ack)

Données à envoyer (PrescriptionRequest) :
- id_dossier (chaîne, obligatoire) : identifiant unique du patient (Exemple : "DOS-1A2B3C4D")
- lignes (liste de chaînes, obligatoire) : liste des médicaments et posologies (Exemple : ["Paracétamol 1g 3x/jour", "Vitamine C"])

Données reçues en retour (Ack) :
- ok (booléen) : true si enregistré avec succès, false en cas d'erreur
- message (chaîne) : "Prescriptions enregistrées avec succès dans le dossier patient"

---

## 3. Routes REST (HTTP / JSON)

### 3.1. Inscription d'un Patient (1.1)
- Méthode HTTP : POST
- Route : /v1/accueil/patients

Données à envoyer (JSON) :
{
  "nom": "Dupont",
  "prenom": "Jean",
  "date_naissance": "1990-05-15",
  "sexe": "M",
  "adresse": "12 Rue de la Paix, Paris",
  "telephone": "+33612345678",
  "antecedents": ["Allergie aspirine", "Diabète"]
}

Données reçues en retour (Code 201 Created) :
{
  "id_dossier": "DOS-7F3A9C12",
  "nom": "Dupont",
  "prenom": "Jean",
  "date_naissance": "1990-05-15",
  "sexe": "M",
  "adresse": "12 Rue de la Paix, Paris",
  "telephone": "+33612345678",
  "antecedents": ["Allergie aspirine", "Diabète"],
  "statut": "ENREGISTRE",
  "message": "Patient Jean Dupont enregistré avec succès."
}

---

### 3.2. Récupérer un Patient par son ID
- Méthode HTTP : GET
- Route : /v1/accueil/patients/{id_dossier}
- Exemple : GET /v1/accueil/patients/DOS-7F3A9C12

Données à envoyer :
- Aucune donnée dans le corps (juste l'id_dossier dans l'URL)

Données reçues en retour (Code 200 OK) :
{
  "id_dossier": "DOS-7F3A9C12",
  "nom": "Dupont",
  "prenom": "Jean",
  "date_naissance": "1990-05-15",
  "sexe": "M",
  "adresse": "12 Rue de la Paix, Paris",
  "telephone": "+33612345678",
  "antecedents": ["Allergie aspirine", "Diabète"],
  "statut": "TROUVE",
  "message": "Patient trouvé."
}

---

### 3.3. Lister tous les Patients
- Méthode HTTP : GET
- Route : /v1/accueil/patients

Données à envoyer :
- Aucune

Données reçues en retour (Code 200 OK) :
- Une liste JSON de tous les dossiers patients enregistrés : [ { ... }, { ... } ]

---

### 3.4. Prise de RDV Consultation (1.2)
- Méthode HTTP : POST
- Route : /v1/accueil/rdv/consultation

Données à envoyer (JSON) :
{
  "id_dossier": "DOS-7F3A9C12",
  "medecin_id": "MED-DR-KONE",
  "date_rdv": "2026-11-05T09:30:00",
  "motif": "Consultation générale",
  "priorite": "NORMAL"
}

Données reçues en retour (Code 200 OK) :
{
  "id_rdv": "RDV-58473921",
  "id_dossier": "DOS-7F3A9C12",
  "medecin_id": "MED-DR-KONE",
  "date_rdv": "2026-11-05T09:30:00",
  "statut": "CONFIRME",
  "message": "RDV confirmé avec succès par le Service Consultation (id_rdv: RDV-58473921)"
}

---

### 3.5. Prise de RDV Laboratoire (1.3)
- Méthode HTTP : POST
- Route : /v1/accueil/rdv/laboratoire

Données à envoyer (JSON) :
{
  "id_dossier": "DOS-7F3A9C12",
  "medecin_prescripteur_id": "MED-DR-KONE",
  "analyses_prescrites": ["NFS", "Glycémie à jeun", "Bilan rénal"],
  "priorite": "NORMAL",
  "ordonnance_ref": "ORD-2026-089"
}

Données reçues en retour (Code 200 OK) :
{
  "id_ordre_labo": "LAB-98124501",
  "id_dossier": "DOS-7F3A9C12",
  "statut": "EN_ATTENTE",
  "message": "Demande transmise au Service Laboratoire."
}

---

### 3.6. Prise de RDV Radiologie (1.4)
- Méthode HTTP : POST
- Route : /v1/accueil/rdv/radiologie

Données à envoyer (JSON) :
{
  "id_dossier": "DOS-7F3A9C12",
  "medecin_prescripteur_id": "MED-DR-KONE",
  "types_radio": ["Radiographie pulmonaire", "Scanner abdominal"],
  "priorite": "NORMAL",
  "notes": "Cliché face et profil"
}

Données reçues en retour (Code 200 OK) :
{
  "id_ordre_radio": "RAD-34091287",
  "id_dossier": "DOS-7F3A9C12",
  "statut": "EN_ATTENTE",
  "message": "Demande transmise au Service Radiologie."
}
