import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from mcdm import analysis as A, data as D, ranking as R, weighting as W

PALETTE = ["#A7C7E7", "#F4A9C0", "#98D8C1", "#F9C784", "#B5A6E0", "#C5E1A5", "#F7B7A3", "#9AD0D3"]
INK = "#4A4468"
MODES = ["Démonstration", "Personnalisé", "Import CSV"]

st.set_page_config(page_title="FinDecision", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp {background: linear-gradient(180deg,#FBF9FF 0%,#F4F8FF 100%);}
section[data-testid="stSidebar"] {background: linear-gradient(180deg,#EDE7FA 0%,#E2F0F9 100%);}
h1,h2,h3,h4 {color:#4A4468; font-weight:600;}
#MainMenu, footer {visibility:hidden;}

/* ---- en-tête fixe ---- */
.topbar {position:sticky; top:0; z-index:999; margin:-1rem -1rem 1.1rem -1rem; padding:1.1rem 1.8rem .9rem;
  background:rgba(251,249,255,.9); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border-bottom:1px solid #EDE7FA; display:flex; align-items:baseline; gap:.7rem; flex-wrap:wrap;}
.topbar .brand {font-size:2.1rem; font-weight:800; letter-spacing:.01em;
  background:linear-gradient(90deg,#B5A6E0,#F4A9C0 60%,#F9C784); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; color:#4A4468;}
.topbar .tag {font-size:.92rem; color:#8B84A8; font-weight:500;}

/* ---- barre d'onglets : stable, ne bouge plus, ancrée sous l'en-tête ---- */
div[data-testid="stTabs"] {position:relative;}
div[data-testid="stTabs"] > div:first-child {position:sticky; top:4.3rem; z-index:998;
  background:rgba(251,249,255,.92); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border-radius:14px; padding:.3rem; border:1px solid #EDE7FA; box-shadow:0 2px 10px rgba(150,140,190,.08);}
button[data-baseweb="tab"] {color:#6B6488; font-weight:500; border-radius:10px; transition:background .15s ease, color .15s ease;}
button[data-baseweb="tab"]:hover {background:#F3EEFC; color:#4A4468;}
button[data-baseweb="tab"][aria-selected="true"] {color:#4A4468; background:#EDE7FA; border-radius:10px; font-weight:600;}
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] {display:none;}
div[data-testid="stTabs"] div[data-baseweb="tab-border"] {display:none;}
div[data-testid="stTabsContent"] {animation:fadein .25s ease;}
@keyframes fadein {from{opacity:0; transform:translateY(4px);} to{opacity:1; transform:translateY(0);}}

div[data-testid="stMetric"] {background:#fff; border:1px solid #EFEAF8; border-radius:14px; padding:.7rem 1rem;
  box-shadow:0 2px 10px rgba(150,140,190,.12); transition:transform .15s ease, box-shadow .15s ease;}
div[data-testid="stMetric"]:hover {transform:translateY(-3px); box-shadow:0 6px 16px rgba(150,140,190,.2);}
.stButton>button, .stDownloadButton>button {border-radius:12px; border:1px solid #D9CFF3; background:#EDE7FA; color:#4A4468;
  transition:transform .12s ease, background .15s ease;}
.stButton>button:hover, .stDownloadButton>button:hover {background:#DCD0F5; border-color:#B5A6E0; color:#4A4468; transform:translateY(-2px);}

/* ---- cartes : hauteur égale, ordonnées en grille stable, effet au survol intentionnel ---- */
.card-row {display:flex; gap:.9rem; align-items:stretch; flex-wrap:wrap; margin:.3rem 0 .6rem;}
.card {background:#fff; border:1px solid #EFEAF8; border-radius:16px; padding:1rem 1.2rem;
  box-shadow:0 2px 12px rgba(150,140,190,.14); flex:1 1 0; min-width:150px; display:flex; flex-direction:column; gap:.35rem;
  transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;}
.card:hover {transform:translateY(-4px); box-shadow:0 10px 22px rgba(150,140,190,.24); border-color:#D9CFF3;}
.card .icon {font-size:1.3rem;}
.card b {color:#4A4468; font-size:.98rem;}
.card span {color:#7C7698; font-size:.88rem; line-height:1.4;}
.card .step-n {display:inline-flex; align-items:center; justify-content:center; width:1.9rem; height:1.9rem;
  border-radius:50%; background:linear-gradient(135deg,#EDE7FA,#F6E9F3); color:#4A4468; font-weight:700;
  font-size:.85rem; margin-bottom:.4rem; box-shadow:0 2px 6px rgba(150,140,190,.25);}
.dot {display:inline-block; width:.55rem; height:.55rem; border-radius:50%; margin-right:.4rem;}

.hero {background:linear-gradient(135deg,#EDE7FA 0%,#E2F0F9 100%); border-radius:18px; padding:1.3rem 1.5rem;
  border:1px solid #E4DBF6;}
.hero b {color:#4A4468;} .hero span {color:#5F5A80; font-size:.95rem; line-height:1.55;}

.podium {border-radius:18px; padding:1.1rem; text-align:center; box-shadow:0 2px 12px rgba(150,140,190,.18);
  transition:transform .18s ease, box-shadow .18s ease;}
.podium:hover {transform:translateY(-4px); box-shadow:0 10px 22px rgba(150,140,190,.26);}
.podium .lab {font-size:.85rem; color:#6B6488; letter-spacing:.05em; text-transform:uppercase;}
.podium .alt {font-size:1.35rem; font-weight:600; color:#4A4468; margin:.2rem 0;}
.podium .sc {color:#6B6488;}

section[data-testid="stSidebar"] .card {background:rgba(255,255,255,.7);}
</style>
<div class="topbar"><span class="brand">FinDecision</span><span class="tag">Aide multicritère à la décision d'investissement</span></div>
""", unsafe_allow_html=True)


# ---------- helpers ----------
def style(fig, h=380):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.7)",
                      font=dict(color=INK), colorway=PALETTE, margin=dict(l=10, r=10, t=40, b=10), legend_title_text="")
    fig.update_xaxes(gridcolor="#EEE9F7")
    fig.update_yaxes(gridcolor="#EEE9F7")
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch")


def show_steps(steps):
    for i, (title, latex, obj) in enumerate(steps, 1):
        st.markdown(f"**Étape {i} : {title}**")
        if latex:
            st.latex(latex)
        st.dataframe(obj.to_frame("Valeur") if isinstance(obj, pd.Series) else obj, width="stretch")


def get_weights(df):
    w = st.session_state.weights
    if w is None or list(w.index) != list(df.columns):
        w = pd.Series(1 / len(df.columns), index=df.columns)
        st.session_state.weights, st.session_state.wmethod = w, "Égale"
    return w


def params_ui(method, key):
    if method == "WASPAS":
        return {"lam": st.slider("λ (part de WSM)", 0.0, 1.0, 0.5, 0.05, key=f"{key}_lam")}
    if method == "VIKOR":
        return {"v": st.slider("v (poids de la stratégie de majorité)", 0.0, 1.0, 0.5, 0.05, key=f"{key}_v")}
    return {}


def reset_data(df, types, mode=None):
    st.session_state.df, st.session_state.types = df, types
    st.session_state.ver += 1
    if mode:
        st.session_state.mode = mode
    st.rerun()


if "df" not in st.session_state:
    st.session_state.update(df=D.DEMO.copy(), types=dict(D.DEMO_TYPES), mode=MODES[0], ver=0,
                            weights=None, wmethod="Égale")

df, types = st.session_state.df, st.session_state.types
errs = D.validate(df, types)
ok = not errs


# ---------- pages ----------
def page_home():
    st.markdown('<div class="hero"><b>Scénario</b><br><span>Un fonds d\'investissement souhaite sélectionner '
                "l'entreprise la plus attractive parmi plusieurs candidates. La décision prend en compte "
                "simultanément la rentabilité, le risque, la croissance, l'endettement, la performance financière, "
                "la liquidité et l'ESG. <b>Objectif MADM</b> : classer les entreprises selon les préférences du "
                "décideur.</span></div>", unsafe_allow_html=True)
    st.write("")
    c = st.columns(3)
    c[0].metric("Alternatives", df.shape[0])
    c[1].metric("Critères", df.shape[1])
    c[2].metric("Source des données", st.session_state.mode)
    st.write("")
    st.markdown("##### Parcours de l'application")
    steps = [("1", "Données", "Matrice de décision, sens MAX/MIN, import CSV."),
             ("2", "Pondération", "Manuelle, AHP, BWM, Entropie, CRITIC."),
             ("3", "Classement", "WSM, WPM, WASPAS, TOPSIS, VIKOR, calculs détaillés."),
             ("4", "Comparaison", "Accord entre méthodes de classement et de pondération."),
             ("5", "Sensibilité", "Variation des poids et simulation de Monte-Carlo.")]
    cards = "".join(f'<div class="card"><span class="step-n">{n}</span><b>{t}</b><span>{d}</span></div>'
                    for n, t, d in steps)
    st.markdown(f'<div class="card-row">{cards}</div>', unsafe_allow_html=True)
    st.caption("Les données du mode Démonstration sont simulées et n'ont aucune valeur d'investissement réelle.")


def page_data():
    st.header("Données")
    mode = st.radio("Source des données", MODES, horizontal=True, index=MODES.index(st.session_state.mode))
    if mode != st.session_state.mode:
        if mode == MODES[0]:
            reset_data(D.DEMO.copy(), dict(D.DEMO_TYPES), mode)
        st.session_state.mode = mode
        st.rerun()
    ver = st.session_state.ver

    if mode == "Import CSV":
        up = st.file_uploader("Fichier CSV (1re colonne : alternatives ; autres colonnes : critères numériques, point décimal)", type=["csv"])
        if up is not None and st.session_state.get("last_up") != (up.name, up.size):
            try:
                raw = pd.read_csv(up, sep=None, engine="python", index_col=0)
                raw.index = raw.index.astype(str)
                raw.index.name = "Alternative"
                raw = raw.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
                st.session_state.last_up = (up.name, up.size)
                reset_data(raw, {c: types.get(c, "max") for c in raw.columns})
            except Exception as e:
                st.error(f"Lecture impossible : {e}")
        st.download_button("Télécharger un modèle CSV", D.DEMO.to_csv().encode("utf-8"), "modele_matrice.csv", "text/csv")

    if mode == MODES[0]:
        disp = df.rename(columns={c: f"{c} {'↑' if types.get(c) == 'max' else '↓'}" for c in df.columns})
        st.dataframe(disp, width="stretch")
        st.caption("↑ critère à maximiser (benefit)   ↓ critère à minimiser (cost). Données simulées de démonstration.")
    else:
        st.markdown("**Matrice de décision** (ajoutez ou supprimez des lignes directement dans le tableau)")
        edited = st.data_editor(df.reset_index(), num_rows="dynamic", width="stretch", key=f"ed_{ver}")
        st.markdown("**Sens des critères**")
        tdf = pd.DataFrame({"Critère": list(df.columns), "Sens": [D.SENS.get(types.get(c, "max")) for c in df.columns]})
        tedit = st.data_editor(
            tdf, hide_index=True, width="stretch", key=f"ty_{ver}",
            column_config={"Critère": st.column_config.TextColumn(disabled=True),
                           "Sens": st.column_config.SelectboxColumn(options=list(D.SENS_INV), required=True)})
        if st.button("Enregistrer les modifications", type="primary"):
            new = edited.dropna(subset=["Alternative"]).copy()
            new["Alternative"] = new["Alternative"].astype(str).str.strip()
            new = new[new["Alternative"] != ""].set_index("Alternative").apply(pd.to_numeric, errors="coerce")
            reset_data(new, {r["Critère"]: D.SENS_INV[r["Sens"]] for _, r in tedit.iterrows()})
        with st.expander("Ajouter ou supprimer un critère (enregistrez d'abord vos modifications)"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nom du nouveau critère")
            if c1.button("Ajouter") and name.strip() and name.strip() not in df.columns:
                d2 = df.copy()
                d2[name.strip()] = 1.0
                reset_data(d2, {**types, name.strip(): "max"})
            rm = c2.multiselect("Critères à supprimer", list(df.columns))
            if c2.button("Supprimer") and rm:
                reset_data(df.drop(columns=rm), {k: v for k, v in types.items() if k not in rm})
        st.download_button("Exporter la matrice (CSV)", df.to_csv().encode("utf-8"), "matrice.csv", "text/csv")

    for e in errs:
        st.error(e)


def page_weights():
    st.header("Pondération des critères")
    crit = list(df.columns)
    method = st.radio("Méthode de pondération", ["Manuelle", "AHP", "BWM", "Entropie", "CRITIC"], horizontal=True)
    res = None
    if method == "Manuelle":
        cols = st.columns(3)
        raw = [cols[i % 3].slider(c, 0, 100, round(100 / len(crit)), key=f"mw_{c}") for i, c in enumerate(crit)]
        if sum(raw) == 0:
            st.error("Au moins un poids doit être non nul.")
            return
        res = {"weights": pd.Series(raw, index=crit) / sum(raw), "steps": [], "info": None}
    elif method == "AHP":
        st.caption("Pour chaque paire : valeur positive = critère de gauche plus important, négative = critère de droite "
                   "plus important, 0 = équivalents (échelle de Saaty).")
        n = len(crit)
        M = np.ones((n, n))
        cols = st.columns(3)
        k = 0
        for i in range(n):
            for j in range(i + 1, n):
                v = cols[k % 3].slider(f"{crit[i]} vs {crit[j]}", -8, 8, 0, key=f"ahp_{crit[i]}_{crit[j]}")
                a = v + 1 if v >= 0 else 1 / (1 - v)
                M[i, j], M[j, i] = a, 1 / a
                k += 1
        res = W.ahp(M, crit)
    elif method == "BWM":
        c1, c2 = st.columns(2)
        best = c1.selectbox("Meilleur critère", crit, index=0)
        worst = c2.selectbox("Pire critère", crit, index=len(crit) - 1)
        if best == worst:
            st.error("Le meilleur et le pire critère doivent être différents.")
            return
        bo, ow = {}, {}
        for c in crit:
            bo[c] = 1 if c == best else c1.number_input(f"{best} comparé à {c}", 1, 9, 2, key=f"bo_{c}")
            ow[c] = 1 if c == worst else c2.number_input(f"{c} comparé à {worst}", 1, 9, 2, key=f"ow_{c}")
        res = W.bwm(crit, best, worst, bo, ow)
        if res is None:
            st.error("Le programme linéaire n'a pas de solution avec ces valeurs.")
            return
    elif method == "Entropie":
        res = W.entropy(df)
    else:
        res = W.critic(df, types)

    w = res["weights"].reindex(crit)
    st.session_state.weights, st.session_state.wmethod = w, method
    left, right = st.columns([3, 2])
    fig = px.bar(pd.DataFrame({"Critère": w.index, "Poids (%)": (w * 100).values}), x="Critère", y="Poids (%)",
                 color="Critère", title=f"Poids obtenus ({method})")
    fig.update_layout(showlegend=False)
    with left:
        show(style(fig))
    with right:
        st.dataframe((w * 100).round(2).rename("Poids (%)").to_frame(), width="stretch")
        if res["info"]:
            st.info(res["info"])
    if res["steps"]:
        with st.expander("Détail des calculs"):
            show_steps(res["steps"])


def page_ranking():
    st.header("Classement des alternatives")
    w = get_weights(df)
    method = st.radio("Méthode de classement", list(R.RANKING), horizontal=True)
    params = params_ui(method, "r")
    res = R.run(method, df, types, w, **params)
    st.caption(f"Poids utilisés : {st.session_state.wmethod}.")

    order = res["ranks"].sort_values(kind="stable").index
    colors = ["#FFE9A8", "#DDE6F5", "#F8D7C4"]
    labels = ["1er", "2e", "3e"]
    for col, alt, colr, lab in zip(st.columns(3), order[:3], colors, labels):
        col.markdown(f'<div class="podium" style="background:{colr}"><div class="lab">{lab}</div>'
                     f'<div class="alt">{alt}</div><div class="sc">{res["label"]} : {res["scores"][alt]:.4f}</div></div>',
                     unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([2, 3])
    table = pd.DataFrame({"Rang": res["ranks"], res["label"]: res["scores"].round(4)}).loc[order]
    left.dataframe(table, width="stretch")
    fig = px.bar(table.reset_index(), x=res["label"], y="Alternative", orientation="h", color="Alternative",
                 title=f"Scores {method}")
    fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed"))
    with right:
        show(style(fig, 340))
    if res["note"]:
        st.info(res["note"])
    with st.expander("Détail des calculs pas à pas"):
        show_steps(res["steps"])


def page_compare():
    st.header("Comparaison des méthodes")
    w = get_weights(df)
    t1, t2 = st.tabs(["Méthodes de classement", "Méthodes de pondération"])
    with t1:
        methods = st.multiselect("Méthodes", list(R.RANKING), default=list(R.RANKING))
        if len(methods) < 2:
            st.info("Sélectionnez au moins deux méthodes.")
        else:
            rk = A.compare_methods(methods, df, types, w)
            rk["Rang moyen"] = rk.mean(axis=1).round(2)
            st.dataframe(rk.sort_values("Rang moyen"), width="stretch")
            pure = rk.drop(columns="Rang moyen")
            c1, c2 = st.columns(2)
            f1 = px.imshow(pure, text_auto=True, aspect="auto", title="Rangs par méthode",
                           color_continuous_scale=["#B5EAD7", "#FFF8F0", "#FFC8DD"])
            f2 = px.imshow(pure.corr(method="spearman").round(2), text_auto=True, zmin=-1, zmax=1, title="Corrélation de Spearman",
                           color_continuous_scale=["#FFC8DD", "#FFFFFF", "#A7C7E7"])
            with c1:
                show(style(f1, 360))
            with c2:
                show(style(f2, 360))
            st.caption("Paramètres par défaut : λ = 0,5 (WASPAS) et v = 0,5 (VIKOR).")
    with t2:
        rm = st.selectbox("Méthode de classement", list(R.RANKING), index=3, key="c_method")
        wsets = {"Égale": W.equal(list(df.columns))["weights"], "Entropie": W.entropy(df)["weights"],
                 "CRITIC": W.critic(df, types)["weights"], f"Actifs ({st.session_state.wmethod})": w}
        wt = pd.DataFrame(wsets) * 100
        st.markdown("**Poids (%)**")
        st.dataframe(wt.round(2), width="stretch")
        rk = pd.DataFrame({k: R.run(rm, df, types, v)["ranks"] for k, v in wsets.items()})
        st.markdown(f"**Rangs obtenus avec {rm}**")
        st.dataframe(rk, width="stretch")


def page_sens():
    st.header("Analyse de sensibilité")
    w = get_weights(df)
    c1, c2 = st.columns(2)
    method = c1.selectbox("Méthode de classement", list(R.RANKING), index=3, key="s_method")
    crit = c2.selectbox("Critère à faire varier", list(df.columns), key="s_crit")
    params = params_ui(method, "s")
    rk = A.weight_sweep(df, types, w, method, crit, **params)
    fig = px.line(rk, markers=True, title=f"Rang des alternatives selon le poids de « {crit} »")
    fig.update_yaxes(autorange="reversed", dtick=1, title="Rang")
    fig.update_xaxes(title=f"Poids de {crit} (les autres poids sont ajustés proportionnellement)")
    fig.add_vline(x=float(w[crit]), line_dash="dot", line_color=INK)
    show(style(fig, 430))
    leader = rk.idxmin(axis=1)
    chg = [(rk.index[i], leader.iloc[i - 1], leader.iloc[i]) for i in range(1, len(rk)) if leader.iloc[i] != leader.iloc[i - 1]]
    if chg:
        st.info("Le leader change : " + " ; ".join(f"vers {b} dès w = {x:.2f} (avant : {a})" for x, a, b in chg) + ".")
    else:
        st.success(f"Le leader ({leader.iloc[0]}) reste le même quel que soit le poids de {crit}.")

    st.subheader("Simulation de Monte-Carlo")
    c1, c2 = st.columns(2)
    noise = c1.slider("Perturbation aléatoire des poids (±%)", 5, 60, 30, 5) / 100
    n = c2.slider("Nombre de simulations", 100, 2000, 500, 100)
    sig = (method, tuple(df.index), tuple(df.columns), tuple(w.round(6)), noise, n, tuple(params.items()))
    if st.button("Lancer la simulation"):
        st.session_state.mc = (sig, A.monte_carlo(df, types, w, method, n=n, noise=noise, **params))
    mc = st.session_state.get("mc")
    if mc and mc[0] == sig:
        left, right = st.columns([2, 3])
        left.dataframe(mc[1].round(2), width="stretch")
        fig = px.bar(mc[1].rename_axis("Alternative").reset_index(), x="Alternative", y="% classé 1er", color="Alternative",
                     title="Fréquence de la 1re place")
        fig.update_layout(showlegend=False)
        with right:
            show(style(fig, 320))


# ---------- layout ----------
tabs = st.tabs(["Accueil", "Données", "Pondération", "Classement", "Comparaison", "Sensibilité"])
with tabs[0]:
    page_home()
with tabs[1]:
    page_data()
for tab, fn in zip(tabs[2:], [page_weights, page_ranking, page_compare, page_sens]):
    with tab:
        if ok:
            fn()
        else:
            st.warning("Corrigez d'abord les données dans l'onglet Données.")

with st.sidebar:
    st.markdown('<div style="font-size:1.5rem;font-weight:800;'
               'background:linear-gradient(90deg,#B5A6E0,#F4A9C0 60%,#F9C784);-webkit-background-clip:text;'
               'background-clip:text;-webkit-text-fill-color:transparent;">FinDecision</div>', unsafe_allow_html=True)
    st.caption("Aide multicritère à la décision d'investissement")
    st.markdown(f'<div class="card"><span>Source&nbsp;: <b>{st.session_state.mode}</b><br>'
               f'{df.shape[0]} alternatives · {df.shape[1]} critères</span></div>', unsafe_allow_html=True)
    if ok:
        w = get_weights(df)
        st.markdown("")
        st.markdown(f"**Poids actifs** — {st.session_state.wmethod}")
        st.dataframe((w * 100).round(1).rename("%").to_frame(), width="stretch")
    else:
        st.warning("Données invalides — voir l'onglet Données.")
    st.divider()
    st.caption("Conçu pour le cours de méthodes MCDM · thème pastel")
