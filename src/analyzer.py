# =============================================================
# analyzer.py — Analyses métier de la consommation électrique
# Facturation ONEE, Ramadan, Vacances
# =============================================================

import pandas as pd

from src.config import (
    ONEE_TARIFF_BRACKETS,
    ONEE_VAT_RATE,
    ONEE_FIXED_CHARGE_DH,
    RAMADAN_2018_START,
    RAMADAN_2018_END,
    VACATION_PERIODS,
    BILLING_OUTPUT_FILE,
)
from src.cleaner import COL_ENERGY_KWH, COL_POWER_W


# -------------------------------------------------------------
# PARTIE 1 : FACTURATION ONEE
# -------------------------------------------------------------

def compute_onee_bill(energy_kwh: float) -> dict:
    """
    Calcule la facture ONEE pour une consommation mensuelle donnée.

    Applique les tranches tarifaires progressives Basse Tension
    Résidentiel Maroc 2018, la TVA à 14% et la redevance fixe.

    Paramètres
    ----------
    energy_kwh : float
        Consommation mensuelle en kWh

    Retourne
    --------
    dict avec les clés :
        - energy_kwh      : consommation (kWh)
        - amount_ht_dh    : montant hors taxes (DH)
        - vat_dh          : TVA 14% (DH)
        - fixed_charge_dh : redevance fixe (DH)
        - total_ttc_dh    : total TTC (DH)
    """
    amount_ht     = 0.0
    remaining_kwh = energy_kwh
    previous_bound = 0

    for upper_bound, price_per_kwh in ONEE_TARIFF_BRACKETS:
        if remaining_kwh <= 0:
            break
        kwh_in_bracket = min(remaining_kwh, upper_bound - previous_bound)
        amount_ht      += kwh_in_bracket * price_per_kwh
        remaining_kwh  -= kwh_in_bracket
        previous_bound  = upper_bound

    vat_amount    = amount_ht * ONEE_VAT_RATE
    total_ttc     = amount_ht + vat_amount + ONEE_FIXED_CHARGE_DH

    return {
        "energy_kwh"      : round(energy_kwh, 2),
        "amount_ht_dh"    : round(amount_ht, 2),
        "vat_dh"          : round(vat_amount, 2),
        "fixed_charge_dh" : round(ONEE_FIXED_CHARGE_DH, 2),
        "total_ttc_dh"    : round(total_ttc, 2),
    }


def compute_monthly_billing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la consommation mensuelle et la facture ONEE estimée
    pour chaque mois de la période analysée.

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame nettoyé indexé par timestamp

    Retourne
    --------
    pd.DataFrame
        Une ligne par mois avec colonnes :
        year, month, month_label, energy_kwh,
        amount_ht_dh, vat_dh, fixed_charge_dh, total_ttc_dh
    """
    df_reset = df.reset_index()
    df_reset["year"]        = df_reset["timestamp"].dt.year
    df_reset["month"]       = df_reset["timestamp"].dt.month
    df_reset["month_label"] = df_reset["timestamp"].dt.strftime("%b %Y")

    monthly_energy = (
        df_reset
        .groupby(["year", "month", "month_label"])[COL_ENERGY_KWH]
        .sum()
        .reset_index()
        .rename(columns={COL_ENERGY_KWH: "energy_kwh"})
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )

    billing_rows = []
    for _, row in monthly_energy.iterrows():
        bill = compute_onee_bill(row["energy_kwh"])
        billing_rows.append({
            "year"            : int(row["year"]),
            "month"           : int(row["month"]),
            "month_label"     : row["month_label"],
            **bill,
        })

    df_billing = pd.DataFrame(billing_rows)

    # Sauvegarde
    df_billing.to_csv(BILLING_OUTPUT_FILE, index=False, sep=";",
                      decimal=",", encoding="utf-8-sig")
    print(f"[ANALYZE] Facturation mensuelle sauvegardée : {BILLING_OUTPUT_FILE}")

    # Résumé console
    print(f"\n{'='*55}")
    print("  RÉSUMÉ FACTURATION ONEE")
    print(f"{'='*55}")
    print(f"  Consommation totale  : {df_billing['energy_kwh'].sum():.2f} kWh")
    print(f"  Total factures       : {df_billing['total_ttc_dh'].sum():.2f} DH")
    print(f"  Facture moyenne/mois : {df_billing['total_ttc_dh'].mean():.2f} DH")
    print(f"{'='*55}\n")

    return df_billing


# -------------------------------------------------------------
# PARTIE 2 : ANALYSE RAMADAN
# -------------------------------------------------------------

def compute_hourly_profile(df_period: pd.DataFrame, label: str) -> pd.Series:
    """
    Calcule le profil horaire moyen (puissance moyenne par heure)
    d'une période donnée.

    Paramètres
    ----------
    df_period : pd.DataFrame
        Sous-ensemble du DataFrame principal pour une période
    label : str
        Nom de la période (pour affichage)

    Retourne
    --------
    pd.Series
        Puissance moyenne (W) indexée par heure (0–23)
    """
    df_copy = df_period.copy()
    df_copy["hour"] = df_copy.index.hour
    profile = df_copy.groupby("hour")[COL_POWER_W].mean()

    print(f"  [{label}]")
    print(f"    Puissance moyenne  : {df_copy[COL_POWER_W].mean():.0f} W")
    print(f"    Consommation totale: {df_copy[COL_ENERGY_KWH].sum():.2f} kWh")
    print(f"    Heure de pointe    : {profile.idxmax()}h ({profile.max():.0f} W)")

    return profile


def analyze_ramadan(df: pd.DataFrame) -> dict:
    """
    Compare la consommation pendant Ramadan 2018 avec les périodes
    avant et après (même durée que Ramadan).

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame nettoyé indexé par timestamp

    Retourne
    --------
    dict avec clés 'before', 'during', 'after'
        Chaque valeur est un pd.Series du profil horaire moyen
    """
    ramadan_duration = RAMADAN_2018_END - RAMADAN_2018_START

    period_before  = df.loc[RAMADAN_2018_START - ramadan_duration : RAMADAN_2018_START]
    period_during  = df.loc[RAMADAN_2018_START : RAMADAN_2018_END]
    period_after   = df.loc[RAMADAN_2018_END   : RAMADAN_2018_END + ramadan_duration]

    print("\n[ANALYZE] Analyse Ramadan 2018")
    print(f"  Période : {RAMADAN_2018_START.date()} → {RAMADAN_2018_END.date()}")

    profiles = {
        "before" : compute_hourly_profile(period_before, "Avant Ramadan"),
        "during" : compute_hourly_profile(period_during, "Pendant Ramadan"),
        "after"  : compute_hourly_profile(period_after,  "Après Ramadan"),
    }

    return profiles
