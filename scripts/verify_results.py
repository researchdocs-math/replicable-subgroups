#!/usr/bin/env python3
"""Verify deterministic experiment outputs against the released signatures."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def signatures():
    result={}
    for name in ['simulation.jsonl','stress.jsonl','benchmark_all.jsonl']:
        rows=[json.loads(line) for line in (ROOT/'results'/name).read_text().splitlines() if line.strip()]
        # Elapsed time and peak memory depend on machine and scheduling.
        for row in rows:
            for key in ['seconds','peak_rss_bytes']:row.pop(key,None)
        result[name]={'records':len(rows),'sha256':digest(rows)}
    for name in ['heart','wine','acs']:
        rows=json.loads((ROOT/'results'/('rules_'+name+'.json')).read_text())
        # Test tails are floating-point; verify rules and exact contingency counts.
        obj=[{'rule':r['rule'],'tables':[{k:v for k,v in t.items() if k not in ['p','risk_difference']} for t in r['tables']]} for r in rows]
        result['rules_'+name]={'records':len(obj),'sha256':digest(obj)}
        arrays=np.load(ROOT/'data'/'processed'/(name+'.npz'))
        for key in sorted(arrays.files):
            a=np.ascontiguousarray(arrays[key]);h=hashlib.sha256(a.tobytes()).hexdigest()
            result['matrix_'+name+'_'+key]={'shape':list(a.shape),'dtype':str(a.dtype),'sha256':h}
    return result
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--record',action='store_true');a=ap.parse_args()
    got=signatures();path=ROOT/'expected'/'signatures.json'
    if a.record:
        path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(got,indent=2));print('Recorded deterministic signatures.')
    else:
        expected=json.loads(path.read_text())
        bad=[key for key in set(got)|set(expected) if got.get(key)!=expected.get(key)]
        if bad:raise AssertionError('Result mismatch: '+', '.join(sorted(bad)))
        print('All deterministic simulation, stress, search, rule, and matrix signatures match.')
