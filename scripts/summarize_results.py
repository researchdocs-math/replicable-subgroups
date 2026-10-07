#!/usr/bin/env python3
from pathlib import Path
import json
import pandas as pd
import numpy as np
from scipy.stats import beta
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'results'
def interval(k,n):
 return [0. if k==0 else float(beta.ppf(.025,k,n-k+1)),1. if k==n else float(beta.ppf(.975,k+1,n-k))]
def main():
 sim=pd.read_json(R/'simulation.jsonl',lines=True);rows=[]
 for (scenario,n,method),g in sim.groupby(['scenario','n','method']):
  k=int(g.false_any.sum());N=len(g);ci=interval(k,N);pk=int(g.planted_found.sum());pci=interval(pk,N)
  rows.append(dict(scenario=scenario,n=n,method=method,runs=N,false_events=k,fwer=k/N,fwer_low=ci[0],fwer_high=ci[1],planted_recall=pk/N,recall_low=pci[0],recall_high=pci[1],mean_discoveries=float(g.discoveries.mean())))
 pd.DataFrame(rows).to_csv(R/'simulation_summary.csv',index=False)
 stress=pd.read_json(R/'stress.jsonl',lines=True);sr=[]
 for scenario,g in stress.groupby('scenario'):
  k=int(g.false_any.sum());N=len(g);ci=interval(k,N)
  sr.append(dict(scenario=scenario,runs=N,false_events=k,fwer=k/N,low=ci[0],high=ci[1]))
 pd.DataFrame(sr).to_csv(R/'stress_summary.csv',index=False)
 b=pd.read_json(R/'benchmark_all.jsonl',lines=True)
 summary=b.groupby(['case','mode']).agg(seconds=('seconds','median'),q25=('seconds',lambda x:x.quantile(.25)),q75=('seconds',lambda x:x.quantile(.75)),family=('family','first'),visited=('visited','median'),intersections=('intersections','median'),exact_tests=('exact_tests','median'),discoveries=('discoveries','median'),n_total=('n_total','first'),peak_rss_bytes=('peak_rss_bytes','max')).reset_index()
 summary.to_csv(R/'benchmark_summary.csv',index=False)
 dev=pd.read_json(R/'devices.json');dev.groupby(['n','method']).seconds.agg(['median','min','max']).to_csv(R/'device_summary.csv')
 report={'simulation_runs':len(sim[sim.method=='quorum']),'stress_runs':len(stress),'verification':json.loads((R/'verification.json').read_text()),'cases':len(b.case.unique()),'algorithm_runs':len(b),'real':{}}
 for name in ['heart','wine','acs']:
  rules=json.loads((R/f'rules_{name}.json').read_text())
  report['real'][name]={'discoveries':len(rules),'minimal_rules':sum(not any(set(q['rule'])<set(p['rule']) for q in rules) for p in rules)}
 (R/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
