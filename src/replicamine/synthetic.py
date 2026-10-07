"""Heterogeneous-source generators with analytic population truth."""
import numpy as np
from .core import Source

def generate(seed,n=500,d=16,m=5,r=3,scenario='replicated',density=.3,effect=.45):
    rng=np.random.default_rng(seed);sources=[];truth=[]
    for s in range(m):
        ns=max(40,round(n*(.6+.8*s/max(m-1,1))))
        freq=np.full(d,density)*(0.7+.6*s/max(m-1,1))
        freq=np.clip(freq,.03,.85)
        X=rng.random((ns,d))<freq
        baseline=.08+.12*s/max(m-1,1)
        terms=[]
        if scenario=='global_null':pass
        elif scenario=='partial_null':
            if s<r-1:terms=[((0,1),effect)]
        elif scenario=='replicated':
            if s<r:terms=[((0,1),effect)]
        elif scenario=='all_sources':terms=[((0,1),effect)]
        elif scenario=='reversal':
            baseline=.45;terms=[((0,1),effect if s<r else -effect)]
        elif scenario=='mixed':
            if s<r:terms.append(((0,1),.35))
            if s>=m-2:terms.append(((2,3),.35))
        elif scenario=='dependent_null':
            latent=rng.random(ns)<.35
            X=np.where((rng.random((ns,d))<.6),latent[:,None],X)
        else:raise ValueError(scenario)
        prob=np.full(ns,baseline)
        for feat,coef in terms:prob+=coef*np.all(X[:,feat],axis=1)
        if prob.min()<0 or prob.max()>1:raise ValueError('invalid outcome probability')
        y=rng.random(ns)<prob
        sources.append(Source(X,y,f'S{s+1}'))
        truth.append({'freq':freq,'terms':terms,'baseline':baseline})
    return sources,truth

def population_replicates(rule,truth):
    count=0;R=set(rule)
    for s in truth:
        diff=0.
        for feat,coef in s['terms']:
            conditional=np.prod([s['freq'][j] for j in feat if j not in R])
            marginal=np.prod([s['freq'][j] for j in feat])
            diff+=coef*(conditional-marginal)
        count+=diff>1e-12
    return count
