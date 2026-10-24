"""Envía variables privadas por stdin a Vercel; nunca por argumentos o Git."""
import argparse
import json
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VARIABLES=['DATABASE_URL','DATABASE_SCHEMA','SECRET_KEY','PHOTO_STORAGE','SUPABASE_URL','SUPABASE_SECRET_KEY','SUPABASE_STORAGE_BUCKET','PROJECT_STAGE','COOKIE_SECURE','CLOUD_PROVIDER','CRON_SECRET']

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'instance/cloud-private.json');parser.add_argument('--environment',choices=['production','preview'],default='production');args=parser.parse_args()
    config=json.loads(args.config.read_text(encoding='utf-8'))
    key_file=ROOT/'instance/supabase-secret.txt'
    if not config.get('SUPABASE_SECRET_KEY') and key_file.exists():config['SUPABASE_SECRET_KEY']=key_file.read_text(encoding='utf-8-sig').strip()
    for key in VARIABLES:
        if not str(config.get(key,'')).strip():raise ValueError('Falta '+key+' en el archivo privado de configuración.')
    for key in VARIABLES:
        cli='npx.cmd' if os.name=='nt' else 'npx'
        subprocess.run([cli,'--yes','vercel@65.2.0','env','add',key,'--environment',args.environment,'--sensitive','--force','--yes'],input=str(config[key]),text=True,cwd=ROOT,check=True)
        print('Variable privada configurada: '+key)
