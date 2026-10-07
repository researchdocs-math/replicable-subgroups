#!/usr/bin/env python3
import sys,itertools,json
from pathlib import Path
import numpy as np
from scipy.stats import hypergeom
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine import Source,mine,family_size
from replicamine.core import cutoff

def main():
    checked=0
    # Enumerate every valid parent/descendant two-by-two table for N <= 14.
    for n in range(2,15):
      for k in range(n+1):
       for a in range(k+1):
        phi=hypergeom.sf(a-1,n,k,a)
        for b in range(n-k+1):
         for ap in range(a+1):
          for bp in range(b+1):
           p=hypergeom.sf(ap-1,n,k,ap+bp)
           assert p+1e-13>=phi,(n,k,a,b,ap,bp,p,phi)
           checked+=1
    rng=np.random.default_rng(34091);trials=0
    for seed in range(120):
      m=int(rng.integers(2,7));d=int(rng.integers(4,10));r=int(rng.integers(1,m+1));L=min(4,d)
      sources=[]
      for s in range(m):
       n=int(rng.integers(20,300));X=rng.random((n,d))<rng.uniform(.05,.9)
       y=rng.random(n)<rng.choice([0.,.03,.2,.5,.9,1.]);sources.append(Source(X,y))
      groups=list(range(d)) if seed%2 else [j//2 for j in range(d)]
      vals=[mine(sources,groups,L,r,alpha=.05,mode=t) for t in ['exhaustive','support','positive','quorum']]
      assert all(v['rules']==vals[0]['rules'] for v in vals)
      assert vals[0]['stats']['visited']==family_size(groups,L)
      trials+=1
    out={'table_inequalities_verified':checked,'randomized_exact_set_comparisons':trials,'status':'passed'}
    p=Path(__file__).resolve().parents[1]/'results'/'verification.json';p.write_text(json.dumps(out,indent=2));print(out)
if __name__=='__main__':main()
