"""Presentación chilena y límites de días locales; nunca modifica registros."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CHILE = ZoneInfo('America/Santiago')


def chile_datetime(value):
    if value is None or value == '':
        return 'No disponible'
    try:
        instant = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if instant.tzinfo is None or instant.utcoffset() is None:
            return str(value) + ' (zona horaria no registrada)'
        local = instant.astimezone(CHILE)
        offset = local.strftime('%z')
        return local.strftime('%d/%m/%Y %H:%M:%S') + ' (UTC' + offset[:3] + ':' + offset[3:] + ')'
    except (ValueError, TypeError, OverflowError):
        return str(value) + ' (fecha no interpretable)'


def calendar_date(value):
    # Las fechas planificadas no son instantes: no se desplazan de día.
    try:
        return date.fromisoformat(str(value)).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return str(value or 'No disponible')


def day_start_utc(day):
    wall = datetime.combine(day, time.min)
    # En el salto de primavera, 00:00 no existe: usar el primer instante
    # válido del día. En un solapamiento elegir la primera ocurrencia.
    candidates = []
    for fold in (0, 1):
        instant = wall.replace(tzinfo=CHILE, fold=fold).astimezone(timezone.utc)
        if instant.astimezone(CHILE).replace(tzinfo=None) >= wall:
            candidates.append(instant)
    return min(candidates)


def local_date_bounds(start='', end=''):
    try:
        days = [date.fromisoformat(value) if value else None for value in (start, end)]
        if any(day and day.isoformat() != value for day, value in zip(days, (start, end))):
            raise ValueError()
        if all(days) and days[0] > days[1]:
            raise ValueError('Desde no puede ser posterior a Hasta.')
        lower = day_start_utc(days[0]) if days[0] else None
        upper = day_start_utc(days[1] + timedelta(days=1)) if days[1] else None
        return tuple(value.isoformat(timespec='seconds') if value else None for value in (lower, upper))
    except (ValueError, TypeError, OverflowError) as error:
        raise ValueError(str(error) if str(error) == 'Desde no puede ser posterior a Hasta.' else 'Usa fechas válidas en formato AAAA-MM-DD dentro del rango admitido.') from None
