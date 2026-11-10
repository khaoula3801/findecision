import numpy as np
import pandas as pd
from . import engine as E

def adapt(result,crit):
 s=result['steps']
 steps=[]
 for k,v in s.items():
  a=np.asarray(v)
  if a.ndim==2: obj=pd.DataFrame(a,index=crit if a.shape[0]==len(crit) else None,columns=crit if a.shape[1]==len(crit) else None)
  elif a.ndim==1:obj=pd.Series(a,index=crit if len(a)==len(crit) else None)
  else:obj=pd.DataFrame({'Valeur':[v]})
  steps.append((k,'',obj))
 return {'weights':pd.Series(result['weights'],index=crit),'steps':steps,'info':('AHP : CR = %.4f — %s'%(s['CR'],'cohérent' if s['CR']<.1 else 'jugements à revoir') if 'CR' in s else 'BWM : écart optimal ξ* = %.4f'%s['Écart maximal ξ*'] if 'Écart maximal ξ*' in s else None)}
def equal(crit):return {'weights':pd.Series(np.ones(len(crit))/len(crit),index=crit),'steps':[],'info':None}
def ahp(M,crit):return adapt(E.ahp(M),crit)
def bwm(crit,best,worst,bo,ow):
 b=crit.index(best);worstidx=crit.index(worst)
 # tie BO[Worst] and OW[Best] as required by the linear optimization
 boval=np.array([bo[c] for c in crit],dtype=float);owval=np.array([ow[c] for c in crit],dtype=float)
 if boval[worstidx]!=owval[b]:raise ValueError('Les deux évaluations Best/Worst doivent être égales : BO[Worst] = OW[Best].')
 return adapt(E.bwm(b,worstidx,boval,owval),crit)
def entropy(df,types=None):return adapt(E.entropy(df.values,[types[c] for c in df.columns] if types else ['max']*len(df.columns)),list(df.columns))
def critic(df,types):return adapt(E.critic(df.values,[types[c] for c in df.columns]),list(df.columns))
