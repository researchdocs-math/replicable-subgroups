#!/usr/bin/env python3
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='1'
from pathlib import Path
import sys,json,multiprocessing,resource
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine import mine
from replicamine.core import mine_vectorized
from replicamine.synthetic import generate
ROOT=Path(__file__).resolve().parents[1]
def task(cfg,q):
    d,L,mode=cfg
    src,_=generate(910000,n=1000,d=d,m=5,r=3,scenario='all_sources',density=.3)
    out=mine_vectorized(src,list(range(d)),L,3) if mode=='vectorized' else mine(src,list(range(d)),L,3,mode=mode)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform!='darwin':peak*=1024
    q.put(dict(d=d,depth=L,mode=mode,peak_rss_bytes=peak,discoveries=out['stats']['discoveries'],family=out['stats']['family']))
if __name__=='__main__':
    rows=[];ctx=multiprocessing.get_context('spawn')
    for d,L in [(32,4),(32,6),(64,4)]:
      for mode in ['exhaustive','vectorized','quorum']:
        q=ctx.Queue();p=ctx.Process(target=task,args=((d,L,mode),q));p.start();row=q.get(timeout=180);p.join();assert p.exitcode==0;rows.append(row);print(row,flush=True)
    (ROOT/'results'/'memory.json').write_text(json.dumps(rows,indent=2))
