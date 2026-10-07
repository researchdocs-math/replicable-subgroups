#!/usr/bin/env python3
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='1'
from pathlib import Path
import sys,json,argparse,time,resource
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine import Source,mine,source_table,replication_p
from replicamine.core import mine_vectorized
from replicamine.synthetic import generate
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    meta=json.loads((ROOT/'data'/'processed'/f'{name}.json').read_text())
    a=np.load(ROOT/'data'/'processed'/f'{name}.npz')
    return [Source(a[f'X{s}'],a[f'y{s}'],row['source']) for s,row in enumerate(meta['sources'])],meta

def compare(sources,groups,depth,r,case,rep,stream,modes=None):
    modes=modes or ['exhaustive','vectorized','support','positive','quorum']
    # Rotate execution order to avoid confounding algorithm and order.
    modes=modes[rep%len(modes):]+modes[:rep%len(modes)]
    expected=None;last=None
    for mode in modes:
        out=mine_vectorized(sources,groups,depth,r) if mode=='vectorized' else mine(sources,groups,depth,r,mode=mode)
        if expected is None:expected=out['rules']
        else:assert out['rules']==expected,(case,rep,mode,'mismatch')
        row=out['stats']|dict(case=case,rep=rep,n_total=sum(s.n for s in sources),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        stream.write(json.dumps(row)+'\n');stream.flush();last=out
        print(case,rep,mode,round(row['seconds'],3),row['discoveries'],flush=True)
    return last

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--part',choices=['real','scaling','large','all'],default='all');ap.add_argument('--reps',type=int,default=5);a=ap.parse_args()
    with (ROOT/'results'/f'benchmark_{a.part}.jsonl').open('w') as out:
      if a.part in ['real','all']:
       for name,r,L in [('heart',3,4),('wine',2,4),('acs',4,4)]:
        sources,meta=load(name)
        for rep in range(a.reps):
          result=compare(sources,meta['groups'],L,r,name,rep,out)
        detail=[]
        for rule in result['rules']:
          tabs=[source_table(s,rule) for s in sources]
          detail.append({'rule':rule,'description':' AND '.join(meta['literal_names'][j] for j in rule),'p_rep':replication_p([t['p'] for t in tabs],r),'tables':tabs})
        (ROOT/'results'/f'rules_{name}.json').write_text(json.dumps(detail,indent=2))
        for rv in range(2,len(sources)+1):
          if rv!=r:compare(sources,meta['groups'],L,rv,name+f'_r{rv}',0,out,['quorum'])
      if a.part in ['scaling','all']:
       cfgs=[]
       for d in [16,24,32,48,64]:cfgs.append((f'features_{d}',1000,d,5,3,4,.3))
       for L in [2,3,5,6]:cfgs.append((f'depth_{L}',1000,32,5,3,L,.3))
       for n in [250,4000,16000]:cfgs.append((f'rows_{n}',n,32,5,3,4,.3))
       for m in [3,10,20]:cfgs.append((f'sources_{m}',1000,32,m,max(2,round(.6*m)),4,.3))
       for p in [.1,.6,.85]:cfgs.append((f'density_{p}',1000,32,5,3,4,p))
       for r in [1,2,4,5]:cfgs.append((f'replication_{r}',1000,32,5,r,4,.3))
       for ci,(name,n,d,m,r,L,p) in enumerate(cfgs):
        for rep in range(a.reps):
          sources,_=generate(910000+rep,n=n,d=d,m=m,r=r,scenario='all_sources',density=p)
          compare(sources,list(range(d)),L,r,name,rep,out)
      if a.part in ['large','all']:
       for d in [64,96,128]:
        for rep in range(a.reps):
          sources,_=generate(810000+rep,n=2000,d=d,m=5,r=3,scenario='all_sources',density=.15)
          compare(sources,list(range(d)),6,3,f'large_{d}',rep,out,['quorum'])
if __name__=='__main__':main()
