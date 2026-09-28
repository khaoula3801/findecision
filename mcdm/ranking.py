import numpy as np
import pandas as pd


def _rank(s, higher):
    return s.rank(ascending=not higher, method="min").astype(int)


def _res(scores, label, higher, steps, note=None):
    return {"scores": scores, "ranks": _rank(scores, higher), "label": label,
            "higher": higher, "steps": steps, "note": note}


def _linear(df, types):
    R = df.astype(float).copy()
    for c in R.columns:
        R[c] = df[c] / df[c].max() if types[c] == "max" else df[c].min() / df[c]
    return R


def _mm(x):
    return (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0


LIN = r"r_{ij}=\frac{x_{ij}}{\max_i x_{ij}}\ (\text{benefit}),\quad r_{ij}=\frac{\min_i x_{ij}}{x_{ij}}\ (\text{cost})"


def wsm(df, types, w, **_):
    R = _linear(df, types)
    V = R.mul(w, axis=1)
    return _res(V.sum(axis=1), "Score WSM", True, [
        ("Normalisation linéaire", LIN, R),
        ("Matrice pondérée", r"v_{ij}=w_j\,r_{ij}", V),
        ("Score", r"Q_i=\sum_j w_j r_{ij}", V.sum(axis=1).rename("WSM")),
    ])


def wpm(df, types, w, **_):
    R = _linear(df, types)
    P = R.pow(w, axis=1)
    return _res(P.prod(axis=1), "Score WPM", True, [
        ("Normalisation linéaire", LIN, R),
        ("Puissances", r"r_{ij}^{\,w_j}", P),
        ("Score", r"Q_i=\prod_j r_{ij}^{\,w_j}", P.prod(axis=1).rename("WPM")),
    ])


def waspas(df, types, w, lam=0.5, **_):
    R = _linear(df, types)
    q1 = R.mul(w, axis=1).sum(axis=1)
    q2 = R.pow(w, axis=1).prod(axis=1)
    Q = lam * q1 + (1 - lam) * q2
    return _res(Q, "Score WASPAS", True, [
        ("Normalisation linéaire", LIN, R),
        ("Scores WSM et WPM", r"Q_i^{(1)}=\sum_j w_j r_{ij},\quad Q_i^{(2)}=\prod_j r_{ij}^{w_j}",
         pd.DataFrame({"WSM": q1, "WPM": q2})),
        ("Score combiné", rf"Q_i=\lambda Q_i^{{(1)}}+(1-\lambda)Q_i^{{(2)}},\ \lambda={lam:.2f}", Q.rename("WASPAS")),
    ])


def topsis(df, types, w, **_):
    X = df.astype(float)
    R = X / np.sqrt((X ** 2).sum())
    V = R.mul(w, axis=1)
    ap = pd.Series({c: V[c].max() if types[c] == "max" else V[c].min() for c in V}, name="A+")
    am = pd.Series({c: V[c].min() if types[c] == "max" else V[c].max() for c in V}, name="A-")
    sp = np.sqrt(((V - ap) ** 2).sum(axis=1))
    sm = np.sqrt(((V - am) ** 2).sum(axis=1))
    rc = sm / (sp + sm)
    return _res(rc, "Coefficient RC", True, [
        ("Matrice normalisée", r"r_{ij}=\frac{x_{ij}}{\sqrt{\sum_i x_{ij}^2}}", R),
        ("Matrice normalisée pondérée", r"v_{ij}=w_j\,r_{ij}", V),
        ("Solutions idéales positive / négative", r"A^+=\{v_j^+\},\quad A^-=\{v_j^-\}", pd.DataFrame([ap, am])),
        ("Distances", r"S_i^{\pm}=\sqrt{\sum_j (v_{ij}-v_j^{\pm})^2}", pd.DataFrame({"S+": sp, "S-": sm})),
        ("Coefficient de proximité", r"RC_i=\frac{S_i^-}{S_i^++S_i^-}", rc.rename("RC")),
    ])


def vikor(df, types, w, v=0.5, **_):
    X = df.astype(float)
    best = pd.Series({c: X[c].max() if types[c] == "max" else X[c].min() for c in X}, name="f*")
    worst = pd.Series({c: X[c].min() if types[c] == "max" else X[c].max() for c in X}, name="f-")
    den = (best - worst).replace(0, np.nan)
    D = X.rsub(best, axis=1).div(den, axis=1).fillna(0).mul(w, axis=1)
    S, Rr = D.sum(axis=1), D.max(axis=1)
    Q = v * _mm(S) + (1 - v) * _mm(Rr)
    order = Q.sort_values().index
    dq = 1 / (len(Q) - 1)
    c1 = (Q[order[1]] - Q[order[0]]) >= dq
    c2 = order[0] in (S.idxmin(), Rr.idxmin())
    note = (f"Condition C1 (avantage acceptable, DQ = {dq:.3f}) : {'vérifiée' if c1 else 'non vérifiée'}. "
            f"Condition C2 (stabilité) : {'vérifiée' if c2 else 'non vérifiée'}.")
    return _res(Q, "Indice Q (plus petit = meilleur)", False, [
        ("Valeurs idéale et anti-idéale", r"f_j^*,\ f_j^-", pd.DataFrame([best, worst])),
        ("Écarts pondérés", r"d_{ij}=w_j\frac{f_j^*-x_{ij}}{f_j^*-f_j^-}", D),
        ("Mesures S et R", r"S_i=\sum_j d_{ij},\quad R_i=\max_j d_{ij}", pd.DataFrame({"S": S, "R": Rr})),
        ("Indice Q", rf"Q_i=v\frac{{S_i-S^*}}{{S^--S^*}}+(1-v)\frac{{R_i-R^*}}{{R^--R^*}},\ v={v:.2f}", Q.rename("Q")),
    ], note)


RANKING = {"WSM": wsm, "WPM": wpm, "WASPAS": waspas, "TOPSIS": topsis, "VIKOR": vikor}


def run(method, df, types, w, **params):
    return RANKING[method](df, types, w, **params)
