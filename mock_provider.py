"""API ficticia independiente: python mock_provider.py --port 5100."""
import argparse, json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def demo_records():
    stamp=datetime.now(timezone.utc).isoformat()
    return [dict(external_id=f'academico-{stamp}-{bridge}-{kind}',bridge_code=f'DEM-0{bridge}',kind=kind,sensor_code=f'DEM-0{bridge}-{kind.upper()}',
                 value=value,unit=unit,measured_at=stamp,status='valido',simulated=True)
            for bridge in (1,2) for kind,unit,value in [('vibracion','mm/s',7),('inclinacion','°',-3)]]

def make_server(host='127.0.0.1',port=5100,records=None):
    batch=demo_records() if records is None else records
    class Provider(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path!='/measurements': self.send_error(404); return
            body=json.dumps(dict(simulated=True,measurements=batch)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def log_message(self,*args): pass
    return ThreadingHTTPServer((host,port),Provider)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=5100);args=parser.parse_args()
    server=make_server(port=args.port)
    print(f'Proveedor FICTICIO en http://127.0.0.1:{args.port}/measurements. Lote estable hasta reiniciar.')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
