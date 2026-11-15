"""Ejecuta suites y conserva evidencia EV3; nunca provisiona/despliega."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import unittest
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def stamp():return datetime.now(ZoneInfo('America/Santiago')).isoformat(timespec='seconds')

def source_hashes(root,files):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def code_revision(root,files):
    """Distingue la base de comparación, HEAD y los archivos realmente ejecutados."""
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=root,text=True,encoding='utf-8').strip()
    head=git('rev-parse','HEAD')
    blobs={}
    for line in git('ls-tree','-r',head).splitlines():
        metadata,path=line.split('\t',1)
        blobs[path]=metadata.split()[2]
    sources={}
    for path in files:
        name=path.relative_to(root).as_posix()
        # Git aplica los atributos/normalización del repositorio sin escribir objetos.
        current=git('hash-object','--path='+name,'--',name)
        sources[name]=dict(head_blob=blobs.get(name),worktree_blob=current,matches_head=blobs.get(name)==current)
    status=git('status','--porcelain=v1','--untracked-files=all')
    try:
        base=dict(reference='origin/main',commit=git('merge-base',head,'origin/main'))
    except subprocess.CalledProcessError:
        base=dict(reference='origin/main',commit=None)
    return dict(head_commit=head,branch=git('branch','--show-current'),comparison_base=base,
                worktree_clean=not status,status_porcelain=status,
                source_matches_head=all(row['matches_head'] for row in sources.values()),source_git_blobs=sources)

class Results(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.records=[];self.current={}
    def startTest(self,test):
        super().startTest(test);self.started=time.monotonic();self.current=dict(test=test.id(),status='running',started_at=stamp())
    def addSuccess(self,test):super().addSuccess(test);self.current['status']='passed'
    def addSkip(self,test,reason):super().addSkip(test,reason);self.current.update(status='skipped',reason=reason)
    def addFailure(self,test,err):super().addFailure(test,err);self.current.update(status='failed',error_type=err[0].__name__)
    def addError(self,test,err):super().addError(test,err);self.current.update(status='error',error_type=err[0].__name__)
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err:self.current.update(status='failed',error_type=err[0].__name__)
    def stopTest(self,test):
        self.current['duration_seconds']=round(time.monotonic()-self.started,3)
        if hasattr(test,'evidence'):self.current['facts']=test.evidence
        self.records.append(dict(self.current));super().stopTest(test)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/EV3_CHRISTIAN_TEST_RESULTS.json');args=parser.parse_args()
    if args.output.exists():parser.error('La evidencia ya existe; usa --output con un archivo nuevo para conservar el histórico.')
    os.chdir(ROOT)
    # La suite solo puede usar SQLite temporal y el usuario PostgreSQL de pruebas.
    from urllib.parse import urlsplit
    url=os.environ.get('PUENTES_TEST_DATABASE_URL','')
    if url and not (urlsplit(url).username or '').startswith('puentes_test.'):
        raise ValueError('Se requiere el rol PostgreSQL restringido puentes_test.')
    for key in ('DATABASE_URL','DATABASE_SCHEMA','VERCEL','PROJECT_STAGE','PHOTO_STORAGE','SUPABASE_URL','SUPABASE_SECRET_KEY','SUPABASE_STORAGE_BUCKET','CLOUD_PROVIDER','CRON_SECRET','SECRET_KEY','COOKIE_SECURE','IOT_API_KEY','PROVIDER_URL','PROVIDER_TOKEN','IOT_POLL_INTERVAL','PUENTES_MIGRATION_DATABASE_URL'):
        os.environ.pop(key,None)
    started=stamp()
    files=[*sorted(ROOT.glob('*.py')),*sorted(ROOT.glob('*.sql')),ROOT/'vercel.json',ROOT/'config/ev2_pilot.json',*sorted((ROOT/'sql').glob('*.sql')),*sorted((ROOT/'templates').glob('*.html')),*sorted((ROOT/'tests').glob('*.py')),*sorted((ROOT/'tests/fixtures').glob('*.sql')),*sorted((ROOT/'tests').glob('*.cjs')),*sorted((ROOT/'static').glob('*.js')),ROOT/'static/app.css',*sorted((ROOT/'tools').glob('*.py'))]
    hashes=source_hashes(ROOT,files)
    revision=code_revision(ROOT,files)
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
    result=unittest.TextTestRunner(verbosity=2,resultclass=Results).run(suite)
    js=subprocess.run(['node','--test','--test-reporter=tap','tests/frontend.test.cjs','tests/cloud-uploads.test.cjs','tests/notifications.test.cjs'],cwd=ROOT,text=True,capture_output=True,encoding='utf-8')
    print(js.stdout)
    counts={key:int(value) for key,value in re.findall(r'^# (tests|pass|fail|skipped) (\d+)$',js.stdout,re.M)}
    final_hashes=source_hashes(ROOT,files)
    final_revision=code_revision(ROOT,files)
    stable=hashes==final_hashes and revision['head_commit']==final_revision['head_commit']
    output=dict(started_at=started,finished_at=stamp(),timezone='America/Santiago',
        comparison_base=revision['comparison_base'],tested_revision=revision,finished_revision=final_revision,
        source_unchanged_during_run=stable,source_sha256_finished=final_hashes,
        environment=dict(python=platform.python_version(),platform=platform.platform(),sqlite=__import__('sqlite3').sqlite_version,
                         postgres_tests_enabled=bool(os.environ.get('PUENTES_TEST_DATABASE_URL')),production_database_used=False),
        source_sha256=hashes,python=dict(run=result.testsRun,passed=sum(r['status']=='passed' for r in result.records),skipped=len(result.skipped),failures=len(result.failures),errors=len(result.errors),cases=result.records),
        javascript=dict(exit_code=js.returncode,counts=counts,stdout=js.stdout,stderr=js.stderr))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evidencia guardada en '+str(args.output))
    return 0 if result.wasSuccessful() and js.returncode==0 and stable else 1

if __name__=='__main__':raise SystemExit(main())
