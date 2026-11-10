import numpy as np
import pandas as pd
from . import ranking as R

def compare_methods(methods,df,types,w):return pd.DataFrame({m:R.run(m,df,types,w)['ranks'] for m in methods})
def adjust(w,crit,x):
 base=w.copy().astype(float);rem=base.sum()-base[crit]
 if rem<=1e-12:
  base[:]= (1-x)/(len(base)-1) if len(base)>1 else 1
 else:
  for c in base.index:
   if c!=crit:base[c]=base[c]*(1-x)/rem
 base[crit]=x
 return base/base.sum()
def weight_sweep(df,types,w,method,crit,**params):
 return pd.DataFrame({round(float(x),2):R.run(method,df,types,adjust(w,crit,float(x)),**params)['ranks'] for x in np.linspace(0,1,21)}).T

def monte_carlo(df,types,w,method,n=500,noise=.3,**params):
 rng=np.random.default_rng(2026); counts=pd.Series(0,index=df.index,dtype=float)
 for i in range(n):
  ww=w.to_numpy()*rng.uniform(1-noise,1+noise,len(w));ww=pd.Series(ww/ww.sum(),index=w.index)
  res=R.run(method,df,types,ww,**params)
  winners=res['ranks'][res['ranks']==1].index
  counts.loc[winners]+=1/len(winners)
 return pd.DataFrame({'% classé 1er':counts*100/n})
