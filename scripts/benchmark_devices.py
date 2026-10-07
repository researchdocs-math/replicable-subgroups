#!/usr/bin/env python3
"""Compare identical exact support counts on bitsets, arrays, and a GPU."""
import os
for v in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS']:os.environ[v]='1'
from pathlib import Path
import sys,json,itertools,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from replicamine.core import pack
ROOT=Path(__file__).resolve().parents[1]
def main():
 import torch
 device='mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else None)
 if device is None:
  print('CPU environment: optional accelerator benchmark skipped.');return
 def sync():
  if device=='mps':torch.mps.synchronize()
  else:torch.cuda.synchronize()
 rows=[]
 for n in [1000,4000,16000]:
  rng=np.random.default_rng(20261007);X=rng.random((n,32))<.3;y=rng.random(n)<.2
  rules=np.array(list(itertools.combinations(range(32),3)));xb=[pack(X[:,j]) for j in range(32)];yb=pack(y)
  tx=torch.tensor(X.astype(np.float32),device=device);ty=torch.tensor(y.astype(np.float32),device=device)
  tr=torch.tensor(rules,dtype=torch.long,device=device)
  def bitsets():
   out=np.empty((len(rules),2),int)
   for i,(a,b,c) in enumerate(rules):
    v=xb[a]&xb[b]&xb[c];out[i]=(v.bit_count(),(v&yb).bit_count())
   return out
  def numpy_count():
   out=[]
   for start in range(0,len(rules),128):
    masks=X[:,rules[start:start+128]].all(axis=2)
    out.append(np.column_stack((masks.sum(axis=0),(masks&y[:,None]).sum(axis=0))))
   return np.vstack(out)
  def gpu_count():
   out=[]
   for start in range(0,len(rules),128):
    masks=tx[:,tr[start:start+128]].prod(dim=2)
    out.append(torch.stack((masks.sum(dim=0),(masks*ty[:,None]).sum(dim=0)),dim=1))
   return torch.cat(out).cpu().numpy().astype(int)
  expected=bitsets();gpu_count();sync()
  for method,fn in [('bitsets',bitsets),('numpy',numpy_count),('gpu',gpu_count)]:
   for rep in range(5):
    sync();t=time.perf_counter();got=fn();sync();dt=time.perf_counter()-t
    assert np.array_equal(got,expected)
    rows.append({'n':n,'rules':len(rules),'method':method,'rep':rep,'seconds':dt,'device':device})
 (ROOT/'results'/'devices.json').write_text(json.dumps(rows,indent=2));print(rows)
if __name__=='__main__':main()
