#!/usr/bin/env python3
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='1'
import sys,json,argparse,itertools,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.stats import hypergeom
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine import mine
from replicamine.core import pack
from replicamine.synthetic import generate,population_replicates
ROOT=Path(__file__).resolve().parents[1]

def trial(job):
    scenario,n,seed=job;d=12;m=5;r=3;L=3
    sources,truth=generate(seed,n=n,d=d,m=m,r=r,scenario=scenario)
    rules=[c for l in range(1,L+1) for c in itertools.combinations(range(d),l)]
    M=len(rules);p=[];aa=[];xx=[]
    for source in sources:
        full=[pack(source.X[:,j]) for j in range(d)];yb=pack(source.y)
        a=[];x=[]
        for rule in rules:
            b=(1<<source.n)-1
            for j in rule:b&=full[j]
            x.append(b.bit_count());a.append((b&yb).bit_count())
        aa.append(a);xx.append(x)
        p.append(hypergeom.sf(np.array(a)-1,source.n,source.k,np.array(x)))
    p=np.array(p);pc=np.minimum(1,(m-r+1)*np.sort(p,axis=0)[r-1])
    counts=np.array([population_replicates(rule,truth) for rule in rules])
    null=counts<r
    res=mine(sources,list(range(d)),L,r,mode='quorum')
    expected=[rules[j] for j in np.flatnonzero(pc<=.05/M)]
    assert sorted(expected)==res['rules'],(scenario,n,seed,'discovery mismatch')
    pooled=hypergeom.sf(np.sum(aa,axis=0)-1,sum(s.n for s in sources),sum(s.k for s in sources),np.sum(xx,axis=0))
    selectors={'quorum':pc<=.05/M,
               'source_bonferroni':(p<=.05/(M*m)).sum(axis=0)>=r,
               'pooled':pooled<=.05/M,
               'uncorrected_replication':(p<=.05).sum(axis=0)>=r}
    rows=[]
    for method,sel in selectors.items():
        rows.append(dict(scenario=scenario,n=n,seed=seed,method=method,
                         false_any=bool(np.any(sel&null)),false_count=int((sel&null).sum()),
                         discoveries=int(sel.sum()),true_count=int((sel&~null).sum()),
                         true_family=int((~null).sum()),
                         planted_found=bool(sel[rules.index((0,1))]),
                         seconds=res['stats']['seconds'] if method=='quorum' else None))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--reps',type=int,default=1000);ap.add_argument('--output',default='simulation.jsonl');args=ap.parse_args()
    cases=[(s,500) for s in ['global_null','partial_null','dependent_null','mixed','replicated','reversal']]
    cases += [('replicated',n) for n in [150,300,1000,2000]]
    jobs=[(s,n,2026100600+ci*100000+j) for ci,(s,n) in enumerate(cases) for j in range(args.reps)]
    out=ROOT/'results'/args.output
    with out.open('w') as f,ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i,rows in enumerate(ex.map(trial,jobs,chunksize=10)):
            for row in rows:f.write(json.dumps(row)+'\n')
            if (i+1)%250==0:f.flush();print(f'{i+1}/{len(jobs)} completed',flush=True)
    print(out,flush=True)
if __name__=='__main__':main()
