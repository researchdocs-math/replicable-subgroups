#!/usr/bin/env python3
"""Build common-schema, disjoint-source benchmark matrices."""
from pathlib import Path
import json,zipfile,sys,hashlib,math
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data'/'raw';OUT=ROOT/'data'/'processed';OUT.mkdir(exist_ok=True)

def json_safe(x):
    if isinstance(x, float) and not math.isfinite(x):
        return 'inf' if x > 0 else '-inf'
    if isinstance(x, (list, tuple)): return [json_safe(v) for v in x]
    if isinstance(x, dict): return {k:json_safe(v) for k,v in x.items()}
    return x

def build(name,frames,features,categorical,outcome,cap=None):
    rng=np.random.default_rng(20261006);design=[];test=[];info=[]
    for sn,df in frames:
        raw=len(df);df=df.dropna(subset=features+[outcome]);complete=len(df)
        unique=len(df)
        idx=rng.permutation(len(df));df=df.iloc[idx[:cap] if cap else idx].reset_index(drop=True)
        cut=int(.2*len(df));design.append(df.iloc[:cut]);test.append(df.iloc[cut:])
        info.append(dict(source=sn,input_rows=raw,complete_rows=complete,unique_rows=unique,design_rows=cut,test_rows=len(df)-cut,positives=int(df.iloc[cut:][outcome].sum())))
    train=pd.concat(design,ignore_index=True);spec=[];groups=[];names=[]
    for g,f in enumerate(features):
        if f in categorical:
            levels=categorical[f]
            for v in levels:spec.append((f,'eq',v));groups.append(g);names.append(f'{f}={v}')
        else:
            edges=np.unique(train[f].quantile([1/3,2/3]).values).tolist()
            edges=[-np.inf]+edges+[np.inf]
            for lo,hi in zip(edges[:-1],edges[1:]):
                spec.append((f,'bin',[lo,hi]));groups.append(g);names.append(f'{f} in ({lo:.6g},{hi:.6g}]')
    arrays={}
    for s,df in enumerate(test):
        cols=[]
        for f,op,v in spec:
            if op=='eq':cols.append(df[f].to_numpy()==v)
            else:cols.append((df[f].to_numpy()>v[0]) & (df[f].to_numpy()<=v[1]))
        arrays[f'X{s}']=np.array(cols,dtype=bool).T;arrays[f'y{s}']=df[outcome].to_numpy(dtype=bool)
    np.savez_compressed(OUT/f'{name}.npz',**arrays)
    meta={'name':name,'sources':info,'features':features,'literal_names':names,'groups':groups,'predicate_spec':spec,'design_seed':20261006,'outcome':outcome}
    (OUT/f'{name}.json').write_text(json.dumps(json_safe(meta),indent=2,allow_nan=False))
    print(name,info,'literals',len(groups),flush=True)

def main():
    cols=['age','sex','cp','trestbps','chol','fbs','restecg','thalach','exang','oldpeak','slope','ca','thal','num']
    frames=[]
    with zipfile.ZipFile(RAW/'heart.zip') as z:
        for f in ['cleveland','hungarian','switzerland','va']:
            df=pd.read_csv(z.open('processed.'+f+'.data'),names=cols,na_values='?')
            df['disease']=df['num']>0;frames.append((f,df))
    build('heart',frames,['age','sex','cp','trestbps','thalach','exang','oldpeak'],{'sex':[0,1],'cp':[1,2,3,4],'exang':[0,1]},'disease')
    frames=[]
    with zipfile.ZipFile(RAW/'wine.zip') as z:
        for f in ['red','white']:
            df=pd.read_csv(z.open(f'winequality-{f}.csv'),sep=';');df['quality_ge6']=df['quality']>=6;frames.append((f,df))
    # Duplicate identity includes the original score before binary coarsening.
    frames=[(s,d.drop_duplicates(subset=list(d.columns))) for s,d in frames]
    build('wine',frames,list(frames[0][1].columns[:11]),{},'quality_ge6')
    frames=[];eligibility=[]
    use=['SERIALNO','SPORDER','AGEP','SCHL','WKHP','MAR','COW','SEX','MIG','PINCP','RELP']
    for st in ['ca','fl','ga','ny','tx']:
        with zipfile.ZipFile(RAW/f'acs_{st}.zip') as z:
            f=[n for n in z.namelist() if n.endswith('.csv')][0]
            df=pd.read_csv(z.open(f),usecols=use,low_memory=False)
        raw=len(df)
        # Housing units only, working-age respondents with work hours and income observed.
        df=df[(df.RELP<16)&df.AGEP.between(25,64)&(df.WKHP>0)&df.PINCP.notna()]
        eligible=len(df)
        df=df.sort_values(['SERIALNO','SPORDER']).drop_duplicates('SERIALNO',keep='first')
        df['income_gt50k']=df['PINCP']>50000
        eligibility.append({'source':st,'raw':raw,'eligible_persons':eligible,'households':len(df)})
        frames.append((st,df))
    build('acs',frames,['AGEP','SCHL','WKHP','MAR','COW','SEX','MIG'],{'MAR':[1,2,3,4,5],'COW':list(range(1,10)),'SEX':[1,2],'MIG':[1,2,3]},'income_gt50k',cap=10000)
    (OUT/'acs_eligibility.json').write_text(json.dumps(eligibility,indent=2))
if __name__=='__main__':main()
