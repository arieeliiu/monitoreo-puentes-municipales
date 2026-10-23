"""Cliente pull del proveedor. Sin dependencia de un proveedor real."""
import json, time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def fetch_measurements(url, token='', attempts=3, timeout=3, delay=0.2):
    if not url.startswith(('http://','https://')):
        raise ValueError('Configura una URL HTTP(S) del proveedor.')
    for attempt in range(attempts):
        try:
            headers={'Accept':'application/json'}
            if token: headers['Authorization']='Bearer '+token
            with urlopen(Request(url,headers=headers),timeout=timeout) as response:
                raw=response.read(2_000_001)
            if len(raw)>2_000_000: raise ValueError('Respuesta del proveedor demasiado grande.')
            data=json.loads(raw)
            if not isinstance(data,dict) or not isinstance(data.get('measurements'),list) or len(data['measurements'])>1000:
                raise ValueError('Formato del proveedor inválido: se espera measurements (hasta 1000).')
            return data['measurements']
        except HTTPError as error:
            error.close()
            if error.code<500 and error.code!=429:
                raise ValueError(f'Proveedor rechazó la consulta: HTTP {error.code}.') from error
            last=error
        except (URLError,TimeoutError,OSError) as error: last=error
        except (ValueError,UnicodeError) as error: raise ValueError('Respuesta JSON inválida del proveedor.') from error
        if attempt+1<attempts: time.sleep(delay*(2**attempt))
    raise ValueError(f'No fue posible conectar con el proveedor tras {attempts} intentos: {type(last).__name__}.')
