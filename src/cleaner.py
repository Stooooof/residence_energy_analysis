# =============================================================
# cleaner.py — Phase TRANSFORM du pipeline ETL (Nettoyage)
# Nettoyage, validation et calcul de la consommation (PM01)
# =============================================================

import numpy as np
import pandas as pd

from src.config import (
    COL_DATE,
    COL_TIME,
    COL_ACTIVE_POWER,
    DATE_FORMAT,
    IQR_FACTOR,
    INTERPOLATION_METHOD,
    TIME_STEP_HOURS,
    CLEAN_DATA_FILE,
)

# Nom des colonnes produites par ce module
COL_DATETIME       = "timestamp"
COL_POWER_W        = "active_power_w"
COL_ENERGY_KWH     = "energy_kwh"
COL_ENERGY_CUM_KWH = "energy_cumulative_kwh"


def build_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fusionne les colonnes DATE et TIME en une colonne timestamp
    de type datetime64, et supprime les lignes avec timestamp invalide.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame brut avec colonnes DATE et TIME en string

    Retourne
    --------
    pd.DataFrame
        DataFrame avec colonne 'timestamp' ajoutée
    """
    df[COL_DATETIME] = pd.to_datetime(
        df[COL_DATE] + " " + df[COL_TIME],
        format=DATE_FORMAT,
        errors="coerce",      # dates invalides → NaT (pas d'erreur)
    )

    n_invalid = df[COL_DATETIME].isna().sum()
    if n_invalid > 0:
        print(f"  [WARN] {n_invalid} timestamp(s) invalide(s) supprimé(s)")
        df = df.dropna(subset=[COL_DATETIME])

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Supprime les lignes dupliquées sur le timestamp.
    Les doublons proviennent du chevauchement entre fichiers CSV.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame avec colonne timestamp

    Retourne
    --------
    pd.DataFrame
        DataFrame sans doublons temporels
    """
    count_before = len(df)
    df = df.drop_duplicates(subset=[COL_DATETIME])
    count_removed = count_before - len(df)

    print(f"  [INFO] Doublons supprimés : {count_removed} "
          f"({count_removed / count_before * 100:.1f}%)")

    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomme les colonnes brutes du capteur vers des noms
    standardisés et lisibles.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame avec colonnes brutes du capteur

    Retourne
    --------
    pd.DataFrame
        DataFrame avec colonnes renommées
    """
    rename_map = {
        COL_ACTIVE_POWER : COL_POWER_W,
    }
    return df.rename(columns=rename_map)


def interpolate_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Interpole les valeurs manquantes (NaN) dans la colonne
    de puissance active en utilisant l'interpolation temporelle.

    L'interpolation temporelle (method="time") tient compte des
    vrais intervalles de temps entre les mesures, contrairement
    à l'interpolation linéaire classique qui suppose des intervalles égaux.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame indexé par timestamp avec colonne active_power_w

    Retourne
    --------
    pd.DataFrame
        DataFrame avec valeurs manquantes interpolées
    """
    n_missing = df[COL_POWER_W].isna().sum()
    pct_missing = n_missing / len(df) * 100
    print(f"  [INFO] Valeurs manquantes : {n_missing} ({pct_missing:.1f}%) → interpolation '{INTERPOLATION_METHOD}'")

    df[COL_POWER_W] = df[COL_POWER_W].interpolate(method=INTERPOLATION_METHOD)

    n_remaining = df[COL_POWER_W].isna().sum()
    print(f"  [INFO] NaN restants après interpolation : {n_remaining}")

    return df


