"""Worker periódico independiente del servidor web, sin hilos por petición."""
import math
from contextlib import contextmanager
from pathlib import Path
from threading import Event
import os

def interval_seconds(value):
    try: value=float(value)
    except (TypeError,ValueError): raise ValueError('El intervalo IoT debe ser numérico.')
    if not math.isfinite(value) or not 1 <= value <= 86400:
        raise ValueError('El intervalo IoT debe estar entre 1 y 86400 segundos.')
    return value

def run_polling(poll, interval=60, stop=None, on_error=None):
    """Primera consulta inmediata; espera configurable después de cada ciclo.

    Las esperas son interrumpibles. Un error de un ciclo no detiene el siguiente.
    Los reintentos de conexión acotados pertenecen al cliente HTTP.
    """
    interval=interval_seconds(interval)
    stop=stop if stop is not None else Event()
    while not stop.is_set():
        try: poll()
        except Exception as error:
            if on_error: on_error(error)
        if stop.wait(interval): break

@contextmanager
def single_worker(database):
    """Bloqueo de SO: un worker por base; se libera incluso si muere el proceso."""
    path=Path(str(database)+'.poll.lock');path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+b') as lock:
        lock.seek(0,2)
        if lock.tell()==0: lock.write(b'0');lock.flush()
        lock.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as error: raise ValueError('Ya existe un worker IoT activo para esta base.') from error
        try: yield
        finally:
            lock.seek(0)
            if os.name=='nt': msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
