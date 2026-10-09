# =============================================================
# loader.py — Phase EXTRACT du pipeline ETL
# Chargement et concaténation des fichiers CSV bruts (PM01)
# =============================================================

import pandas as pd
from pathlib import Path

from src.config import (
    RAW_DATA_DIR,
    CSV_ENCODING,
    CSV_SEPARATOR,
    NUMERIC_COLUMNS,
)


def _convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convertit les colonnes numériques du format européen (virgule)
    vers le format Python (point), et les valeurs non convertibles
    (ex: "n/a") sont automatiquement remplacées par NaN.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame brut avec colonnes en string

    Retourne
    --------
    pd.DataFrame
        DataFrame avec colonnes numériques converties en float
    """
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].str.replace(",", ".", regex=False),
                errors="coerce",
            )
    return df


def load_raw_files(source_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """
    Charge et concatène tous les fichiers CSV bruts du dossier source.

    Processus :
    1. Liste tous les fichiers .csv / .CSV du dossier
    2. Charge chaque fichier en forçant le type string (dtype=str)
       pour éviter les erreurs de parsing dues au format européen
    3. Nettoie les espaces dans les noms de colonnes et les valeurs
    4. Convertit les colonnes numériques (virgule → point)
    5. Concatène tous les DataFrames en un seul

    Paramètres
    ----------
    source_dir : Path
        Chemin vers le dossier contenant les fichiers CSV bruts.
        Par défaut : RAW_DATA_DIR défini dans config.py

    Retourne
    --------
    pd.DataFrame
        DataFrame brut combiné de tous les fichiers CSV

    Lève
    ----
    FileNotFoundError
        Si le dossier source n'existe pas
    ValueError
        Si aucun fichier CSV valide n'est trouvé
    """
    if not source_dir.exists():
        raise FileNotFoundError(f"Dossier source introuvable : {source_dir}")

    # Lister tous les fichiers CSV (majuscule et minuscule)
    csv_files = sorted(
        list(source_dir.glob("*.csv"))
    )

    if not csv_files:
        raise ValueError(f"Aucun fichier CSV trouvé dans : {source_dir}")

    print(f"[EXTRACT] {len(csv_files)} fichier(s) CSV trouvé(s) dans : {source_dir}")

    dataframes = []
    load_errors = []

    for file_path in csv_files:
        try:
            # Charger en forçant tout en string pour éviter
            # les erreurs de parsing du format européen (virgules)
            df_raw = pd.read_csv(
                file_path,
                sep=CSV_SEPARATOR,
                dtype=str,
                encoding=CSV_ENCODING,
            )

            # Nettoyer les espaces dans les noms de colonnes
            df_raw.columns = df_raw.columns.str.strip()

            # Nettoyer les espaces dans les valeurs
            for col in df_raw.columns:
                df_raw[col] = df_raw[col].str.strip()

            # Convertir les colonnes numériques
            df_raw = _convert_numeric_columns(df_raw)

            dataframes.append(df_raw)

        except Exception as error:
            load_errors.append((file_path.name, str(error)))
            print(f"  [WARN] Erreur sur {file_path.name} : {error}")

    if not dataframes:
        raise ValueError("Aucun fichier CSV n'a pu être chargé correctement.")

    # Concaténer tous les DataFrames
    df_combined = pd.concat(dataframes, ignore_index=True)

    print(f"[EXTRACT] Chargement terminé : {df_combined.shape[0]} lignes brutes")
    if load_errors:
        print(f"[EXTRACT] {len(load_errors)} fichier(s) en erreur : {[e[0] for e in load_errors]}")

    return df_combined