def remove_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte et corrige les valeurs aberrantes dans la colonne
    de puissance active via la méthode IQR (Interquartile Range).

    Méthode :
    - Q1 = 25e percentile, Q3 = 75e percentile
    - IQR = Q3 - Q1
    - Borne inférieure = max(0, Q1 - IQR_FACTOR × IQR)
    - Borne supérieure = Q3 + IQR_FACTOR × IQR
    - Les valeurs hors bornes → NaN → ré-interpolées

    La puissance ne pouvant pas être négative, la borne
    inférieure est forcée à 0.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame indexé par timestamp

    Retourne
    --------
    pd.DataFrame
        DataFrame avec valeurs aberrantes corrigées
    """
    q1  = df[COL_POWER_W].quantile(0.25)
    q3  = df[COL_POWER_W].quantile(0.75)
    iqr = q3 - q1

    lower_bound = max(0, q1 - IQR_FACTOR * iqr)
    upper_bound = q3 + IQR_FACTOR * iqr

    mask_outliers = (df[COL_POWER_W] < lower_bound) | (df[COL_POWER_W] > upper_bound)
    n_outliers = mask_outliers.sum()

    print(f"  [INFO] Valeurs aberrantes détectées : {n_outliers} "
          f"(bornes : [{lower_bound:.0f} W — {upper_bound:.0f} W])")

    df.loc[mask_outliers, COL_POWER_W] = np.nan
    df[COL_POWER_W] = df[COL_POWER_W].interpolate(method=INTERPOLATION_METHOD)

    return df


def compute_energy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule l'énergie consommée à chaque pas de temps (kWh)
    et la consommation cumulée depuis le début de la période.

    Formule : E (kWh) = P (W) / 1000 × Δt (h)
    Avec Δt = TIME_STEP_HOURS = 0.25 h (pas de 15 minutes)

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame avec colonne active_power_w

    Retourne
    --------
    pd.DataFrame
        DataFrame avec colonnes energy_kwh et energy_cumulative_kwh
    """
    df[COL_ENERGY_KWH]     = (df[COL_POWER_W] / 1000) * TIME_STEP_HOURS
    df[COL_ENERGY_CUM_KWH] = df[COL_ENERGY_KWH].cumsum()

    print(f"  [INFO] Consommation totale   : {df[COL_ENERGY_KWH].sum():.2f} kWh")
    print(f"  [INFO] Puissance moyenne     : {df[COL_POWER_W].mean():.0f} W")
    print(f"  [INFO] Puissance maximale    : {df[COL_POWER_W].max():.0f} W")

    return df


def save_clean_data(df: pd.DataFrame) -> None:
    """
    Sauvegarde le DataFrame nettoyé en CSV dans le dossier processed/.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame nettoyé et traité
    """
    df.to_csv(CLEAN_DATA_FILE, sep=";", decimal=",", encoding="utf-8-sig")
    print(f"  [LOAD] Données sauvegardées : {CLEAN_DATA_FILE}")


def run_cleaning_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Exécute le pipeline de nettoyage complet (phase TRANSFORM).

    Étapes :
    1. Construction du timestamp (DATE + TIME → datetime)
    2. Suppression des doublons temporels
    3. Tri chronologique
    4. Renommage des colonnes
    5. Mise en index datetime (requis pour interpolation temporelle)
    6. Interpolation des valeurs manquantes
    7. Détection et correction des valeurs aberrantes
    8. Calcul de la consommation en kWh
    9. Sauvegarde du CSV nettoyé

    Paramètres
    ----------
    df_raw : pd.DataFrame
        DataFrame brut issu de loader.load_raw_files()

    Retourne
    --------
    pd.DataFrame
        DataFrame propre, indexé par timestamp, prêt pour l'analyse
    """
    print("\n[TRANSFORM] Début du nettoyage...")

    df = build_timestamp(df_raw)
    df = remove_duplicates(df)

    # Tri chronologique
    df = df.sort_values(COL_DATETIME).reset_index(drop=True)
    print(f"  [INFO] Données triées : {df.shape[0]} lignes")

    df = rename_columns(df)

    # Mettre timestamp en index (obligatoire pour interpolation temporelle)
    df = df.set_index(COL_DATETIME)

    df = interpolate_missing(df)
    df = remove_outliers(df)
    df = compute_energy(df)

    save_clean_data(df)

    print(f"[TRANSFORM] Nettoyage terminé : {df.shape[0]} lignes propres\n")

    return df