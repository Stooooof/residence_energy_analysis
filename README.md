# Analyse de la Consommation Électrique — PM01 Résidence 1

Pipeline ETL complet pour l'analyse de données réelles issues d'un compteur électrique intelligent (smart meter) installé en résidence.

---

## Structure du Projet

```
residence_energy_analysis/
│
├── data/
│   ├── raw/                        ← Fichiers CSV bruts du capteur PM01
│   ├── processed/
│   │   └── pm01_clean.csv          ← Données nettoyées (sortie ETL)
│   └── outputs/
│       └── pm01_monthly_billing.csv← Facturation mensuelle ONEE
│
├── notebooks/
│   └── 01_energy_analysis.ipynb    ← Notebook principal (ETL + analyses)
│
├── src/
│   ├── __init__.py
│   ├── config.py                   ← Constantes, chemins, tarifs, dates
│   ├── loader.py                   ← EXTRACT : chargement des CSV bruts
│   ├── cleaner.py                  ← TRANSFORM : nettoyage + calcul kWh
│   ├── analyzer.py                 ← TRANSFORM : facturation, Ramadan, vacances
│   └── visualizer.py               ← LOAD : génération des graphiques
│
├── reports/
│   └── figures/                    ← Graphiques générés (.png)
│       ├── pm01_power_consumption.png
│       ├── pm01_monthly_billing.png
│       ├── pm01_ramadan_analysis.png
│       └── pm01_vacation_analysis.png
│
├── rapport_pipeline_PM01.md        ← Rapport détaillé du pipeline
└── README.md                       ← Ce fichier
```

---

## Pipeline ETL

```
[Fichiers CSV bruts]
        ↓
   E X T R A C T           src/loader.py
   • Lister tous les CSV
   • Charger en dtype=str
   • Nettoyer les espaces
   • Convertir virgule → point
        ↓
   T R A N S F O R M       src/cleaner.py + src/analyzer.py
   • Construire timestamp
   • Supprimer doublons
   • Interpoler NaN (method=time)
   • Corriger aberrants (IQR x3)
   • Calculer énergie (kWh)
   • Facturation ONEE
   • Analyser Ramadan / Vacances
        ↓
     L O A D               src/visualizer.py
   • pm01_clean.csv
   • pm01_monthly_billing.csv
   • 4 graphiques PNG
```

---

## Données

|Paramètre|Valeur|
|---|---|
|Capteur|PM01|
|Site|Résidence 1|
|Période|Juillet 2017 → Juillet 2018|
|Pas de temps|15 minutes|
|Variable clé|`active_power_w` (Watts)|
|Encodage CSV|latin-1|
|Séparateur|`;`|
|Décimale|`,` (format européen)|

### Colonnes du capteur

|Colonne brute|Colonne nettoyée|Unité|Description|
|---|---|---|---|
|`W_PM01`|`active_power_w`|W|Puissance active ← clé|
|`A_PM01`|—|A|Courant|
|`VA_PM01`|—|VA|Puissance apparente|
|`VAR_PM01`|—|VAR|Puissance réactive|
|`VLL_PM01`|—|V|Tension ligne-ligne|
|`VLN_PM01`|—|V|Tension ligne-neutre|
|`PF_PM01`|—|—|Facteur de puissance|

---

## Résultats Clés

|Indicateur|Valeur|
|---|---|
|Mesures valides|~26 800 points|
|Consommation totale|~670 000 kWh|
|Puissance moyenne|~95 000 W|
|Puissance maximale|~210 000 W|
|Facture mensuelle moy.|À calculer (ONEE)|

---

## Installation


```bash
# Cloner ou copier le projet
cd residence_energy_analysis

# Installer les dépendances
pip install pandas numpy matplotlib

# Placer les fichiers CSV dans :
# data/raw/
```

---

## Utilisation


```bash
jupyter notebook notebooks/01_energy_analysis.ipynb
```

Exécuter les cellules dans l'ordre — chaque section correspond à une phase du pipeline ETL.

---

## Tarification ONEE (Maroc 2018)

Basse Tension Résidentiel — tranches progressives mensuelles :

|Tranche|Prix (DH/kWh)|
|---|---|
|0 – 100 kWh|0.9010|
|101 – 150 kWh|1.0560|
|151 – 200 kWh|1.1760|
|201 – 300 kWh|1.3940|
|301 – 500 kWh|1.5640|
|> 500 kWh|1.7260|

TVA : 14% — Redevance fixe : 9.00 DH/mois

---

## Périodes Analysées

|Période|Dates|
|---|---|
|Ramadan 2018|17 mai 2018 → 14 juin 2018|
|Vacances Hiver 2018|15 janvier → 31 janvier 2018|

---

_Projet réalisé dans le cadre d'un TP d'analyse de données de consommation électrique._
