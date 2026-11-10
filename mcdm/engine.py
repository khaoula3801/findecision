"""Moteur MCDM pédagogique. Toutes les sorties renvoient les matrices auditables."""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import rankdata

EPS=1e-12
RI={1:0,2:0,3:.58,4:.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49}

def normalize_weights(w):
    w=np.asarray(w,float)
    if not np.all(np.isfinite(w)) or np.any(w<0) or w.sum()<=0: raise ValueError('Poids non négatifs, finis et de somme strictement positive requis.')
    return w/w.sum()

def matrix(X):
    X=np.asarray(X,float)
    if X.ndim!=2 or min(X.shape)<1 or not np.all(np.isfinite(X)): raise ValueError('Matrice numérique 2D sans valeurs manquantes requise.')
    return X

def benefit_norm(X,senses,kind='ratio'):
    X=matrix(X); out=np.empty_like(X)
    for j,s in enumerate(senses):
        c=X[:,j]; mn,mx=c.min(),c.max()
        if kind=='range':
            out[:,j]=(.5 if mx-mn<EPS else (c-mn)/(mx-mn) if s=='max' else (mx-c)/(mx-mn))
        else:
            if mn<=0: raise ValueError('WSM/WPM/WASPAS par ratios nécessitent des valeurs strictement positives pour chaque critère. Utilisez TOPSIS/VIKOR ou transformez les données.')
            out[:,j]=c/mx if s=='max' else mn/c
    return out

def equal(n): return {'weights':np.ones(n)/n,'steps':{}}

def ahp(A):
    A=matrix(A); n=len(A)
    if A.shape!=(n,n) or np.any(A<=0) or not np.allclose(A*A.T,1,atol=1e-6): raise ValueError('La matrice AHP doit être positive et réciproque.')
    sums=A.sum(axis=0); N=A/sums
    w=N.mean(axis=1)
    lam=float(sums@w)
    ci=max(0.,(lam-n)/(n-1)) if n>1 else 0
    ri=RI.get(n,1.49)
    cr=ci/ri if ri else 0.
    return {'weights':normalize_weights(w),'steps':{'Matrice de comparaison':A,'Sommes colonnes':sums,'Matrice normalisée':N,'Priorités':w,'Lambda max approximatif':lam,'CI':ci,'CR':cr,'Cohérence CR < 0,10':cr<.1}}

def bwm(best,worst,bo,ow):
    bo=np.asarray(bo,float);ow=np.asarray(ow,float);n=len(bo)
    if best==worst or len(ow)!=n or np.any((bo<1)|(bo>9)) or np.any((ow<1)|(ow>9)): raise ValueError('Comparaisons BWM invalides (échelle 1–9).')
    if bo[best]!=1 or ow[worst]!=1 or abs(bo[worst]-ow[best])>EPS: raise ValueError('BWM : BO[Best]=1, OW[Worst]=1 et BO[Worst]=OW[Best] sont obligatoires.')
    Aub=[]; bub=[]
    for j in range(n):
        r=np.zeros(n+1)
        r[best]+=1; r[j]-=bo[j]; r[-1]=-1
        Aub.append(r);Aub.append(np.r_[-r[:-1],-1]);bub.extend([0,0])
        r=np.zeros(n+1)
        r[j]+=1; r[worst]-=ow[j]; r[-1]=-1
        Aub.append(r);Aub.append(np.r_[-r[:-1],-1]);bub.extend([0,0])
    c=np.zeros(n+1);c[-1]=1
    sol=linprog(c,A_ub=Aub,b_ub=bub,A_eq=[np.r_[np.ones(n),0]],b_eq=[1],bounds=[(0,None)]*(n+1),method='highs')
    if not sol.success:raise ValueError('Optimisation BWM impossible : '+sol.message)
    return {'weights':normalize_weights(sol.x[:-1]),'steps':{'BO':bo,'OW':ow,'Poids optimaux':sol.x[:-1],'Écart maximal ξ*':sol.x[-1]}}

def entropy(X,senses):
    X=matrix(X)
    if len(X)<2: raise ValueError('Au moins 2 alternatives nécessaires pour Entropie.')
    N=benefit_norm(X,senses,'range')
    # décalage faible : évite le 0/0 pour colonnes constantes
    P=(N+EPS)/(N+EPS).sum(axis=0)
    E=-np.sum(P*np.log(P),axis=0)/np.log(len(X))
    d=np.maximum(0,1-E)
    w=normalize_weights(d) if d.sum()>EPS else np.ones(X.shape[1])/X.shape[1]
    return {'weights':w,'steps':{'Matrice normalisée orientée':N,'Proportions':P,'Entropies E':E,'Diversification 1-E':d}}

