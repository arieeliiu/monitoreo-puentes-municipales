"""Fotos privadas: misma ruta Flask autenticada, disco o Supabase Storage."""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class PhotoStorageError(ValueError): pass


class PhotoStorage:
    def __init__(self, config):
        self.remote = config.get('PHOTO_STORAGE') == 'supabase'
        self.folder = Path(config['UPLOAD_FOLDER'])
        self.base = config.get('SUPABASE_URL', '').rstrip('/')
        self.key = config.get('SUPABASE_SECRET_KEY', '')
        self.bucket = config.get('SUPABASE_STORAGE_BUCKET', 'puentes-fotos')
        if self.remote and (not self.base.startswith('https://') or not self.key):
            raise ValueError('Faltan SUPABASE_URL y SUPABASE_SECRET_KEY para las fotos privadas.')

    def request(self, method, path, body=None, content_type='application/json'):
        headers = {'apikey': self.key, 'Content-Type': content_type}
        if self.key.startswith('eyJ'): headers['Authorization'] = 'Bearer ' + self.key
        try:
            with urlopen(Request(self.base+'/storage/v1/'+path, data=body, headers=headers, method=method), timeout=15) as response:
                data=response.read(20*1024*1024+1)
                if len(data)>20*1024*1024: raise PhotoStorageError('La fotografía supera el límite de 20 MB.')
                return data
        except HTTPError as error:
            status = error.code; error.close()
            raise PhotoStorageError(f'No fue posible acceder a la fotografía (Storage HTTP {status}).') from None
        except (URLError, OSError):
            raise PhotoStorageError('Storage no disponible. Intenta nuevamente.') from None

    def object_path(self, filename):
        if Path(filename).name != filename or '/' in filename or '\\' in filename: raise PhotoStorageError('Nombre de fotografía inválido.')
        return 'object/'+quote(self.bucket, safe='')+'/'+quote(filename, safe='')

    def put(self, filename, data):
        if self.remote: self.request('POST', self.object_path(filename), data, 'image/jpeg')
        else:
            self.folder.mkdir(parents=True, exist_ok=True)
            (self.folder/filename).write_bytes(data)

    def get(self, filename):
        if self.remote: return self.request('GET', self.object_path(filename))
        return (self.folder/filename).read_bytes()

    def delete(self, filename):
        if self.remote:
            self.request('DELETE', 'object/'+quote(self.bucket, safe=''), json.dumps({'prefixes':[filename]}).encode())
        else: (self.folder/filename).unlink(missing_ok=True)

    def signed_download(self, filename):
        path=self.object_path(filename).replace('object/','object/sign/',1)
        result=json.loads(self.request('POST',path,json.dumps({'expiresIn':60}).encode()))
        return self.base+'/storage/v1'+result['signedURL']

    def signed_upload(self, filename):
        bucket=self.bucket+'-staging'
        result=json.loads(self.request('POST','object/upload/sign/'+quote(bucket)+'/'+quote(filename),b'{}'))
        return self.base+'/storage/v1'+result['url']

    def staged(self, filename):
        return self.request('GET','object/'+quote(self.bucket+'-staging')+'/'+quote(filename))

    def delete_staged(self, names):
        if names:self.request('DELETE','object/'+quote(self.bucket+'-staging'),json.dumps({'prefixes':names}).encode())

    def cleanup_staged(self):
        from datetime import datetime,timezone,timedelta
        entries=json.loads(self.request('POST','object/list/'+quote(self.bucket+'-staging'),json.dumps({'prefix':'','limit':100,'sortBy':{'column':'created_at','order':'asc'}}).encode()))
        cutoff=datetime.now(timezone.utc)-timedelta(hours=4)
        expired=[e['name'] for e in entries if e.get('created_at') and datetime.fromisoformat(e['created_at'].replace('Z','+00:00'))<cutoff]
        self.delete_staged(expired)
