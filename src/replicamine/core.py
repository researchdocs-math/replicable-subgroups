"""Fixed-family exact inference and bit-parallel quorum search.

The family, direction, replication count and alpha must be fixed independently
of the tested labels. Numerical comparisons use a 1e-12 relative tolerance only
for conservative retention at pruning boundaries.
"""
from dataclasses import dataclass
from itertools import combinations
from math import comb, log
from time import perf_counter
import numpy as np
from scipy.stats import hypergeom

@dataclass
class Source:
    X: np.ndarray
    y: np.ndarray
    name: str = ''
    def __post_init__(self):
        self.X=np.asarray(self.X,dtype=bool)
        self.y=np.asarray(self.y,dtype=bool)
        if self.X.ndim!=2 or len(self.X)!=len(self.y):
            raise ValueError('X must be a matrix with one row per outcome')
        self.n=len(self.y); self.k=int(self.y.sum())

def pack(v):
    return int.from_bytes(np.packbits(v,bitorder='little').tobytes(),'little')

def family_size(groups,depth):
    """Coefficient sum of product_g (1 + number_of_literals_g z)."""
    vals,counts=np.unique(groups,return_counts=True)
    c=[1]+[0]*depth
    for b in counts:
        for j in range(depth,0,-1): c[j]+=int(b)*c[j-1]
    return sum(c[1:])

def cutoff(n,k,beta):
    """Minimum positive support whose all-positive table can pass beta."""
    if k==0 or k==n:return n+1
    a=np.arange(1,k+1,dtype=float)
    lp=np.concatenate(([0.], np.cumsum(np.log(k-a+1)-np.log(n-a+1))))
    ok=np.flatnonzero(lp<=log(beta)+1e-12)
    return int(ok[0]) if len(ok) else n+1

def source_table(source,rule):
    mask=np.all(source.X[:,rule],axis=1)
    x=int(mask.sum());a=int((mask & source.y).sum())
    return {'n':source.n,'k':source.k,'x':x,'a':a,
            'p':float(hypergeom.sf(a-1,source.n,source.k,x)),
            'risk_difference': (a/x-(source.k-a)/(source.n-x)) if 0<x<source.n else 0.}

def replication_p(ps,r):
    return min(1.,(len(ps)-r+1)*sorted(ps)[r-1])