def critic(X,senses):
    X=matrix(X); N=benefit_norm(X,senses,'range'); n=N.shape[1]
    std=N.std(axis=0,ddof=1) if len(X)>1 else np.zeros(n)
    corr=np.eye(n)
    for j in range(n):
        for k in range(j+1,n):
            r=float(np.corrcoef(N[:,j],N[:,k])[0,1]) if std[j]>EPS and std[k]>EPS else 0.
            corr[j,k]=corr[k,j]=r if np.isfinite(r) else 0
    C=std*np.sum(1-np.abs(corr),axis=1)
    w=normalize_weights(C) if C.sum()>EPS else np.ones(n)/n
    return {'weights':w,'steps':{'Matrice min-max orientée':N,'Écarts-types':std,'Corrélations':corr,'Indices C':C}}

def rank(X,senses,w,method,lam=.5,v=.5,q=.05,p=.20,threshold=.65):
    X=matrix(X);w=normalize_weights(w);m,n=X.shape
    if len(senses)!=n or len(w)!=n:raise ValueError('Dimensions de poids ou sens incompatibles.')
    steps={};higher=True;note=''
    if method in ('WSM','WPM','WASPAS'):
        N=benefit_norm(X,senses); S=N@w
        P=np.exp(np.sum(np.where(N>0,np.log(np.maximum(N,EPS)),0)*w,axis=1))
        if method=='WSM': score=S
        elif method=='WPM':score=P
        else:score=lam*S+(1-lam)*P
        steps={'Normalisation bénéfice/coût':N,'Sommes pondérées WSM':S,'Produits pondérés WPM':P}
        if method=='WASPAS':steps['Lambda']=lam
    elif method=='TOPSIS':
        norm=np.linalg.norm(X,axis=0)
        norm=np.where(norm<EPS,1,norm)
        N=X/norm; V=N*w
        ideal=np.array([max(V[:,j]) if senses[j]=='max' else min(V[:,j]) for j in range(n)])
        anti=np.array([min(V[:,j]) if senses[j]=='max' else max(V[:,j]) for j in range(n)])
        dp=np.linalg.norm(V-ideal,axis=1);dm=np.linalg.norm(V-anti,axis=1)
        score=np.divide(dm,dp+dm,out=np.full(m,.5),where=dp+dm>EPS)
        steps={'Normalisation vectorielle':N,'Matrice pondérée':V,'Idéal positif':ideal,'Idéal négatif':anti,'Distance à idéal +':dp,'Distance à idéal -':dm}
    elif method=='VIKOR':
        ideal=np.array([max(X[:,j]) if senses[j]=='max' else min(X[:,j]) for j in range(n)])
        anti=np.array([min(X[:,j]) if senses[j]=='max' else max(X[:,j]) for j in range(n)])
        gap=np.abs(ideal-anti)
        losses=np.divide(ideal-X,ideal-anti,out=np.zeros_like(X),where=gap>EPS)*w
        S=losses.sum(axis=1);R=losses.max(axis=1)
        ss=S.max()-S.min();rr=R.max()-R.min()
        score=v*(S-S.min())/ss if ss>EPS else np.zeros(m)
        score=score+((1-v)*(R-R.min())/rr if rr>EPS else 0)
        higher=False
        order=np.argsort(score,kind='stable')
        advantage=(score[order[1]]-score[order[0]])>=1/(m-1)-1e-10 if m>1 else True
        stable=bool(order[0]==np.argmin(S) or order[0]==np.argmin(R))
        compromise=[int(order[0])]
        if m>1:
            if not advantage:compromise=[int(i) for i in order if score[i]-score[order[0]]<1/(m-1)-1e-10]
            elif not stable:compromise=[int(order[0]),int(order[1])]
        steps={'Meilleures valeurs':ideal,'Pires valeurs':anti,'Regrets pondérés':losses,'Utilité de groupe S':S,'Regret individuel R':R,'Indice Q (minimiser)':score,'Avantage acceptable':advantage,'Stabilité acceptable (S ou R)':stable,'Indices compromis (0-based)':compromise}
        note='VIKOR : minimiser Q ; vérifier les deux conditions de compromis. La stabilité est satisfaite si le gagnant Q est aussi premier en S ou R.'
    elif method in ('PROMETHEE II','ELECTRE I'):
        # Préférences sur critères orientés, min-max (valeurs comparables)
        N=benefit_norm(X,senses,'range');diff=N[:,None,:]-N[None,:,:]
        if method=='PROMETHEE II':
            pref=np.clip((diff-q)/max(p-q,EPS),0,1)
            pref=np.where(diff<=q,0,pref)
            pi=np.sum(pref*w,axis=2)
            np.fill_diagonal(pi,0)
            plus=pi.sum(axis=1)/max(m-1,1);minus=pi.sum(axis=0)/max(m-1,1)
            score=plus-minus
            steps={'Matrice orientée':N,'Préférences agrégées π(a,b)':pi,'Flux sortant Φ+':plus,'Flux entrant Φ-':minus,'Flux net Φ':score,'Indifférence q':q,'Préférence stricte p':p}
            note='PROMETHEE II : fonction de préférence linéaire à seuils q et p, appliquée aux écarts min-max ; convention explicitée dans l’interface.'
        else:
            concord=(diff>=-q).astype(float)@w
            # Veto absent : implémentation ELECTRE I simplifiée (pas ELECTRE III)
            outrank=concord>=threshold
            np.fill_diagonal(outrank,False)
            score=outrank.sum(axis=1)-outrank.sum(axis=0)
            steps={'Matrice orientée':N,'Concordance C(a,b)':concord,'Relation de surclassement':outrank.astype(int),'Solde sortant-entrant':score}
            note='ELECTRE I simplifié : concordance et seuil, sans veto ; le score de flux est un indicateur de synthèse, pas un classement canonique ELECTRE III.'
    else:raise ValueError('Méthode non reconnue.')
    ranks=pd.Series(score).rank(method='min',ascending=not higher).to_numpy(dtype=int)
    return {'scores':score,'ranks':ranks,'higher':higher,'steps':steps,'note':note}

