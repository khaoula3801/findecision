import numpy as np
import pandas as pd
from scipy.optimize import linprog

RI = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
CI_BWM = {1: 0.0, 2: 0.44, 3: 1.0, 4: 1.63, 5: 2.30, 6: 3.0, 7: 3.73, 8: 4.47, 9: 5.23}


def _out(w, steps=None, info=None):
    return {"weights": w, "steps": steps or [], "info": info}


def equal(criteria):
    return _out(pd.Series(1 / len(criteria), index=criteria))


def entropy(df):
    X = df.astype(float)
    P = X / X.sum()
    E = -(P * np.log(P)).sum() / np.log(len(X))
    d = 1 - E
    w = d / d.sum() if d.sum() > 1e-12 else pd.Series(1 / len(d), index=d.index)
    steps = [
        ("Matrice des proportions", r"p_{ij}=\frac{x_{ij}}{\sum_i x_{ij}}", P),
        ("Entropie de chaque critère", r"E_j=-\frac{1}{\ln m}\sum_i p_{ij}\ln p_{ij}", E.rename("E_j")),
        ("Divergence et poids", r"d_j=1-E_j,\quad w_j=\frac{d_j}{\sum_k d_k}", pd.DataFrame({"d_j": d, "w_j": w})),
    ]
    return _out(w, steps)


def critic(df, types):
    X = df.astype(float)
    N = pd.DataFrame(index=X.index, columns=X.columns, dtype=float)
    for c in X.columns:
        lo, hi = X[c].min(), X[c].max()
        rng = (hi - lo) or 1.0
        N[c] = (X[c] - lo) / rng if types[c] == "max" else (hi - X[c]) / rng
    sigma = N.std(ddof=1)
    corr = N.corr().fillna(0)
    C = sigma * (1 - corr).sum()
    w = C / C.sum() if C.sum() > 1e-12 else pd.Series(1 / len(C), index=C.index)
    steps = [
        ("Matrice normalisée (min-max)", r"r_{ij}=\frac{x_{ij}-x_j^{-}}{x_j^{+}-x_j^{-}}", N),
        ("Corrélations entre critères", r"\rho_{jk}", corr),
        ("Information et poids", r"C_j=\sigma_j\sum_k(1-\rho_{jk}),\quad w_j=\frac{C_j}{\sum_k C_k}",
         pd.DataFrame({"sigma_j": sigma, "C_j": C, "w_j": w})),
    ]
    return _out(w, steps)


def ahp(A, crit):
    A = np.array(A, float)
    n = len(A)
    vals, vecs = np.linalg.eig(A)
    i = int(np.argmax(vals.real))
    lam = vals[i].real
    w = np.abs(vecs[:, i].real)
    w = w / w.sum()
    ci = (lam - n) / (n - 1) if n > 2 else 0.0
    ri = RI.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0
    verdict = "cohérent" if cr < 0.10 else "à revoir (CR ≥ 0,10)"
    info = f"λmax = {lam:.3f} | CI = {ci:.3f} | CR = {cr:.3f} : jugements {verdict}."
    steps = [
        ("Matrice de comparaison par paires", r"a_{ji}=1/a_{ij}", pd.DataFrame(A, index=crit, columns=crit)),
        ("Vecteur propre principal", r"A\,w=\lambda_{max}\,w", pd.Series(w, index=crit, name="w_j")),
    ]
    return _out(pd.Series(w, index=crit), steps, info)


def bwm(crit, best, worst, bo, ow):
    n = len(crit)
    ib, iw = crit.index(best), crit.index(worst)
    rows = []
    for j in range(n):
        r = np.zeros(n + 1)
        r[ib] += 1
        r[j] -= bo[crit[j]]
        rows += [np.append(r[:-1], -1), np.append(-r[:-1], -1)]
        r = np.zeros(n + 1)
        r[j] += 1
        r[iw] -= ow[crit[j]]
        rows += [np.append(r[:-1], -1), np.append(-r[:-1], -1)]
    c = np.zeros(n + 1)
    c[-1] = 1
    res = linprog(c, A_ub=np.array(rows), b_ub=np.zeros(len(rows)),
                  A_eq=[[1] * n + [0]], b_eq=[1], bounds=[(0, None)] * (n + 1), method="highs")
    if not res.success:
        return None
    w = pd.Series(res.x[:-1], index=crit)
    xi = res.x[-1]
    ci = CI_BWM.get(int(round(bo[worst])), 5.23)
    cr = xi / ci if ci > 0 else 0.0
    info = f"ξ* = {xi:.4f} | ratio de consistance = {cr:.3f} (proche de 0 = cohérent)."
    steps = [
        ("Vecteurs de comparaison", r"A_B,\;A_W", pd.DataFrame({"Best-to-Others": pd.Series(bo), "Others-to-Worst": pd.Series(ow)})),
        ("Programme linéaire", r"\min \xi\ \text{s.c.}\ |w_B-a_{Bj}w_j|\le\xi,\ |w_j-a_{jW}w_W|\le\xi", w.rename("w_j")),
    ]
    return _out(w, steps, info)
