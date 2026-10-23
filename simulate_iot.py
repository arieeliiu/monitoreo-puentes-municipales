"""Envío manual de prueba al adaptador API local; nunca programa capturas reales."""
import argparse, json, os, urllib.request
from datetime import datetime, timezone
from uuid import uuid4
p=argparse.ArgumentParser();p.add_argument('--sensor',required=True);p.add_argument('--value',type=float,required=True);p.add_argument('--unit',required=True);p.add_argument('--url',default='http://127.0.0.1:5000');a=p.parse_args()
key=os.environ.get('IOT_API_KEY')
if not key: p.error('Configura IOT_API_KEY en el servidor y en esta terminal.')
data=dict(external_id='sim-'+uuid4().hex,sensor_code=a.sensor,value=a.value,unit=a.unit,status='valido',measured_at=datetime.now(timezone.utc).isoformat(),simulated=True)
r=urllib.request.Request(a.url+'/api/v1/measurements',data=json.dumps(data).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
with urllib.request.urlopen(r) as response: print('PRUEBA SIMULADA:',response.read().decode())
