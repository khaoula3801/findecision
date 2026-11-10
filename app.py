import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from mcdm import analysis as A, data as D, ranking as R, weighting as W
import theme

PALETTE = theme.NEON
INK = "#161A38"
px.defaults.color_discrete_sequence = PALETTE
MODES = ["Démonstration", "Personnalisé", "Import CSV"]

st.set_page_config(page_title="FinDecision", page_icon="◆", layout="wide", initial_sidebar_state="expanded")
theme.inject()


# ---------- helpers ----------
def style(fig, h=380):
    fig.update_layout(height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FFFFFF",
                      font=dict(color="#2A2F55", size=13, family="Space Grotesk, sans-serif"), colorway=PALETTE,
                      margin=dict(l=12, r=24, t=48, b=12), legend_title_text="",
                      hoverlabel=dict(bgcolor="#FFFFFF", font_color="#161A38", bordercolor="#6D28D9"),
                      title_font=dict(size=17, color="#161A38"))
    fig.update_xaxes(gridcolor="#ECEEF8", zerolinecolor="#D5D9EC", linecolor="#D5D9EC")
    fig.update_yaxes(gridcolor="#ECEEF8", zerolinecolor="#D5D9EC", linecolor="#D5D9EC")
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
    if method == "PROMETHEE II":
        q = st.slider("Seuil d’indifférence q (normalisé)", 0.0, 0.5, 0.05, 0.01, key=f"{key}_q")
        p = st.slider("Seuil de préférence p (normalisé)", q + 0.01, 1.0, max(0.2, q + 0.01), 0.01, key=f"{key}_p")
        return {"q":q, "p":p}
    if method == "ELECTRE I (simplifié)":
        return {"threshold":st.slider("Seuil de concordance", 0.5, 1.0, 0.65, 0.05, key=f"{key}_conc")}
    return {}


def reset_data(df, types, mode=None, preserve_weights=False):
    old_w = st.session_state.get("weights")
    old_method = st.session_state.get("wmethod", "Égale")
    st.session_state.df, st.session_state.types = df, types
    if preserve_weights and isinstance(old_w, pd.Series) and list(old_w.index) == list(df.columns):
        if old_method == "Entropie":
            st.session_state.weights = W.entropy(df, types)["weights"]
        elif old_method == "CRITIC":
            st.session_state.weights = W.critic(df, types)["weights"]
        else:
            st.session_state.weights = old_w
        st.session_state.wmethod = old_method
    else:
        st.session_state.weights = None
        st.session_state.wmethod = "Égale"
    st.session_state.pop("mc", None)
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




def insert_alternative(name, values):
    """Ajoute une ligne à la matrice courante et actualise les analyses."""
    label = str(name).strip()
    if not label:
        return "Indique le nom de la nouvelle entreprise."
    if label.casefold() in {str(x).casefold() for x in df.index}:
        return "Cette entreprise existe déjà. Choisis un autre nom."
    updated = df.copy()
    updated.loc[label] = pd.Series(values, index=df.columns, dtype=float)
    problems = D.validate(updated, types)
    if problems:
        return " ; ".join(problems)
    st.session_state.last_added = label
    reset_data(updated, dict(types), mode="Personnalisé", preserve_weights=True)
    return None


@st.dialog("Nouvelle alternative · Entreprise", width="large")
def new_alternative_dialog():
    st.caption("Renseigne les performances de l'entreprise selon les critères actuels. Aucune ressaisie des autres entreprises n'est nécessaire.")
    with st.form("modal_new_alternative", clear_on_submit=False):
        name = st.text_input("Nom de l’entreprise", placeholder="Ex. Entreprise F", key="modal_add_name")
        values = {}
        cols = st.columns(2, gap="large")
        for j, criterion in enumerate(df.columns):
            with cols[j % 2]:
                values[criterion] = st.number_input(
                    f"{criterion} {'↑' if types.get(criterion)=='max' else '↓'}",
                    value=0.0, step=0.1, format="%.3f", key=f"modal_newcriterion_{j}")
        submitted = st.form_submit_button("Ajouter l’entreprise et recalculer", type="primary", use_container_width=True)
    if submitted:
        err = insert_alternative(name, values)
        if err:
            st.error(err)


