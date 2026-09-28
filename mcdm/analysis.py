import numpy as np
import pandas as pd

from . import ranking as R


def compare_methods(methods, df, types, w):
    return pd.DataFrame({m: R.run(m, df, types, w)["ranks"] for m in methods})


def weight_sweep(df, types, w, method, crit, steps=21, **params):
    grid = np.linspace(0, 1, steps)
    rest = w.drop(crit)
    rest = rest / rest.sum() if rest.sum() > 0 else rest + 1 / len(rest)
    rows = {}
    for g in grid:
        w2 = (rest * (1 - g)).copy()
        w2[crit] = g
        rows[round(g, 4)] = R.run(method, df, types, w2.reindex(w.index), **params)["ranks"]
    out = pd.DataFrame(rows).T
    out.index.name = "Poids"
    return out


def monte_carlo(df, types, w, method, n=500, noise=0.3, seed=0, **params):
    rng = np.random.default_rng(seed)
    ranks = []
    for _ in range(n):
        w2 = w * rng.uniform(1 - noise, 1 + noise, len(w))
        ranks.append(R.run(method, df, types, w2 / w2.sum(), **params)["ranks"])
    rk = pd.DataFrame(ranks)
    return pd.DataFrame({"% classé 1er": (rk == 1).mean() * 100, "Rang moyen": rk.mean(),
                         "Meilleur rang": rk.min(), "Pire rang": rk.max()}).sort_values("Rang moyen")
