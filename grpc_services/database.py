"""
database.py — Gestion de la base de données SQLite pour le Service Accueil.
Gère :
  - Les informations administratives (état civil, antécédents)
  - Les observations médicales envoyées par Consultation (RenseignerObservations)
  - Les prescriptions médicales envoyées par Consultation (RenseignerPrescription)
"""

import sqlite3
import json
import uuid
import os
from typing import Optional, List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "clinique.db")


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion à la base de données SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise la table des dossiers patients avec colonnes observations et prescriptions."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id_dossier TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                date_naissance TEXT NOT NULL,
                sexe TEXT NOT NULL,
                adresse TEXT,
                telephone TEXT,
                antecedents TEXT,
                observations TEXT DEFAULT '[]',
                prescriptions TEXT DEFAULT '[]',
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


# Initialisation au chargement du module
init_db()


def save_patient(patient_dict: dict) -> str:
    """1.1 Inscription du Patient dans la base SQLite."""
    id_dossier = f"DOS-{uuid.uuid4().hex[:8].upper()}"
    antecedents_json = json.dumps(patient_dict.get("antecedents", []))

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO patients (id_dossier, nom, prenom, date_naissance, sexe, adresse, telephone, antecedents, observations, prescriptions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '[]', '[]')
        """, (
            id_dossier,
            patient_dict.get("nom", "").strip(),
            patient_dict.get("prenom", "").strip(),
            patient_dict.get("date_naissance", "").strip(),
            patient_dict.get("sexe", "").strip(),
            patient_dict.get("adresse", "").strip(),
            patient_dict.get("telephone", "").strip(),
            antecedents_json
        ))
        conn.commit()

    return id_dossier


def get_patient(id_dossier: str) -> Optional[Dict]:
    """Récupère un patient complet par son id_dossier."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM patients WHERE id_dossier = ?", (id_dossier,))
        row = cursor.fetchone()
        if not row:
            return None

        data = dict(row)
        for key in ["antecedents", "observations", "prescriptions"]:
            try:
                data[key] = json.loads(data.get(key) or "[]")
            except Exception:
                data[key] = []
        return data


def add_observations(id_dossier: str, new_observations: List[str]) -> bool:
    """Ajoute des observations médicales au dossier du patient."""
    p = get_patient(id_dossier)
    if not p:
        return False
    current = list(p.get("observations", []))
    current.extend(new_observations)
    with get_connection() as conn:
        conn.execute("UPDATE patients SET observations = ? WHERE id_dossier = ?", (json.dumps(current), id_dossier))
        conn.commit()
    return True


def add_prescriptions(id_dossier: str, new_prescriptions: List[str]) -> bool:
    """Ajoute des prescriptions médicales au dossier du patient."""
    p = get_patient(id_dossier)
    if not p:
        return False
    current = list(p.get("prescriptions", []))
    current.extend(new_prescriptions)
    with get_connection() as conn:
        conn.execute("UPDATE patients SET prescriptions = ? WHERE id_dossier = ?", (json.dumps(current), id_dossier))
        conn.commit()
    return True


def list_patients() -> List[Dict]:
    """Retourne la liste complète des patients."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM patients ORDER BY date_creation DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            for key in ["antecedents", "observations", "prescriptions"]:
                try:
                    data[key] = json.loads(data.get(key) or "[]")
                except Exception:
                    data[key] = []
            result.append(data)
        return result


def clear_all():
    """Vide la table des patients."""
    with get_connection() as conn:
        conn.execute("DELETE FROM patients")
        conn.commit()