def add_alternative_ui(prefix="data", expanded=False):
    if st.button("＋ Ajouter une entreprise", type="primary", key=f"open_add_{prefix}", use_container_width=True):
        new_alternative_dialog()


def inline_alternative_form():
    """Formulaire visible dans l'onglet Données, indépendant de la sidebar."""
    st.markdown("#### ＋ Ajouter une nouvelle alternative")
    st.caption("Une alternative = une entreprise (une nouvelle ligne). Renseigne ses performances, puis clique sur Ajouter. Tous les classements seront mis à jour.")
    with st.form("inline_add_alternative", clear_on_submit=False):
        name = st.text_input("Nom de la nouvelle entreprise", placeholder="Ex. Entreprise F", key="inline_add_name")
        values = {}
        cols = st.columns(2, gap="large")
        for j, criterion in enumerate(df.columns):
            with cols[j % 2]:
                values[criterion] = st.number_input(
                    f"{criterion} {'↑' if types.get(criterion)=='max' else '↓'}",
                    value=0.0, step=0.1, format="%.3f", key=f"inline_newcriterion_{j}")
        submitted = st.form_submit_button("＋ Ajouter et recalculer les classements", type="primary", use_container_width=True)
    if submitted:
        err = insert_alternative(name, values)
        if err:
            st.error(err)



def insert_criterion(name, sens, values):
    """Ajoute une colonne (critère) avec une valeur par entreprise et recalcule tout."""
    label = str(name).strip()
    if not label:
        return "Indique le nom du nouveau critère."
    if label.casefold() in {str(c).casefold() for c in df.columns}:
        return "Ce critère existe déjà. Choisis un autre nom."
    updated = df.copy()
    updated[label] = pd.Series(values, index=df.index, dtype=float)
    new_types = {**types, label: sens}
    problems = D.validate(updated, new_types)
    if problems:
        return " ; ".join(problems)
    st.session_state.last_added_crit = label
    reset_data(updated, new_types, mode="Personnalisé", preserve_weights=False)
    return None


def _criterion_fields(prefix):
    ver = st.session_state.ver
    name = st.text_input("Nom du nouveau critère", placeholder="Ex. Marge nette (%)", key=f"{prefix}_crit_name_{ver}")
    sens_label = st.radio("Sens du critère", ["MAX ↑  (plus c’est grand, mieux c’est)", "MIN ↓  (plus c’est petit, mieux c’est)"],
                          horizontal=True, key=f"{prefix}_crit_sens_{ver}")
    sens = "max" if sens_label.startswith("MAX") else "min"
    st.markdown("**Valeur de chaque entreprise pour ce critère**")
    values = {}
    cols = st.columns(2, gap="large")
    for j, alt in enumerate(df.index):
        with cols[j % 2]:
            values[alt] = st.number_input(str(alt), value=0.0, step=0.1, format="%.3f", key=f"{prefix}_crit_val_{ver}_{j}")
    return name, sens, values


@st.dialog("Nouveau critère", width="large")
def new_criterion_dialog():
    st.caption("Ajoute un critère (une colonne) et renseigne la valeur de chaque entreprise existante. Les classements sont recalculés ; les poids repartent en pondération égale, à redéfinir dans l’onglet Pondération.")
    with st.form("modal_new_criterion", clear_on_submit=False):
        name, sens, values = _criterion_fields("modal")
        submitted = st.form_submit_button("Ajouter le critère et recalculer", type="primary", use_container_width=True)
    if submitted:
        err = insert_criterion(name, sens, values)
        if err:
            st.error(err)


def add_criterion_ui(prefix="data"):
    if st.button("＋ Ajouter un critère", key=f"open_crit_{prefix}", use_container_width=True):
        new_criterion_dialog()


def inline_criterion_form():
    """Formulaire visible dans l'onglet Données pour ajouter un critère."""
    st.markdown("#### ＋ Ajouter un nouveau critère")
    st.caption("Un critère = une nouvelle colonne (ex. marge nette, beta, dividende). Choisis son sens MAX/MIN et saisis la valeur de chaque entreprise. Les poids repartent en pondération égale : redéfinis-les ensuite dans l’onglet Pondération.")
    with st.form("inline_add_criterion", clear_on_submit=False):
        name, sens, values = _criterion_fields("inline")
        submitted = st.form_submit_button("＋ Ajouter le critère et recalculer", type="primary", use_container_width=True)
    if submitted:
        err = insert_criterion(name, sens, values)
        if err:
            st.error(err)


