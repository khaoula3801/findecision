# FinDecision

**Application d’aide multicritère à la décision d’investissement** — laboratoire pédagogique Streamlit.

L’interface propose une palette lavande, bleu et menthe, des résultats interactifs et des calculs MCDM vérifiables.

## Démarrage local

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Application disponible localement sur http://localhost:8501 (une fois le serveur lancé).

## Déploiement Streamlit Community Cloud

Créer un dépôt GitHub nommé `findecision` et déposer **directement à sa racine** `app.py`, `requirements.txt`, `mcdm/`, `.streamlit/` et `README.md`. Dans Streamlit Community Cloud, choisir ce dépôt et le fichier principal `app.py`.

## Fonctionnalités

- 7 critères financiers et ESG ; scénario de 5 entreprises simulées, édition et CSV
- Ajout d’entreprise **visible dans l’onglet Données**, et également accessible depuis l’accueil et la barre latérale. La matrice et les classements sont recalculés sans ressaisie des anciennes entreprises.
- Pondération : manuelle, AHP, BWM, Entropie, CRITIC
- Classement : WSM, WPM, WASPAS, TOPSIS, VIKOR, PROMETHEE II, ELECTRE I simplifié
- Analyse : comparaisons Spearman, sensibilité des poids, Monte-Carlo
- Compléments pédagogiques : MAUT, Fuzzy WSM, Fuzzy TOPSIS et AHP complet

**Méthodes non implémentées :** ELECTRE III et approches hybrides ML/XAI. ELECTRE I est une variante simplifiée distincte d’ELECTRE III.

Les données sont **fictives**. Les ajouts persistent pendant la session active ; exporter le CSV pour les conserver après redémarrage.

## Vérification

```powershell
python test_methods.py
```

## Ajouter un critère

Onglet **Données → ＋ Ajouter un critère** (ou boutons de l'accueil et de la barre latérale) : nom, sens MAX/MIN et valeur de chaque entreprise. Les poids repartent en pondération égale ; les redéfinir dans **Pondération**.

## Ajouter une entreprise sans recommencer l'étude

1. Ouvre l'onglet **Données**.
2. Repère **＋ Ajouter une nouvelle alternative** (formulaire visible en haut).
3. Saisis le nom et les valeurs de tous les critères existants.
4. Clique sur **＋ Ajouter et recalculer les classements**.
5. Consulte **Classement** ou l'aperçu de l'accueil ; exporte le CSV pour conserver les données.

Les poids manuels/AHP/BWM sont conservés lorsqu'on ajoute seulement des alternatives. Si les poids actifs ont été calculés par Entropie ou CRITIC, ils sont recalculés sur les nouvelles données.

**Attention aux anciens serveurs :** si une version différente apparaît à `localhost:8501`, arrête ses terminaux (`Ctrl+C`) ou lance cette version sur un port distinct : `python -m streamlit run app.py --server.port 8502`.
