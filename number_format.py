"""Presentación de números con coma decimal (es-CL). Solo para mostrar: no se usa en formularios ni API.

Los campos <input type="number"> y el contrato JSON siguen con punto decimal, como exige el navegador y la API.
"""


def decimal(value, places=6):
    """2.5 -> '2,5'; 0.115 -> '0,115'; 3.0 -> '3'. Sin redondeo visible hasta `places` decimales."""
    if value is None or value == '':
        return value
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value
    text = f'{number:.{places}f}'.rstrip('0').rstrip('.')
    if text in ('-0', ''):
        text = '0'
    return text.replace('.', ',')
