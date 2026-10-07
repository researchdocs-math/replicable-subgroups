#!/usr/bin/env python3
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='1'
from pathlib import Path
import sys,json,itertools,argparse
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine import Source,mine
ROOT=Path(__file__).resolve().parents[1]

def trial(job):
    kind,seed=job;rng=np.random.default_rng(seed);m=5
    if kind=='shared_sources':
        X=rng.random((1000,12))<.5;y=rng.random(1000)<.5
        sources=[Source(X,y) for s in range(m)];r=3;d=12
    elif kind=='global_r1':
        sources=[Source(rng.random((1000,12))<.5,rng.random(1000)<.5) for s in range(m)];r=1;d=12
    else:
        d=8;r=5;sources=[]
        for s in range(m):
            X=rng.random((5000,d))<.5
            prob=expit(1.5*(X.sum(axis=1)-4)) if s<4 else np.full(5000,.5)
            sources.append(Source(X,rng.random(5000)<prob))
    out=mine(sources,list(range(d)),3,r,mode='quorum')
    # Every replication hypothesis is null in these stress scenarios.
    return {'scenario':kind,'seed':seed,'r':r,'false_any':out['stats']['discoveries']>0,'discoveries':out['stats']['discoveries']}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=8);parser.add_argument('--reps',type=int,default=1000);parser.add_argument('--output',default='stress.jsonl');args=parser.parse_args()
    jobs=[(s,730000+si*10000+i) for si,s in enumerate(['shared_sources','global_r1','least_favourable']) for i in range(args.reps)]
    with (ROOT/'results'/args.output).open('w') as f,ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i,row in enumerate(ex.map(trial,jobs,chunksize=5)):
            f.write(json.dumps(row)+'\n')
            if (i+1)%250==0:f.flush();print(i+1,flush=True)
