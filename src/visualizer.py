# =============================================================
# visualizer.py — Visualisations de la consommation électrique
# Toutes les fonctions de génération de graphiques (PM01)
# =============================================================

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from src.config import (
    FIGURES_DIR,
    FIGURE_DPI,
    COLOR_POWER,
    COLOR_ENERGY,
    COLOR_BILLING,
    COLOR_NORMAL,
    COLOR_RAMADAN,
    COLOR_BEFORE,
    COLOR_AFTER,
    SITE_NAME,
    METER_ID,
    RAMADAN_2018_START,
    RAMADAN_2018_END,
)
from src.cleaner import COL_POWER_W, COL_ENERGY_KWH, COL_ENERGY_CUM_KWH


def _save_figure(fig: plt.Figure, filename: str) -> None:
    """Sauvegarde un graphique dans le dossier reports/figures/."""
    output_path = FIGURES_DIR / filename
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches="tight")
    print(f"  [PLOT] Graphique sauvegardé : {output_path}")
    plt.show()
    plt.close(fig)


# -------------------------------------------------------------
# GRAPHIQUE 1 : Puissance et consommation cumulée globale
# -------------------------------------------------------------

def plot_power_and_cumulative(df: pd.DataFrame) -> None:
    """
    Trace deux courbes :
    - Puissance active instantanée (W) au pas de 15 minutes
    - Consommation énergétique cumulée (kWh) sur toute la période

    Paramètres
    ----------
    df : pd.DataFrame
        DataFrame nettoyé indexé par timestamp
    """
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    fig.suptitle(
        f"Consommation Électrique — {METER_ID} ({SITE_NAME})",
        fontsize=14, fontweight="bold"
    )

    # --- Courbe 1 : Puissance active (W) ---
    ax1 = axes[0]
    ax1.plot(df.index, df[COL_POWER_W],
             color=COLOR_POWER, linewidth=0.8, label="Puissance active (W)")
    ax1.fill_between(df.index, df[COL_POWER_W], alpha=0.15, color=COLOR_POWER)
    ax1.set_title("Puissance Active — pas de 15 minutes")
    ax1.set_ylabel("Puissance (W)")
    ax1.set_xlabel("Temps")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # --- Courbe 2 : Consommation cumulée (kWh) ---
    ax2 = axes[1]
    ax2.plot(df.index, df[COL_ENERGY_CUM_KWH],
             color=COLOR_ENERGY, linewidth=1.5, label="Consommation cumulée (kWh)")
    ax2.set_title("Consommation Cumulée (kWh)")
    ax2.set_ylabel("Consommation (kWh)")
    ax2.set_xlabel("Temps")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
    ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    _save_figure(fig, "pm01_power_consumption.png")


# -------------------------------------------------------------
# GRAPHIQUE 2 : Consommation mensuelle et facturation ONEE
# -------------------------------------------------------------

def plot_monthly_billing(df_billing: pd.DataFrame) -> None:
    """
    Trace deux graphiques en barres :
    - Consommation mensuelle (kWh)
    - Facture mensuelle estimée TTC (DH)

    Paramètres
    ----------
    df_billing : pd.DataFrame
        DataFrame de facturation issu de analyzer.compute_monthly_billing()
    """
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle(
        f"Analyse Mensuelle — {SITE_NAME} ({METER_ID})",
        fontsize=13, fontweight="bold"
    )

    x            = range(len(df_billing))
    month_labels = df_billing["month_label"]

    # --- Barres 1 : Consommation mensuelle (kWh) ---
    ax1 = axes[0]
    bars1 = ax1.bar(x, df_billing["energy_kwh"],
                    color=COLOR_POWER, alpha=0.8, label="Consommation (kWh)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(month_labels, rotation=45, ha="right")
    ax1.set_ylabel("Consommation (kWh)")
    ax1.set_title("Consommation Mensuelle (kWh)")
    ax1.grid(True, alpha=0.3, axis="y")

    for bar, val in zip(bars1, df_billing["energy_kwh"]):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 50,
                 f"{val:.0f}", ha="center", va="bottom", fontsize=8)

    # --- Barres 2 : Facture mensuelle TTC (DH) ---
    ax2 = axes[1]
    bars2 = ax2.bar(x, df_billing["total_ttc_dh"],
                    color=COLOR_BILLING, alpha=0.8, label="Facture TTC (DH)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(month_labels, rotation=45, ha="right")
    ax2.set_ylabel("Montant (DH)")
    ax2.set_title("Facture Mensuelle Estimée — Tarif ONEE (DH TTC)")
    ax2.grid(True, alpha=0.3, axis="y")

    for bar, val in zip(bars2, df_billing["total_ttc_dh"]):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 5,
                 f"{val:.0f} DH", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    _save_figure(fig, "pm01_monthly_billing.png")


# -------------------------------------------------------------
# GRAPHIQUE 3 : Profil horaire Ramadan
# -------------------------------------------------------------

def plot_ramadan_analysis(ramadan_profiles: dict) -> None:
    """
    Trace les profils horaires moyens avant, pendant et après Ramadan.

    Paramètres
    ----------
    ramadan_profiles : dict
        Dictionnaire avec clés 'before', 'during', 'after'
        Chaque valeur est un pd.Series (puissance moyenne par heure)
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.set_title(
        "Profil Horaire Moyen — Avant / Pendant / Après Ramadan 2018",
        fontsize=12, fontweight="bold"
    )

    plot_config = [
        ("before", "Avant Ramadan",   COLOR_BEFORE,  "-"),
        ("during", "Pendant Ramadan", COLOR_RAMADAN, "-"),
        ("after",  "Après Ramadan",   COLOR_AFTER,   "--"),
    ]

    for key, label, color, linestyle in plot_config:
        if key in ramadan_profiles:
            profile = ramadan_profiles[key]
            ax.plot(profile.index, profile.values,
                    color=color, linestyle=linestyle,
                    linewidth=2, marker="o", markersize=4, label=label)

    # Annotations Ftour et Shour
    ymax = ax.get_ylim()[1]
    ax.axvline(x=19, color=COLOR_RAMADAN, linestyle=":", alpha=0.7)
    ax.text(19.1, ymax * 0.92, "Ftour (~19h)",
            color=COLOR_RAMADAN, fontsize=9)
    ax.axvline(x=3, color="purple", linestyle=":", alpha=0.7)
    ax.text(3.1, ymax * 0.92, "Shour (~3h)",
            color="purple", fontsize=9)

    ax.set_xlabel("Heure de la journée")
    ax.set_ylabel("Puissance moyenne (W)")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h}h" for h in range(24)], rotation=45)
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    _save_figure(fig, "pm01_ramadan_analysis.png")