def fuzzy_topsis(T,w,senses):
    T=np.asarray(T,float);w=normalize_weights(w)
    if T.ndim!=3 or T.shape[2]!=3 or np.any(T<=0) or np.any(np.diff(T,axis=2)<0):raise ValueError('Nombres triangulaires strictement positifs avec a ≤ b ≤ c requis.')
    m,n,_=T.shape
    if len(w)!=n or len(senses)!=n:raise ValueError('Dimensions incompatibles.')
    N=np.empty_like(T)
    for j,s in enumerate(senses):
        if s=='max':N[:,j,:]=T[:,j,:]/T[:,j,2].max()
        else:
            mn=T[:,j,0].min();N[:,j,:]=mn/T[:,j,::-1]
    V=N*w[None,:,None]
    dp=np.sqrt(((V-1)**2).mean(axis=2)).sum(axis=1)
    dm=np.sqrt((V**2).mean(axis=2)).sum(axis=1)
    cc=np.divide(dm,dp+dm,out=np.full(m,.5),where=dp+dm>EPS)
    return {'scores':cc,'ranks':pd.Series(cc).rank(method='min',ascending=False).to_numpy(int),'higher':True,'steps':{'Normalisation floue':N,'Matrice floue pondérée':V,'D+':dp,'D-':dm},'note':'Fuzzy TOPSIS triangulaire (Chen), idéal (1,1,1), anti-idéal (0,0,0).'}

def fuzzy_wsm(T,w,senses):
    T=np.asarray(T,float);w=normalize_weights(w)
    if T.ndim!=3 or T.shape[-1]!=3 or np.any(T<=0) or np.any(np.diff(T,axis=2)<0):raise ValueError('Triplets triangulaires positifs et ordonnés requis.')
    N=np.empty_like(T)
    for j,s in enumerate(senses):
        if s=='max':N[:,j,:]=T[:,j,:]/T[:,j,2].max()
        else:N[:,j,:]=T[:,j,0].min()/T[:,j,::-1]
    total=(N*w[None,:,None]).sum(axis=1);score=total.mean(axis=1)
    return {'scores':score,'ranks':pd.Series(score).rank(ascending=False,method='min').to_numpy(int),'higher':True,'steps':{'Normalisation floue':N,'Somme triangulaire (a,b,c)':total,'Largeur incertitude c-a':total[:,2]-total[:,0],'Défuzzification':score},'note':'Somme pondérée floue et défuzzification par (a+b+c)/3.'}

def single_maut(values,lows,highs,senses,w,threshold):
    values=np.asarray(values,float);lo=np.asarray(lows,float);hi=np.asarray(highs,float);w=normalize_weights(w)
    if np.any(hi<=lo):raise ValueError('Les bornes maximales doivent dépasser les bornes minimales.')
    if np.any(values<lo) or np.any(values>hi):raise ValueError('Les valeurs doivent appartenir aux plages de référence.')
    U=np.array([(x-a)/(b-a) if s=='max' else (b-x)/(b-a) for x,a,b,s in zip(values,lo,hi,senses)])
    score=float(U@w)
    return score,U,score>=threshold
