import numpy as np
import pandas as pd
from . import engine as E
RANKING=('WSM','WPM','WASPAS','TOPSIS','VIKOR','PROMETHEE II','ELECTRE I (simplifié)')
FORMULAS={
'WSM':r'Q_i=\sum_j w_j r_{ij}',
'WPM':r'Q_i=\prod_j r_{ij}^{w_j}',
'WASPAS':r'Q_i=\lambda Q_i^{WSM}+(1-\lambda)Q_i^{WPM}',
'TOPSIS':r'C_i=\frac{D_i^-}{D_i^++D_i^-}',
'VIKOR':r'Q_i=v\frac{S_i-S^*}{S^--S^*}+(1-v)\frac{R_i-R^*}{R^--R^*}',
'PROMETHEE II':r'\phi_i=\phi_i^+-\phi_i^-',
'ELECTRE I (simplifié)':r'C(a,b)=\sum_j w_j\mathbf{1}[r_{aj}\geq r_{bj}-q]'}
def run(method,df,types,w,**params):
 real='ELECTRE I' if method=='ELECTRE I (simplifié)' else method
 result=E.rank(df.values,[types[c] for c in df.columns],w.values if isinstance(w,pd.Series) else w,real,**params)
 steps=[]
 for k,v in result['steps'].items():
  a=np.asarray(v)
  if a.ndim==2:
   rows=df.index if a.shape[0]==len(df) else df.columns if a.shape[0]==len(df.columns) else None
   cols=df.columns if a.shape[1]==len(df.columns) else df.index if a.shape[1]==len(df) else None
   obj=pd.DataFrame(a,index=rows,columns=cols)
  elif a.ndim==1:
   obj=pd.Series(a,index=df.index if len(a)==len(df) else df.columns if len(a)==len(df.columns) else None)
  else:obj=pd.DataFrame({'Valeur':[str(v)]})
  steps.append((k,'',obj))
 return {'scores':pd.Series(result['scores'],index=df.index), 'ranks':pd.Series(result['ranks'],index=df.index), 'label':'Q (min)' if method=='VIKOR' else 'Score','note':result['note'],'steps':steps}
