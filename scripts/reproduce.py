#!/usr/bin/env python3
"""Run the experiment workflow with preserved reference signatures."""
from pathlib import Path
import argparse,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
def run(script,*args):
    command=[sys.executable,str(ROOT/'scripts'/script),*map(str,args)]
    print('Running '+script+' '+ ' '.join(map(str,args)),flush=True)
    subprocess.run(command,cwd=ROOT,check=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--smoke',action='store_true');ap.add_argument('--rebuild-data',action='store_true');ap.add_argument('--gpu',action='store_true');a=ap.parse_args()
    (ROOT/'results').mkdir(exist_ok=True)
    if a.rebuild_data:run('download_data.py');run('prepare_data.py')
    run('verify_algorithm.py')
    if a.smoke:
        run('run_simulations.py','--workers',a.workers,'--reps',2,'--output','smoke_simulation.jsonl')
        run('run_stress.py','--workers',a.workers,'--reps',2,'--output','smoke_stress.jsonl')
    else:
        run('run_benchmarks.py','--part','all','--reps',5)
        run('measure_memory.py')
        run('run_simulations.py','--workers',a.workers,'--reps',1000)
        run('run_stress.py','--workers',a.workers,'--reps',1000)
        if a.gpu:run('benchmark_devices.py')
        run('summarize_results.py');run('verify_results.py')
    print('Experiment workflow completed.',flush=True)
