"""Fechas de formularios del piloto; API/IoT conservan su contrato ISO."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def form_timestamp(data, prefix, legacy):
    if prefix+'_date' not in data and prefix+'_time' not in data:
        return legacy(data.get(prefix+'_at'))
    day, clock = data.get(prefix+'_date',''), data.get(prefix+'_time','')
    if not day or not clock:
        raise ValueError('Completa la fecha y la hora (America/Santiago).')
    try:
        import re
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',day) or not re.fullmatch(r'\d{2}:\d{2}(:\d{2})?',clock):raise ValueError()
        local=datetime.fromisoformat(day+'T'+clock)
    except (ValueError,TypeError):
        raise ValueError('Fecha u hora inválida. Revisa el calendario y usa una hora de 00:00 a 23:59.') from None
    zone=ZoneInfo('America/Santiago')
    candidates=set()
    for fold in (0,1):
        try:utc=local.replace(tzinfo=zone,fold=fold).astimezone(timezone.utc)
        except (OverflowError,ValueError):raise ValueError('Fecha fuera del rango admitido. Selecciona una fecha válida no futura.') from None
        if utc.astimezone(zone).replace(tzinfo=None)==local:candidates.add(utc)
    if not candidates:raise ValueError('Esa hora no existe por el cambio de horario en Chile. Selecciona otra hora.')
    if len(candidates)>1:raise ValueError('Esa hora es ambigua por el cambio de horario en Chile. Selecciona una hora fuera del cambio.')
    utc=candidates.pop()
    if utc>datetime.now(timezone.utc):raise ValueError('Fecha y hora futuras. Selecciona un momento anterior o igual al actual en America/Santiago.')
    return legacy(utc.isoformat())
