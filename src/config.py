# =============================================================
# config.py — Configuration centrale du projet ETL
# Résidence 1 — Analyse de Consommation Électrique (PM01)
# =============================================================
# Toutes les constantes, chemins et paramètres du projet
# sont définis ici. Ne pas coder en dur ces valeurs ailleurs.
# =============================================================

from pathlib import Path
import pandas as pd

# -------------------------------------------------------------
# CHEMINS DU PROJET
# -------------------------------------------------------------

# Racine du projet (dossier parent de /src)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Données brutes (fichiers CSV originaux du capteur PM01)
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Données traitées (CSV nettoyé après pipeline ETL)
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Résultats d'analyse (factures, statistiques exportées)
OUTPUTS_DATA_DIR = PROJECT_ROOT / "data" / "outputs"

# Graphiques générés
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# Fichiers de sortie
CLEAN_DATA_FILE      = PROCESSED_DATA_DIR / "pm01_clean.csv"
BILLING_OUTPUT_FILE  = OUTPUTS_DATA_DIR   / "pm01_monthly_billing.csv"

# Créer les dossiers s'ils n'existent pas
for _dir in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUTS_DATA_DIR, FIGURES_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------
# PARAMÈTRES DU CAPTEUR PM01
# -------------------------------------------------------------

# Identifiant du compteur
METER_ID   = "PM01"
SITE_NAME  = "Residence 1"

# Colonnes brutes du fichier CSV capteur
COL_DATE   = "DATE"
COL_TIME   = "TIME"
COL_CURRENT        = "A_PM01"      # Courant (Ampères)
COL_ACTIVE_POWER   = "W_PM01"      # Puissance active (Watts)  ← variable principale
COL_APPARENT_POWER = "VA_PM01"     # Puissance apparente (VA)
COL_REACTIVE_POWER = "VAR_PM01"    # Puissance réactive (VAR)
COL_VOLTAGE_LL     = "VLL_PM01"    # Tension ligne-ligne (V)
COL_VOLTAGE_LN     = "VLN_PM01"    # Tension ligne-neutre (V)
COL_POWER_FACTOR   = "PF_PM01"     # Facteur de puissance

# Liste des colonnes numériques à convertir au chargement
NUMERIC_COLUMNS = [
    COL_CURRENT,
    COL_ACTIVE_POWER,
    COL_APPARENT_POWER,
    COL_REACTIVE_POWER,
    COL_VOLTAGE_LL,
    COL_VOLTAGE_LN,
    COL_POWER_FACTOR,
]

# Format de date dans les fichiers CSV
DATE_FORMAT = "%d/%m/%Y %H:%M:%S"

# Pas de temps de mesure (15 minutes = 0.25 heure)
TIME_STEP_HOURS = 0.25   # utilisé pour le calcul kWh : E = P(kW) × 0.25h

# Encodage des fichiers CSV capteur
CSV_ENCODING  = "latin-1"
CSV_SEPARATOR = ";"
CSV_DECIMAL   = ","


# -------------------------------------------------------------
# PARAMÈTRES DE NETTOYAGE (Data Cleaning)
# -------------------------------------------------------------

# Facteur IQR pour la détection des valeurs aberrantes
# 3.0 = conservateur (ne supprime que les vraies anomalies)
IQR_FACTOR = 3.0

# Méthode d'interpolation des valeurs manquantes
INTERPOLATION_METHOD = "time"   # tient compte des vrais intervalles temporels


# -------------------------------------------------------------
# TARIFICATION ONEE MAROC 2018
# Basse Tension Résidentiel — Tranches progressives mensuelles
# -------------------------------------------------------------

# Structure : (borne_superieure_kWh, prix_DH_par_kWh)
# La dernière tranche a une borne infinie (float("inf"))
ONEE_TARIFF_BRACKETS = [
    (100,          0.9010),   # Tranche 1 :   0 – 100 kWh
    (150,          1.0560),   # Tranche 2 : 101 – 150 kWh
    (200,          1.1760),   # Tranche 3 : 151 – 200 kWh
    (300,          1.3940),   # Tranche 4 : 201 – 300 kWh
    (500,          1.5640),   # Tranche 5 : 301 – 500 kWh
    (float("inf"), 1.7260),   # Tranche 6 :  > 500 kWh
]

ONEE_VAT_RATE          = 0.14   # TVA 14%
ONEE_FIXED_CHARGE_DH   = 9.00   # Redevance fixe mensuelle (DH)


# -------------------------------------------------------------
# PÉRIODES D'ANALYSE SPÉCIALES
# -------------------------------------------------------------

# Ramadan 2018 (Maroc)
RAMADAN_2018_START = pd.Timestamp("2018-05-17")
RAMADAN_2018_END   = pd.Timestamp("2018-06-14")

# Périodes de vacances à analyser
VACATION_PERIODS = {
    "Vacances Hiver Jan 2018" : ("2018-01-20", "2018-01-31"),
    "Vacances Été Juil 2018"  : ("2018-07-01", "2018-07-31"),
    "Vacances Été Août 2018"  : ("2018-08-01", "2018-08-31"),
}


# -------------------------------------------------------------
# PARAMÈTRES DE VISUALISATION
# -------------------------------------------------------------

# Couleurs principales
COLOR_POWER      = "steelblue"    # courbe puissance (W)
COLOR_ENERGY     = "darkorange"   # courbe énergie cumulée (kWh)
COLOR_BILLING    = "darkorange"   # barres facture
COLOR_NORMAL     = "steelblue"    # profil horaire normal
COLOR_RAMADAN    = "green"        # profil horaire Ramadan
COLOR_BEFORE     = "steelblue"    # période avant Ramadan
COLOR_AFTER      = "darkorange"   # période après Ramadan

# Résolution des graphiques sauvegardés (DPI)
FIGURE_DPI = 150