# ---------- pages ----------
def page_home():

    st.write("")
    w = get_weights(df)
    k1,k2,k3,k4 = st.columns(4, gap="medium")
    k1.metric("Entreprises", len(df))
    k2.metric("Critères", len(df.columns))
    k3.metric("Méthodes de classement", len(R.RANKING))
    k4.metric("Pondération", st.session_state.wmethod)
    st.markdown('<div class="slabel">Exploration interactive · ajouter une alternative depuis le bouton ci-dessous</div>', unsafe_allow_html=True)
    filtercol, actioncol = st.columns([3.2,1], gap="large",vertical_alignment="bottom")
    with filtercol:
        quick_method = st.selectbox("Méthode du classement instantané", list(R.RANKING), index=list(R.RANKING).index("TOPSIS"), key="quick_method", help="Change la méthode pour comparer instantanément les classements, sans modifier la pondération active.")
    with actioncol:
        add_alternative_ui("home")
        add_criterion_ui("home")
    if ok:
        try:
            result = R.run(quick_method, df, types, w)
            order = result["ranks"].sort_values(kind="stable").index
            leader = str(order[0])
            score = float(result["scores"].loc[leader])
            c1,c2 = st.columns([.86,1.14],gap="large")
            with c1:
                st.markdown(f'<div class="winner-card"><span class="eyebrow">Alternative n°1 · {quick_method}</span><span class="name">{leader}</span><span class="score">Score : {score:.4f} · Pondération {st.session_state.wmethod}</span></div>',unsafe_allow_html=True)
                st.markdown('<div class="slabel">Classement actuel</div>',unsafe_allow_html=True)
                ordered_table = pd.DataFrame({"Rang": result["ranks"],"Score": result["scores"]}).loc[order]
                st.dataframe(ordered_table.style.format({"Score":"{:.4f}"}),width="stretch",height=248)
            with c2:
                vals = pd.DataFrame({"Entreprise":result["scores"].index,"Score":result["scores"].values}).set_index("Entreprise").loc[order].rename_axis("Entreprise").reset_index()
                fig = px.bar(vals.iloc[::-1], x="Score",y="Entreprise",orientation="h",color="Entreprise",text="Score",
                             color_discrete_sequence=PALETTE,title=f"Scores · {quick_method}")
                fig.update_traces(texttemplate="%{text:.3f}",textposition="outside",marker_line_width=0,hovertemplate="%{y}<br>Score : %{x:.4f}<extra></extra>")
                fig.update_layout(showlegend=False,xaxis_title="Score",yaxis_title="",uniformtext_minsize=9,uniformtext_mode="hide")
                fig.update_xaxes(range=[0,float(vals["Score"].max())*1.22])
                fig.update_yaxes(categoryorder="array", categoryarray=list(vals["Entreprise"])[::-1])
                show(style(fig,355))
            if result.get("note"):
                st.caption(result["note"])
            st.caption("Ce classement est relatif à la matrice et aux poids actifs. Pour justifier le résultat, consulte l’onglet Classement et ses calculs intermédiaires.")
        except ValueError as exc:
            st.warning(f"Classement indisponible pour cette méthode : {exc}")
    st.markdown('<div class="slabel">Données et parcours de décision</div>',unsafe_allow_html=True)
    with st.expander("Voir la matrice financière et les sens MAX / MIN"):
        names={c:f"{c} {'↑' if types.get(c)=='max' else '↓'}" for c in df.columns}
        st.dataframe(df.rename(columns=names).rename_axis("Entreprise"),width="stretch")
        st.caption("Données simulées pour l’apprentissage ; aucune recommandation financière réelle.")
    steps=[("01","Structurer","Matrice de décision, sens et alternatives"),("02","Pondérer","Expertise AHP/BWM ou données CRITIC/Entropie"),("03","Classer","Méthodes additives, compromis et surclassement"),("04","Valider","Spearman, scénarios et sensibilité")]
    cols=st.columns(4,gap="medium")
    for col,(n,label,sub) in zip(cols,steps):
        col.markdown(f'<div class="featurecard"><span class="num">{n}</span><b>{label}</b><small>{sub}</small></div>',unsafe_allow_html=True)


