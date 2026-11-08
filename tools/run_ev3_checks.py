"""Ejecuta suites y conserva evidencia real de B-11; nunca provisiona/despliega."""
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
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/EV3_B11_TEST_RESULTS.json');args=parser.parse_args()
    os.chdir(ROOT)
    # La suite solo puede usar SQLite temporal y el usuario PostgreSQL de pruebas.
    from urllib.parse import urlsplit
    url=os.environ.get('PUENTES_TEST_DATABASE_URL','')
    if url and not (urlsplit(url).username or '').startswith('puentes_test.'):
        raise ValueError('Se requiere el rol PostgreSQL restringido puentes_test.')
    for key in ('DATABASE_URL','DATABASE_SCHEMA','VERCEL','PROJECT_STAGE','PHOTO_STORAGE','SUPABASE_URL','SUPABASE_SECRET_KEY','SUPABASE_STORAGE_BUCKET','CLOUD_PROVIDER','CRON_SECRET','SECRET_KEY','COOKIE_SECURE','IOT_API_KEY','PROVIDER_URL','PROVIDER_TOKEN','IOT_POLL_INTERVAL'):
        os.environ.pop(key,None)
    started=stamp()
    base=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    files=[ROOT/'app.py',ROOT/'display_time.py',ROOT/'pilot_time.py',*sorted((ROOT/'templates').glob('*.html')),*sorted((ROOT/'tests').glob('test_*.py')),*sorted((ROOT/'tests').glob('*.cjs')),ROOT/'static/app.js',ROOT/'static/notifications.js',ROOT/'static/app.css',Path(__file__)]
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),top_level_dir=str(ROOT))
    result=unittest.TextTestRunner(verbosity=2,resultclass=Results).run(suite)
    js=subprocess.run(['node','--test','--test-reporter=tap','tests/frontend.test.cjs','tests/cloud-uploads.test.cjs','tests/notifications.test.cjs'],cwd=ROOT,text=True,capture_output=True,encoding='utf-8')
    print(js.stdout)
    counts={key:int(value) for key,value in re.findall(r'^# (tests|pass|fail|skipped) (\d+)$',js.stdout,re.M)}
    output=dict(started_at=started,finished_at=stamp(),timezone='America/Santiago',base_commit=base,
        environment=dict(python=platform.python_version(),platform=platform.platform(),sqlite=__import__('sqlite3').sqlite_version,
                         postgres_tests_enabled=bool(os.environ.get('PUENTES_TEST_DATABASE_URL')),production_database_used=False),
        source_sha256=hashes,python=dict(run=result.testsRun,passed=sum(r['status']=='passed' for r in result.records),skipped=len(result.skipped),failures=len(result.failures),errors=len(result.errors),cases=result.records),
        javascript=dict(exit_code=js.returncode,counts=counts,stdout=js.stdout,stderr=js.stderr))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Evidencia guardada en '+str(args.output))
    return 0 if result.wasSuccessful() and js.returncode==0 else 1

if __name__=='__main__':raise SystemExit(main())