def mine(sources,groups,depth=3,r=None,alpha=.05,mode='quorum',collect=True):
    """Find exactly all p_rep <= alpha/M; modes share one traversal and tests.

    exhaustive: no statistical branch pruning.
    support: classical margin-only descendant bound combined over sources.
    positive: observed-positive descendant bound, keeping all source indexes.
    quorum: positive-only vertical search, retire impossible source indexes,
            materialize negative intersections only for candidate tests.
    """
    start=perf_counter();m=len(sources);r=m if r is None else r
    if not 1<=r<=m or mode not in ('exhaustive','support','positive','quorum'):
        raise ValueError('invalid r or search mode')
    d=len(groups);M=family_size(groups,depth);beta=alpha/(M*(m-r+1))
    groups=tuple(groups);cut=[cutoff(s.n,s.k,beta) for s in sources]
    pos=[[pack(s.X[:,j]&s.y) for j in range(d)] for s in sources]
    neg=[[pack(s.X[:,j]&~s.y) for j in range(d)] for s in sources]
    full=[[pos[s][j]|neg[s][j] for j in range(d)] for s in range(m)]
    ybits=[pack(s.y) for s in sources]
    caches=[{} for _ in sources]
    stats=dict(mode=mode,m=m,r=r,d=d,depth=depth,family=M,beta=beta,
               visited=0,pruned=0,intersections=0,exact_tests=0,table_requests=0,
               retired=0,discoveries=0,cutoffs=cut)
    found=[]
    def pval(s,a,x):
        stats['table_requests']+=1;key=(a,x)
        if key not in caches[s]:
            caches[s][key]=float(hypergeom.sf(a-1,sources[s].n,sources[s].k,x))
            stats['exact_tests']+=1
        return caches[s][key]
    def visit(rule,used,bits,active,get_negative=None):
        last=rule[-1] if rule else -1
        for j in range(last+1,d):
            if groups[j] in used:continue
            rr=rule+(j,);stats['visited']+=1
            if mode=='quorum':
                bb={};aa={}
                for s in active:
                    b=bits[s]&pos[s][j];stats['intersections']+=1
                    a=b.bit_count()
                    if a>=cut[s]:bb[s]=b;aa[s]=a
                    else:stats['retired']+=1
                live=list(bb)
                if len(live)<r:stats['pruned']+=1;continue
                # Sources with stronger attainable evidence first; affects cost only.
                live.sort(key=lambda s:aa[s]/max(cut[s],1),reverse=True)
                neg_cache={}
                def child_negative(s,parent=get_negative,item=j,cache=neg_cache):
                    if s not in cache:
                        cache[s]=parent(s)&neg[s][item]
                        stats['intersections']+=1
                    return cache[s]
                success=0;remaining=len(live)
                for s in live:
                    nb=child_negative(s)
                    if pval(s,aa[s],aa[s]+nb.bit_count())<=beta:success+=1
                    remaining-=1
                    if success>=r or success+remaining<r:break
            else:
                bb=[bits[s]&full[s][j] for s in range(m)];stats['intersections']+=m
                xx=[b.bit_count() for b in bb]
                if mode=='support' and sum(x>=cut[s] for s,x in enumerate(xx))<r:
                    stats['pruned']+=1;continue
                aa=[]
                for s in range(m):
                    aa.append((bb[s]&ybits[s]).bit_count());stats['intersections']+=1
                if mode=='positive' and sum(a>=cut[s] for s,a in enumerate(aa))<r:
                    stats['pruned']+=1;continue
                success=0;remaining=m
                for s in range(m):
                    if pval(s,aa[s],xx[s])<=beta:success+=1
                    remaining-=1
                    if success>=r or success+remaining<r:break
            if success>=r:
                stats['discoveries']+=1
                if collect:found.append(rr)
            if len(rr)<depth:
                visit(rr,used|{groups[j]},bb,list(bb) if mode=='quorum' else active,child_negative if mode=='quorum' else None)
    if mode=='quorum':
        bits={s:ybits[s] for s in range(m)}
    else:bits=[(1<<s.n)-1 for s in sources]
    visit((),set(),bits,list(range(m)),lambda s:((1<<sources[s].n)-1)^ybits[s])
    stats['seconds']=perf_counter()-start
    stats['cache_entries']=sum(len(c) for c in caches)
    return {'rules':sorted(found),'stats':stats}

def mine_vectorized(sources,groups,depth=3,r=None,alpha=.05):
    """Full vertical enumeration with vectorized Fisher tests on unique tables."""
    start=perf_counter();m=len(sources);r=m if r is None else r
    M=family_size(groups,depth);d=len(groups);rules=[]
    for l in range(1,depth+1):
        rules.extend(c for c in combinations(range(d),l) if len({groups[j] for j in c})==l)
    ps=[];tests=0;intersections=0
    for s in sources:
        full=[pack(s.X[:,j]) for j in range(d)];yb=pack(s.y)
        tables=np.empty((M,2),dtype=np.int64)
        # Eclat-style depth-first vertical intersections, same order as rule map.
        tablemap={}
        def dfs(prefix,bits,used):
            nonlocal intersections
            for j in range(prefix[-1]+1 if prefix else 0,d):
                if groups[j] in used:continue
                b=bits&full[j];intersections+=2
                rule=prefix+(j,);tablemap[rule]=((b&yb).bit_count(),b.bit_count())
                if len(rule)<depth:dfs(rule,b,used|{groups[j]})
        dfs((),(1<<s.n)-1,set())
        for i,rule in enumerate(rules):tables[i]=tablemap[rule]
        del tablemap
        uniq,inv=np.unique(tables,axis=0,return_inverse=True)
        pv=hypergeom.sf(uniq[:,0]-1,s.n,s.k,uniq[:,1]);tests+=len(uniq)
        ps.append(pv[inv])
    pc=np.minimum(1,(m-r+1)*np.sort(np.array(ps),axis=0)[r-1])
    selected=np.flatnonzero(pc<=alpha/M)
    return {'rules':sorted(rules[i] for i in selected),
            'stats':dict(mode='vectorized',m=m,r=r,d=d,depth=depth,family=M,
                         visited=M,pruned=0,intersections=intersections,exact_tests=tests,
                         table_requests=m*M,retired=0,discoveries=len(selected),
                         seconds=perf_counter()-start)}