def page_data():
    st.header("Matrice de décision")
    st.markdown('<p class="section-intro">Gère les entreprises, leurs performances et les critères. Toute modification validée actualise les scores et les classements.</p>',unsafe_allow_html=True)
    if st.session_state.get("last_added_crit"):
        st.success(f"Critère « {st.session_state.pop('last_added_crit')} » ajouté : renseigne son poids dans l’onglet Pondération ; les classements sont à jour.")
    if st.session_state.get("last_added"):
        st.success(f"{st.session_state.pop('last_added')} ajoutée : la matrice et les classements ont été mis à jour.")
    # L'ajout est visible sans passer par la barre latérale ni importer un CSV.
    with st.container(border=True):
        t_alt, t_crit = st.tabs(["＋ Ajouter une entreprise", "＋ Ajouter un critère"])
        with t_alt:
            inline_alternative_form()
        with t_crit:
            inline_criterion_form()
    st.download_button("↓ Exporter la matrice mise à jour en CSV",df.to_csv().encode("utf-8-sig"),"findecision_matrice.csv","text/csv",use_container_width=False)
    st.markdown('<div class="kicker">Source et édition des données</div>',unsafe_allow_html=True)
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
        st.caption("Mode Démonstration : données en lecture seule. Choisis Personnalisé pour modifier les valeurs.")
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
            reset_data(new, {r["Critère"]: D.SENS_INV[r["Sens"]] for _, r in tedit.iterrows()}, preserve_weights=True)
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
    st.markdown('<p class="section-intro">Détermine l’importance de chaque critère. Compare les méthodes subjectives (jugement expert) et objectives (données).</p>',unsafe_allow_html=True)
    crit = list(df.columns)
    method = st.radio("Méthode de pondération", ["Manuelle", "AHP", "BWM", "Entropie", "CRITIC"], horizontal=True, index=(["Manuelle", "AHP", "BWM", "Entropie", "CRITIC"].index(st.session_state.wmethod) if st.session_state.wmethod in ["Manuelle", "AHP", "BWM", "Entropie", "CRITIC"] else 0))
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
            bo[c] = 1 if c == best else c1.number_input(f"{best} comparé à {c}", 1, 9, 9 if c == worst else 3, key=f"bo_{c}")
            ow[c] = 1 if c == worst else c2.number_input(f"{c} comparé à {worst}", 1, 9, 9 if c == best else 3, key=f"ow_{c}")
        if bo[worst] != ow[best]:
            st.warning("BWM : la comparaison Best/Worst doit être identique dans les deux vecteurs.")
            return
        res = W.bwm(crit, best, worst, bo, ow)
        if res is None:
            st.error("Le programme linéaire n'a pas de solution avec ces valeurs.")
            return
    elif method == "Entropie":
        res = W.entropy(df, types)
    else:
        res = W.critic(df, types)

    w = res["weights"].reindex(crit)
    if st.button("Appliquer cette pondération",type="primary",key="apply_weights"):
        st.session_state.weights, st.session_state.wmethod = w, method
        st.toast(f"Pondération {method} appliquée",icon="✅")
    else:
        st.caption(f"Pondération active : {st.session_state.wmethod}. Clique sur « Appliquer cette pondération » pour valider les poids affichés.")
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
    st.markdown('<p class="section-intro">Compare les entreprises grâce aux scores, aux rangs et aux calculs intermédiaires de chaque méthode.</p>',unsafe_allow_html=True)
    with st.expander("Ajouter une entreprise directement au classement"):
        add_alternative_ui("ranking")
    w = get_weights(df)
    method = st.radio("Méthode de classement", list(R.RANKING), horizontal=True)
    params = params_ui(method, "r")
    try:
        res = R.run(method, df, types, w, **params)
    except ValueError as exc:
        st.error(str(exc))
        return
    with st.expander("Comprendre la méthode et sa formule", expanded=False):
        st.latex(R.FORMULAS[method])
        explanations = {
          "WSM":"Somme des performances normalisées pondérées ; le plus grand score gagne.",
          "WPM":"Produit de performances pondérées ; pénalise les critères très faibles.",
          "WASPAS":"Combine les deux scores précédents avec le coefficient λ.",
          "TOPSIS":"Recherche l’alternative proche de l’idéal positif et éloignée de l’idéal négatif.",
          "VIKOR":"Recherche un compromis entre utilité collective S et regret maximal R ; Q est à minimiser.",
          "PROMETHEE II":"Compare les alternatives deux à deux par des fonctions de préférence, puis calcule des flux nets.",
          "ELECTRE I (simplifié)":"Vérifie la concordance entre paires (version simplifiée, sans veto ; ce n'est pas ELECTRE III)."}
        st.write(explanations[method])
    st.caption(f"Poids utilisés : {st.session_state.wmethod}.")

    order = res["ranks"].sort_values(kind="stable").index
    classes = ["p1", "p2", "p3"]
    labels = ["◆ 1er", "2e", "3e"]
    for col, alt, colr, lab in zip(st.columns(3), order[:3], classes, labels):
        col.markdown(f'<div class="podium {colr}"><div class="lab">{lab}</div>'
                     f'<div class="alt">{alt}</div><div class="sc">{res["label"]} : {res["scores"][alt]:.4f}</div></div>',
                     unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([2, 3])
    table = pd.DataFrame({"Rang": res["ranks"], res["label"]: res["scores"].round(4)}).loc[order]
    left.dataframe(table, width="stretch")
    fig = px.bar(table.reset_index(), x=res["label"], y="Alternative", orientation="h", color="Alternative",
                 title=f"Scores {method}")
    fig.update_layout(showlegend=False)
    fig.update_yaxes(categoryorder="array", categoryarray=list(table.index)[::-1])
    fig.update_xaxes(range=[0, float(table[res["label"]].max()) * 1.12])
    with right:
        show(style(fig, 340))
    if res["note"]:
        st.info(res["note"])
    with st.expander("Détail des calculs pas à pas"):
        show_steps(res["steps"])


def page_compare():
    st.header("Comparer les méthodes")
    st.markdown('<p class="section-intro">Observe les écarts entre classements et mesure leur accord avec Spearman.</p>',unsafe_allow_html=True)
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
                           color_continuous_scale=["#10B981", "#FFFFFF", "#E11DBA"])
            f2 = px.imshow(pure.corr(method="spearman").round(2), text_auto=True, zmin=-1, zmax=1, title="Corrélation de Spearman",
                           color_continuous_scale=["#E11DBA", "#FFFFFF", "#06B6D4"])
            with c1:
                show(style(f1, 360))
            with c2:
                show(style(f2, 360))
            st.caption("Paramètres par défaut : λ = 0,5 (WASPAS) et v = 0,5 (VIKOR).")
    with t2:
        rm = st.selectbox("Méthode de classement", list(R.RANKING), index=3, key="c_method")
        wsets = {"Égale": W.equal(list(df.columns))["weights"], "Entropie": W.entropy(df, types)["weights"],
                 "CRITIC": W.critic(df, types)["weights"], f"Actifs ({st.session_state.wmethod})": w}
        wt = pd.DataFrame(wsets) * 100
        st.markdown("**Poids (%)**")
        st.dataframe(wt.round(2), width="stretch")
        rk = pd.DataFrame({k: R.run(rm, df, types, v)["ranks"] for k, v in wsets.items()})
        st.markdown(f"**Rangs obtenus avec {rm}**")
        st.dataframe(rk, width="stretch")


