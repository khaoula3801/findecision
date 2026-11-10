import numpy as np
import pandas as pd

SENS = {'max':'MAX ↑','min':'MIN ↓'}
SENS_INV = {v:k for k,v in SENS.items()}

# Cas financier simulé (aucune recommandation d'investissement réel)
DEMO = pd.DataFrame({
    'ROI (%)': [16,13,12,19,15],
    'Risque (%)': [22,14,18,29,16],
    'Croissance CA (%)': [21,13,9,26,17],
    'Dette / Fonds propres': [0.65,0.35,0.48,0.78,0.42],
    'ROE (%)': [18,15,12,21,17],
    'Liquidité': [1.6,2.1,1.8,1.2,2.4],
    'ESG (/10)': [7.3,8.1,6.8,6.5,9.0],
}, index=['Atlas Tech','Maghreb Energies','Rabat Industrie','Noria Services','Solaris Maroc'])
DEMO.index.name='Alternative'
DEMO_TYPES={
    'ROI (%)':'max', 'Risque (%)':'min', 'Croissance CA (%)':'max',
    'Dette / Fonds propres':'min','ROE (%)':'max','Liquidité':'max','ESG (/10)':'max'
}

def validate(df,types):
    errors=[]
    if df.shape[0]<2: errors.append('Au moins deux alternatives sont nécessaires pour les classements relatifs.')
    if df.shape[1]<1: errors.append('Au moins un critère est nécessaire.')
    if df.index.has_duplicates: errors.append('Les noms des alternatives doivent être uniques.')
    if df.columns.has_duplicates: errors.append('Les noms des critères doivent être uniques.')
    try:
        X=df.to_numpy(dtype=float)
        if not np.isfinite(X).all(): errors.append('La matrice doit contenir uniquement des valeurs numériques finies.')
    except (TypeError,ValueError): errors.append('La matrice doit être numérique.')
    if any(types.get(c) not in ('max','min') for c in df.columns):
        errors.append('Tous les sens doivent être MAX ou MIN.')
    return errors
