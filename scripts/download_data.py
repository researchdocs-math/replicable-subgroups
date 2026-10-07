#!/usr/bin/env python3
"""Acquire and verify the seven original public-data archives."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,urllib.request,os
ROOT=Path(__file__).resolve().parents[1]
def fetch(row):
    raw=ROOT/'data'/'raw';raw.mkdir(exist_ok=True)
    dest=raw/row['name']
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()==row['sha256']:
        return row['name']+': checksum verified'
    tmp=dest.with_suffix('.part')
    req=urllib.request.Request(row['url'],headers={'User-Agent':'Quorum-reproducibility/1.0'})
    h=hashlib.sha256()
    with urllib.request.urlopen(req,timeout=180) as response,tmp.open('wb') as f:
        while True:
            block=response.read(1024*1024)
            if not block:break
            h.update(block);f.write(block)
    if h.hexdigest()!=row['sha256']:
        tmp.unlink();raise ValueError('Source checksum mismatch: '+row['name'])
    os.replace(tmp,dest)
    return row['name']+': downloaded and checksum verified'
if __name__=='__main__':
    rows=json.loads((ROOT/'data'/'sources.json').read_text())
    with ThreadPoolExecutor(max_workers=3) as pool:
        for message in pool.map(fetch,rows):print(message,flush=True)