def page_sens():
    st.header("Robustesse de la décision")
    st.markdown('<p class="section-intro">Fais varier les poids et vérifie si l’entreprise classée première reste la même.</p>',unsafe_allow_html=True)
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


def page_advanced():
    from mcdm import engine as E
    st.header("Explorer les méthodes avancées")
    st.caption("Compléments du cours : évaluation isolée, logique floue et AHP hiérarchique.")
    w = get_weights(df)
    tabs_adv = st.tabs(["MAUT · alternative isolée", "Logique floue / Fuzzy", "AHP complet", "Guide des méthodes"])
    with tabs_adv[0]:
        st.subheader("Évaluer une entreprise par rapport à des seuils absolus")
        st.latex(r"S(A)=\sum_j w_j u_j(x_j)")
        alt=st.selectbox("Entreprise à évaluer", list(df.index),key="maut_alt")
        st.caption("Les bornes de référence sont définies ici par l'utilisateur ; par défaut, les min/max du scénario servent d'exemple pédagogique.")
        lows=[];highs=[];vals=[]
        for c in df.columns:
            mn=float(df[c].min());mx=float(df[c].max());v=float(df.loc[alt,c])
            if mn==mx:mn-=1;mx+=1
            c1,c2,c3=st.columns(3)
            c1.number_input(f"{c} · valeur",value=v,disabled=True,key=f"mval_{c}")
            lo=c2.number_input(f"{c} · référence basse",value=mn,key=f"mlow_{c}")
            hi=c3.number_input(f"{c} · référence haute",value=mx,key=f"mhigh_{c}")
            vals.append(v);lows.append(lo);highs.append(hi)
        tau=st.slider("Seuil d'acceptation τ",0.0,1.0,0.7,0.05)
        try:
            score,utility,accepted=E.single_maut(vals,lows,highs,[types[c] for c in df.columns],w.values,tau)
            st.metric("Score MAUT",f"{score:.3f}")
            if accepted:
                st.success("Alternative acceptée selon ce seuil")
            else:
                st.warning("Alternative rejetée selon ce seuil")
            st.dataframe(pd.DataFrame({"Critère":df.columns,"Utilité":utility,"Poids":w.values,"Contribution":utility*w.values}),hide_index=True,width="stretch")
        except ValueError as e:st.error(str(e))
    with tabs_adv[1]:
        st.subheader("Évaluations floues triangulaires")
        st.latex(r"\tilde{x}=(l,m,u),\qquad l\leq m\leq u")
        st.write("Pour illustrer un avis imprécis, on construit autour de chaque valeur une plage triangulaire réglable. Les évaluations sont *synthétiques*, et non des avis d'experts collectés.")
        spread=st.slider("Incertitude autour des données (%)",1,30,10,1)/100
        method=st.radio("Méthode floue",["Fuzzy WSM","Fuzzy TOPSIS"],horizontal=True)
        X=df.to_numpy(float)
        if (X<=0).any():
            st.warning("La démonstration triangulaire exige des valeurs strictement positives.")
        else:
            T=np.stack([X*(1-spread),X,X*(1+spread)],axis=2)
            try:
                res=E.fuzzy_wsm(T,w.values,[types[c] for c in df.columns]) if method=="Fuzzy WSM" else E.fuzzy_topsis(T,w.values,[types[c] for c in df.columns])
                out=pd.DataFrame({"Alternative":df.index,"Rang":res["ranks"],"Score défuzzifié":res["scores"]}).sort_values("Rang")
                st.dataframe(out,width="stretch",hide_index=True)
                with st.expander("Calculs flous intermédiaires"):
                    for k,v in res["steps"].items():
                        a=np.asarray(v)
                        if a.ndim==3:
                            st.markdown(f"**{k}**")
                            st.dataframe(pd.DataFrame(a.reshape(len(df),-1),index=df.index),width="stretch")
                        elif a.ndim==2:st.write(k);st.dataframe(pd.DataFrame(a,index=df.index),width="stretch")
                        else:st.write(k,pd.Series(a,index=df.index))
                st.caption(res["note"])
            except ValueError as e:st.error(str(e))
    with tabs_adv[2]:
        st.subheader("AHP hiérarchique : comparaisons locales des alternatives")
        st.write("Les poids des critères sont ceux déjà déterminés dans l’onglet Pondération. Pour chaque critère, comparez les alternatives par paires, puis agrégez les priorités locales.")
        names=list(df.index)
        if len(names)>7:
            st.info("Pour limiter le nombre de comparaisons, utilisez au plus 7 alternatives pour cet exercice AHP.")
        else:
            local=[];crs=[]
            for c in df.columns:
                with st.expander(f"Comparaisons des alternatives : {c}"):
                    m=len(names);P=np.ones((m,m))
                    for i in range(m):
                        for j in range(i+1,m):
                            option=st.select_slider(f"{names[i]} / {names[j]}",options=[1/9,1/7,1/5,1/3,1,3,5,7,9],value=1,key=f"loc_{c}_{i}_{j}")
                            P[i,j]=float(option);P[j,i]=1/float(option)
                    r=E.ahp(P);local.append(r["weights"]);crs.append(r["steps"]["CR"])
                    st.caption(f"CR = {crs[-1]:.4f} — " + ("cohérent" if crs[-1]<.1 else "jugements incohérents"))
            if local:
                loc=np.array(local).T
                overall=loc@w.values
                st.dataframe(pd.DataFrame(loc,index=names,columns=df.columns),width="stretch")
                st.dataframe(pd.DataFrame({"Alternative":names,"Priorité globale":overall}).sort_values("Priorité globale",ascending=False),width="stretch",hide_index=True)
                if any(cr>=.1 for cr in crs):st.warning("Au moins une matrice locale est incohérente : interprétation prudente.")
    with tabs_adv[3]:
        guide=[("AHP / BWM","Pondération subjective", "AHP : paires et CR ; BWM : Best/Worst et optimisation."),
               ("Entropie / CRITIC","Pondération objective","Entropie : dispersion de l'information ; CRITIC : dispersion et corrélations."),
               ("WSM / WPM / WASPAS","Classement compensatoire","Somme / produit / combinaison pondérée."),
               ("TOPSIS / VIKOR","Classement par compromis","TOPSIS : distance à l’idéal ; VIKOR : utilité collective et regret."),
               ("PROMETHEE II / ELECTRE I","Surclassement","PROMETHEE : flux nets ; ELECTRE I simplifié : concordance sans veto."),
               ("Spearman / Monte-Carlo","Robustesse","Comparer les rangs et tester les variations de poids."),
               ("MAUT / Fuzzy","Extensions","Évaluation absolue et appréciations imprécises.")]
        st.dataframe(pd.DataFrame(guide,columns=["Méthodes","Rôle","À expliquer au professeur"]),width="stretch",hide_index=True)
        st.warning("Limites : ELECTRE III, Fuzzy intuitionniste et MCDM hybride IA ne sont pas intégrés. Le cours les aborde mais l’application ne doit pas prétendre les implémenter.")


