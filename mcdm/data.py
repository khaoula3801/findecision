import pandas as pd

COLS = ["ROI (%)", "Risque (%)", "Croissance CA (%)", "Dette/FP", "ROE (%)", "Liquidité", "ESG (/10)"]
DEMO_TYPES = dict(zip(COLS, ["max", "min", "max", "min", "max", "max", "max"]))
DEMO = pd.DataFrame(
    [
        [21, 24, 32, 1.8, 19, 1.4, 6],
        [15, 12, 21, 1.2, 14, 1.7, 9],
        [19, 20, 28, 1.5, 17, 1.5, 7],
        [17, 15, 24, 0.9, 16, 2.0, 8],
        [12, 9, 10, 0.7, 13, 2.2, 7],
        [23, 27, 38, 1.1, 22, 1.8, 6],
    ],
    index=pd.Index(["FinTech", "Green Energy", "E-commerce", "HealthTech", "Industrie", "SaaS / Tech"], name="Alternative"),
    columns=COLS,
    dtype=float,
)

SENS = {"max": "Maximiser", "min": "Minimiser"}
SENS_INV = {v: k for k, v in SENS.items()}


def validate(df, types):
    errs = []
    if df.shape[0] < 2:
        errs.append("Il faut au moins 2 alternatives.")
    if df.shape[1] < 2:
        errs.append("Il faut au moins 2 critères.")
    if df.index.duplicated().any():
        errs.append("Les noms d'alternatives doivent être uniques.")
    if any(c not in types for c in df.columns):
        errs.append("Le sens (maximiser/minimiser) manque pour certains critères.")
    if df.isna().any().any():
        errs.append("Valeurs manquantes ou non numériques dans la matrice.")
    elif (df <= 0).any().any():
        errs.append("Toutes les valeurs doivent être strictement positives.")
    return errs
