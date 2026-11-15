"""Identificadores de referencia compartidos por carga inicial y proveedores.

Las mediciones provienen del proveedor de referencia; el alcance no incluye sensores físicos (SC-01).
"""

BRIDGE_REFERENCES = (
    ('PM-001', 'Puente Estero Norte', 'Sector municipal · Biobío'),
    ('PM-002', 'Puente Ribera Sur', 'Sector municipal · Biobío'),
)


def reference_inventory(connection, references=BRIDGE_REFERENCES, strict=True):
    """Verifica firma e identidad relacional; nunca autoriza por código aislado."""
    result=[]
    for code,name,location in references:
        bridge=connection.execute('SELECT * FROM bridges WHERE code=?',(code,)).fetchone()
        if bridge is None:
            if strict: raise ValueError('Inventario de referencia incompleto: '+code)
            continue
        if bridge['name']!=name or bridge['location']!=location:
            raise ValueError('Inventario personalizado: requiere revisión manual de '+code)
        sensors=connection.execute('SELECT s.code,s.kind,s.unit,c.bridge_id,c.name AS component FROM sensors s JOIN components c ON c.id=s.component_id WHERE c.bridge_id=?',(bridge['id'],)).fetchall()
        expected={(code+'-VIBRACION','vibracion','m/s²'),(code+'-INCLINACION','inclinacion','°')}
        if {(s['code'],s['kind'],s['unit']) for s in sensors}!=expected or len(sensors)!=2:
            raise ValueError('Sensores no canónicos o inventario parcial: '+code)
        if any(s['component'] not in ('Tablero','Viga','Estribo') for s in sensors):
            raise ValueError('Asociación de componente no esperada: '+code)
        result.append(bridge)
    return result