# ---------- layout ----------
_leader, _wm = None, st.session_state.wmethod
if ok:
    try:
        _w = get_weights(df)
        _r = R.run("TOPSIS", df, types, _w)
        _leader = str(_r["ranks"].sort_values(kind="stable").index[0])
        _wm = st.session_state.wmethod
    except Exception:
        _leader = None
theme.hero(_leader, "TOPSIS", len(df), len(df.columns), len(R.RANKING), _wm,
           ["AHP", "BWM", "ENTROPIE", "CRITIC", "WSM", "WPM", "WASPAS", "TOPSIS", "VIKOR", "PROMETHEE II", "ELECTRE I", "SPEARMAN", "MONTE-CARLO", "MAUT", "FUZZY"])
tabs = st.tabs(["Vue d’ensemble", "Données", "Pondération", "Classement", "Comparaison", "Robustesse", "Méthodes avancées"])
with tabs[0]:
    page_home()
with tabs[1]:
    page_data()
for tab, fn in zip(tabs[2:], [page_weights, page_ranking, page_compare, page_sens, page_advanced]):
    with tab:
        if ok:
            fn()
        else:
            st.warning("Corrigez d'abord les données dans l'onglet Données.")

with st.sidebar:
    st.markdown('<div class="sidebar-brand">◆ FinDecision</div><div class="sidebar-sub">Aide multicritère à la décision d’investissement</div>',unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Espace de travail</div>',unsafe_allow_html=True)
    st.markdown(f'<span class="sidebar-pill">{len(df)} entreprises</span><span class="sidebar-pill">{len(df.columns)} critères</span>',unsafe_allow_html=True)
    st.write("")
    add_alternative_ui("sidebar")
    add_criterion_ui("sidebar")
    st.markdown('<div class="sidebar-section">Pondération en cours</div>',unsafe_allow_html=True)
    if ok:
        w=get_weights(df)
        st.markdown(f'**{st.session_state.wmethod}**')
        fig=px.bar(pd.DataFrame({"Critère":w.index,"Poids":w.values*100}),x="Poids",y="Critère",orientation="h")
        fig.update_traces(marker_color="#6D28D9")
        fig.update_layout(height=250,margin=dict(l=0,r=8,t=5,b=0),showlegend=False,plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#2A2F55",size=11),xaxis_title="Poids (%)",yaxis_title="")
        st.plotly_chart(fig,width="stretch",config={"displayModeBar":False})
        with st.expander("Afficher les poids numériques"):
            st.dataframe((w*100).round(2).rename("Poids (%)").to_frame(),width="stretch")
    else:
        st.warning("Matrice invalide. Vérifier les données.")
    st.divider()
    st.caption("Données simulées · Usage pédagogique · Aucun conseil d’investissement.")
