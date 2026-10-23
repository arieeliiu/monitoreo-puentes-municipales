import os, secrets, sqlite3, math, hmac, json
from decimal import Decimal
from datetime import datetime, timezone, date
from functools import wraps
from pathlib import Path
from uuid import uuid4
import click
from migrations import migrate
from provider_client import fetch_measurements
from polling import run_polling, interval_seconds, single_worker
from flask import Flask, g, session, request, redirect, url_for, render_template, flash, abort, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image, UnidentifiedImageError

KINDS = {'vibracion': 'm/s²', 'inclinacion': '°'}
CONDITIONS = ['Baja','Media','Alta','Crítica']
SEVERITIES = ['Atención','Alerta','Crítico']
LABELS = {'vibracion':'Aceleración vertical pico','inclinacion':'Inclinación','visual':'Condición visual'}
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    key_file = Path(app.instance_path) / 'session.key'
    if not key_file.exists(): key_file.write_text(secrets.token_hex(32))
    app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY') or key_file.read_text(), DATABASE=str(Path(app.instance_path)/'puentes.sqlite'), UPLOAD_FOLDER=str(Path(app.instance_path)/'photos'), MAX_CONTENT_LENGTH=20*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE')=='1', IOT_API_KEY=os.environ.get('IOT_API_KEY'), DEMO_ENABLED=False, PROVIDER_URL=os.environ.get('PROVIDER_URL','http://127.0.0.1:5100/measurements'), PROVIDER_TOKEN=os.environ.get('PROVIDER_TOKEN',''))
    if config: app.config.update(config)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g:
            g.db=sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory=sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
            migrate(g.db)
        return g.db
    def rows(sql,args=()): return db().execute(sql,args).fetchall()
    def one(sql,args=()): return db().execute(sql,args).fetchone()
    def insert(table, **values):
        keys=','.join(values); marks=','.join('?' for _ in values)
        return db().execute(f'INSERT INTO {table} ({keys}) VALUES ({marks})',tuple(values.values())).lastrowid
    def audit(action,entity,entity_id,details=''):
        insert('audit',author=g.user['username'] if g.get('user') else 'API IoT',action=action,entity=entity,entity_id=entity_id,details=details,created_at=now())
    def required(data,*fields):
        for field in fields:
            value=data.get(field)
            if not isinstance(value,str) or not value.strip(): raise ValueError(f'El campo {field} es obligatorio y debe ser texto.')
            if len(value)>4000: raise ValueError(f'El campo {field} supera los 4000 caracteres.')
    def get_id(table,value):
        try: record=one(f'SELECT * FROM {table} WHERE id=?',(int(value),))
        except (TypeError,ValueError): record=None
        if not record: raise ValueError(f'El registro de {table} no existe.')
        return record
    def belongs(component_id,bridge_id):
        c=get_id('components',component_id)
        if c['bridge_id']!=int(bridge_id): raise ValueError('El componente no pertenece al puente seleccionado.')
        return c
    def timestamp(value):
        try:
            dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
            if dt.tzinfo is None: raise ValueError()
            dt=dt.astimezone(timezone.utc)
            if dt>datetime.now(timezone.utc): raise ValueError()
            return dt.isoformat(timespec='seconds')
        except (ValueError,TypeError): raise ValueError('Fecha inválida o futura. Indica fecha y hora con zona horaria.')
    def access(*roles):
        def decorator(fn):
            @wraps(fn)
            def inner(*args,**kwargs):
                if not g.user: return redirect(url_for('login',next=request.path))
                if roles and g.user['role'] not in roles: abort(403)
                return fn(*args,**kwargs)
            return inner
        return decorator

    @app.teardown_appcontext
    def close(error):
        connection=g.pop('db',None)
        if connection: connection.close()
    @app.before_request
    def prepare():
        g.user=one('SELECT * FROM users WHERE id=?',(session['user_id'],)) if session.get('user_id') else None
        if 'csrf' not in session: session['csrf']=secrets.token_hex(32)
        if request.method=='POST' and request.endpoint!='iot':
            if not hmac.compare_digest(str(session['csrf']),str(request.form.get('csrf',''))): abort(400, 'La sesión del formulario venció. Recarga la página.')
    @app.after_request
    def security(response):
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        response.headers['Cache-Control']='no-store'
        return response
    @app.context_processor
    def context(): return dict(user=g.get('user'), csrf=session.get('csrf'), kinds=KINDS, conditions=CONDITIONS, severities=SEVERITIES, labels=LABELS)
    @app.errorhandler(403)
    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error(e): return render_template('error.html',error=e),e.code

    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            u=one('SELECT * FROM users WHERE username=?',(request.form.get('username',''),))
            if u and check_password_hash(u['password'],request.form.get('password','')):
                session.clear(); session['user_id']=u['id']; session['csrf']=secrets.token_hex(32)
                g.user=u; audit('Inicio de sesión','users',u['id']); db().commit()
                return redirect(url_for('dashboard'))
            flash('Usuario o contraseña incorrectos.','error')
        return render_template('login.html')
    @app.post('/logout')
    @access()
    def logout(): session.clear(); return redirect(url_for('login'))

    @app.get('/')
    @access()
    def dashboard():
        bridges=rows('SELECT b.*, (SELECT count(*) FROM alerts a WHERE a.bridge_id=b.id AND a.status!=\'Resuelta\') AS active FROM bridges b ORDER BY b.code')
        latest=rows('SELECT m.*, s.code,s.kind,c.bridge_id FROM sensors s JOIN components c ON c.id=s.component_id LEFT JOIN measurements m ON m.id=(SELECT id FROM measurements WHERE sensor_id=s.id ORDER BY measured_at DESC,id DESC LIMIT 1) ORDER BY s.code')
        active=rows('SELECT a.*,b.name,r.label FROM alerts a JOIN bridges b ON b.id=a.bridge_id JOIN rules r ON r.id=a.rule_id WHERE a.status!=\'Resuelta\' ORDER BY a.id DESC LIMIT 10')
        rules=one("SELECT count(*) AS n FROM rules WHERE active=1 AND standard='EV2'")['n']
        pending=rows("SELECT t.*,b.name FROM tasks t JOIN bridges b ON b.id=t.bridge_id WHERE t.status!='Completada'"+(' AND t.assignee_id=?' if g.user['role']=='Mantención' else '')+' ORDER BY planned_date', (g.user['id'],) if g.user['role']=='Mantención' else ())
        plans=rows("SELECT p.*,b.name,u.username FROM inspection_plans p JOIN bridges b ON b.id=p.bridge_id JOIN users u ON u.id=p.inspector_id WHERE p.status='Programada' ORDER BY planned_date")
        visual=rows('SELECT i.*,b.name,c.name AS component FROM inspections i JOIN bridges b ON b.id=i.bridge_id JOIN components c ON c.id=i.component_id WHERE i.id=(SELECT id FROM inspections WHERE bridge_id=b.id ORDER BY inspected_at DESC,id DESC LIMIT 1)')
        return render_template('dashboard.html',bridges=bridges,latest=latest,alerts=active,rule_count=rules,pending=pending,plans=plans,visual=visual)

    @app.route('/bridges',methods=['GET','POST'])
    @access()
    def bridges():
        if request.method=='POST':
            if g.user['role']!='DOM': abort(403)
            try:
                required(request.form,'code','name','location','criticality')
                if request.form['criticality'] not in ['Baja','Media','Alta']: raise ValueError('Criticidad inválida.')
                values={k:request.form[k].strip() for k in ('code','name','location','criticality')}
                values['code']=values['code'].upper()
                if request.form.get('id'):
                    bid=get_id('bridges',request.form['id'])['id']
                    db().execute('UPDATE bridges SET code=?,name=?,location=?,criticality=? WHERE id=?',(*values.values(),bid))
                    action='Editar puente'
                else: bid=insert('bridges',**values); action='Registrar puente'
                audit(action,'bridges',bid); db().commit(); flash('Puente guardado.','success')
                return redirect(url_for('bridge',bid=bid))
            except (ValueError,sqlite3.IntegrityError) as e:
                db().rollback(); flash(str(e) if isinstance(e,ValueError) else 'El identificador ya existe. Usa uno único.','error')
        return render_template('bridges.html',bridges=rows('SELECT * FROM bridges ORDER BY code'))

    @app.route('/bridges/<int:bid>',methods=['GET','POST'])
    @access()
    def bridge(bid):
        b=one('SELECT * FROM bridges WHERE id=?',(bid,))
        if not b: abort(404)
        if request.method=='POST':
            if g.user['role']!='DOM': abort(403)
            try:
                if request.form.get('entity')=='component':
                    required(request.form,'name'); name=request.form['name'].strip()
                    if request.form.get('id'):
                        c=belongs(request.form['id'],bid)
                        db().execute('UPDATE components SET name=? WHERE id=?',(name,c['id'])); eid=c['id']
                    else: eid=insert('components',bridge_id=bid,name=name)
                    audit('Guardar componente','components',eid)
                else:
                    required(request.form,'code','component_id','kind','location')
                    belongs(request.form['component_id'],bid)
                    kind=request.form['kind']
                    if kind not in KINDS: raise ValueError('Tipo de sensor inválido.')
                    reference=None
                    if kind=='inclinacion' and request.form.get('reference_value','').strip():
                        try: reference=float(request.form['reference_value'])
                        except ValueError: raise ValueError('La referencia debe ser numérica.')
                        if not math.isfinite(reference): raise ValueError('La referencia debe ser finita.')
                    code=request.form['code'].strip().upper()
                    if request.form.get('id'):
                        s=get_id('sensors',request.form['id']); belongs(s['component_id'],bid)
                        if one('SELECT id FROM measurements WHERE sensor_id=?',(s['id'],)) and (s['kind']!=kind or s['component_id']!=int(request.form['component_id'])): raise ValueError('Un sensor con mediciones no puede cambiar de tipo ni componente.')
                        db().execute('UPDATE sensors SET code=?,component_id=?,kind=?,unit=?,location=?,reference_value=? WHERE id=?',(code,request.form['component_id'],kind,KINDS[kind],request.form['location'].strip(),reference,s['id'])); eid=s['id']
                    else: eid=insert('sensors',component_id=request.form['component_id'],code=code,kind=kind,unit=KINDS[kind],location=request.form['location'].strip(),reference_value=reference)
                    audit('Guardar sensor','sensors',eid)
                db().commit(); flash('Registro guardado.','success'); return redirect(url_for('bridge',bid=bid))
            except (ValueError,sqlite3.IntegrityError) as e:
                db().rollback(); flash(str(e) if isinstance(e,ValueError) else 'El nombre o código está duplicado.','error')
        return render_template('bridge.html',b=b,components=rows('SELECT * FROM components WHERE bridge_id=?',(bid,)),sensors=rows('SELECT s.*,c.name AS component FROM sensors s JOIN components c ON c.id=s.component_id WHERE c.bridge_id=?',(bid,)))

    def evaluate(kind,bridge_id,record_id,value,simulated):
        applicable=rows("SELECT * FROM rules WHERE bridge_id=? AND kind=? AND active=1 AND standard='EV2'",(bridge_id,kind))
        matches=[r for r in applicable if (kind=='visual' and value==r['condition']) or (kind!='visual' and r['unit']==KINDS[kind] and value>=r['threshold'])]
        if matches:
            r=max(matches,key=lambda rule:(SEVERITIES.index(rule['severity']),rule['id']))
            aid=insert('alerts',bridge_id=bridge_id,rule_id=r['id'],measurement_id=record_id if kind!='visual' else None,inspection_id=record_id if kind=='visual' else None,created_at=now(),simulated=int(bool(simulated or r['simulated'])),severity=r['severity'],standard='EV2')
            audit('Generar alerta','alerts',aid,r['severity'])
        return bool(applicable)

    def validate_identity(data, provider=False):
        required(data,'sensor_code')
        sensor=one('SELECT s.*,b.code AS bridge_code FROM sensors s JOIN components c ON c.id=s.component_id JOIN bridges b ON b.id=c.bridge_id WHERE s.code=?',(data['sensor_code'],))
        if not sensor: raise ValueError('Sensor desconocido.')
        if provider or 'bridge_code' in data or 'kind' in data:
            required(data,'bridge_code','kind')
            if data['bridge_code']!=sensor['bridge_code']: raise ValueError('El identificador del puente no coincide con el sensor registrado.')
            if data['kind']!=sensor['kind']: raise ValueError('El tipo de medición no coincide con la variable del sensor registrado.')

    def receive(data,simulated=False):
        validate_identity(data)
        required(data,'sensor_code','unit','measured_at','status')
        if data.get('external_id') is not None and (not isinstance(data['external_id'],str) or len(data['external_id'])>200): raise ValueError('external_id debe ser texto de hasta 200 caracteres.')
        s=one('SELECT s.*,c.bridge_id FROM sensors s JOIN components c ON c.id=s.component_id WHERE s.code=?',(data['sensor_code'],))
        if not s: raise ValueError('Sensor desconocido.')
        if data['unit']!=KINDS[s['kind']]: raise ValueError(f'Unidad incorrecta. Se espera {KINDS[s["kind"]]}.')
        status=data['status']
        if status not in ['valido','invalido','no_disponible']: raise ValueError('Estado de medición inválido.')
        value=data.get('value')
        if value in ('',None):
            value=None
            if status=='valido': raise ValueError('Una medición válida requiere un valor.')
        else:
            if isinstance(value,bool): raise ValueError('El valor debe ser numérico, no booleano.')
            try: value=float(value)
            except (ValueError,TypeError): raise ValueError('El valor debe ser numérico.')
            if not math.isfinite(value): raise ValueError('El valor debe ser finito.')
            if status=='valido' and s['kind']=='vibracion' and value<0: raise ValueError('La vibración no puede ser negativa.')
        measured_at=timestamp(data['measured_at'])
        reference=s['reference_value'] if s['kind']=='inclinacion' else None
        variation=float(abs(Decimal(str(value))-Decimal(str(reference)))) if value is not None and reference is not None else None
        if variation is not None and not math.isfinite(variation): raise ValueError('La variación calculada debe ser finita.')
        mid=insert('measurements',specification='EV2',reference_value=reference,variation=variation,sensor_id=s['id'],value=value,unit=KINDS[s['kind']],measured_at=measured_at,status=status,simulated=int(simulated),external_id=data.get('external_id') or None,author_id=g.user['id'] if g.get('user') else None,created_at=now())
        applicable=bool(one("SELECT id FROM rules WHERE bridge_id=? AND kind=? AND active=1 AND standard='EV2'",(s['bridge_id'],s['kind'])))
        if status=='valido' and (s['kind']!='inclinacion' or reference is not None): evaluate(s['kind'],s['bridge_id'],mid,variation if s['kind']=='inclinacion' else value,simulated)
        evaluation=('Evaluada' if status=='valido' else 'No evaluada: dato '+status) if applicable else 'Sin regla aplicable'
        if s['kind']=='inclinacion' and reference is None: evaluation='Falta referencia del sensor: medición no evaluable'
        db().execute('UPDATE measurements SET evaluation=? WHERE id=?',(evaluation,mid))
        if not applicable: audit('Sin regla aplicable','measurements',mid,s['kind'])
        audit('Recibir medición simulada' if simulated else 'Recibir medición','measurements',mid)
        return mid

    @app.route('/measurements',methods=['GET','POST'])
    @access()
    def measurements():
        if request.method=='POST':
            if g.user['role']!='DOM': abort(403)
            try:
                mid=receive(request.form,True); db().commit(); flash(f'Medición {mid} guardada. '+one('SELECT evaluation FROM measurements WHERE id=?',(mid,))['evaluation'],'success')
                return redirect(url_for('measurements'))
            except (ValueError,sqlite3.IntegrityError) as e:
                db().rollback(); flash(str(e) if isinstance(e,ValueError) else 'El identificador externo ya se recibió.','error')
        filters=[]; args=[]
        for field,column in [('bridge_id','c.bridge_id'),('sensor_id','s.id')]:
            if request.args.get(field): filters.append(column+'=?'); args.append(request.args[field])
        for field,op in [('from','>='),('to','<=')]:
            if request.args.get(field): filters.append(f'substr(m.measured_at,1,10){op}?'); args.append(request.args[field])
        where=' WHERE '+' AND '.join(filters) if filters else ''
        data=rows('SELECT m.*,s.code,s.kind,b.name FROM measurements m JOIN sensors s ON s.id=m.sensor_id JOIN components c ON c.id=s.component_id JOIN bridges b ON b.id=c.bridge_id'+where+' ORDER BY m.measured_at DESC,m.id DESC LIMIT 500',args)
        return render_template('measurements.html',measurements=data,sensors=rows('SELECT s.*,b.name FROM sensors s JOIN components c ON c.id=s.component_id JOIN bridges b ON b.id=c.bridge_id'),bridges=rows('SELECT * FROM bridges'))

    @app.post('/api/v1/measurements')
    def iot():
        key=app.config.get('IOT_API_KEY')
        if not key: return jsonify(error='El acceso de recepción no está configurado.'),503
        if not hmac.compare_digest(request.headers.get('Authorization',''),'Bearer '+key): return jsonify(error='No autorizado'),401
        data=request.get_json(silent=True)
        if not isinstance(data,dict): return jsonify(error='Se requiere un objeto JSON.'),400
        try:
            required(data,'external_id')
            if not isinstance(data.get('simulated',False),bool): raise ValueError('simulated debe ser booleano.')
            mid=receive(data,data.get('simulated',False)); db().commit(); return jsonify(id=mid,evaluation=one('SELECT evaluation FROM measurements WHERE id=?',(mid,))['evaluation']),201
        except (ValueError,sqlite3.IntegrityError) as e:
            db().rollback(); return jsonify(error=str(e) if isinstance(e,ValueError) else 'external_id duplicado.'),400

    @app.get('/measurements/<int:mid>')
    @access()
    def measurement(mid):
        m=one('SELECT m.*,s.code,s.kind,b.name,c.name AS component FROM measurements m JOIN sensors s ON s.id=m.sensor_id JOIN components c ON c.id=s.component_id JOIN bridges b ON b.id=c.bridge_id WHERE m.id=?',(mid,))
        if not m: abort(404)
        return render_template('measurement.html',m=m)

    @app.route('/inspections',methods=['GET','POST'])
    @access()
    def inspections():
        if request.method=='POST':
            if g.user['role'] not in ['DOM','Inspector']: abort(403)
            saved=[]
            try:
                required(request.form,'bridge_id','component_id','inspected_at','condition','description')
                belongs(request.form['component_id'],request.form['bridge_id'])
                if request.form['condition'] not in CONDITIONS: raise ValueError('Condición inválida.')
                files=[f for f in request.files.getlist('photos') if f.filename]
                if len(files)>5: raise ValueError('Adjunta hasta 5 fotografías por inspección.')
                images=[]
                for f in files:
                    try:
                        image=Image.open(f.stream)
                        if image.format not in ['JPEG','PNG'] or image.width*image.height>20_000_000: raise ValueError('Usa fotografías JPEG o PNG de hasta 20 megapíxeles.')
                        image.load(); images.append(image.convert('RGB'))
                    except (UnidentifiedImageError,OSError,Image.DecompressionBombError): raise ValueError('El archivo no es una fotografía JPEG o PNG válida.')
                iid=insert('inspections',bridge_id=request.form['bridge_id'],component_id=request.form['component_id'],inspected_at=timestamp(request.form['inspected_at']),inspector_id=g.user['id'],condition=request.form['condition'],standard='EV2',description=request.form['description'].strip(),simulated=int(request.form.get('simulated')=='1'))
                if request.form.get('plan_id'):
                    plan=get_id('inspection_plans',request.form['plan_id'])
                    if g.user['role']!='Inspector' or plan['inspector_id']!=g.user['id']: abort(403)
                    if plan['status']!='Programada' or plan['bridge_id']!=int(request.form['bridge_id']) or plan['component_id']!=int(request.form['component_id']): raise ValueError('La programación no corresponde al puente/componente o ya fue atendida.')
                    db().execute("UPDATE inspection_plans SET status='Realizada',inspection_id=? WHERE id=?",(iid,plan['id']))
                    audit('Realizar inspección programada','inspection_plans',plan['id'])
                for image in images:
                    filename=uuid4().hex+'.jpg'; path=Path(app.config['UPLOAD_FOLDER'])/filename
                    saved.append(path); image.save(path,'JPEG',quality=88)
                    insert('photos',inspection_id=iid,filename=filename)
                evaluate('visual',int(request.form['bridge_id']),iid,request.form['condition'],request.form.get('simulated')=='1')
                audit('Registrar inspección','inspections',iid); db().commit()
                return redirect(url_for('inspection',iid=iid))
            except (ValueError,sqlite3.IntegrityError) as e:
                db().rollback()
                for path in saved: path.unlink(missing_ok=True)
                flash(str(e) if isinstance(e,ValueError) else 'No fue posible guardar: revisa los registros asociados.','error')
        query='SELECT i.*,b.name,c.name AS component,u.username FROM inspections i JOIN bridges b ON b.id=i.bridge_id JOIN components c ON c.id=i.component_id JOIN users u ON u.id=i.inspector_id'
        args=()
        if request.args.get('bridge_id'): query+=' WHERE i.bridge_id=?'; args=(request.args['bridge_id'],)
        return render_template('inspections.html',inspections=rows(query+' ORDER BY inspected_at DESC',args),bridges=rows('SELECT * FROM bridges'),plans=rows("SELECT * FROM inspection_plans WHERE status='Programada' AND inspector_id=?",(g.user['id'],)),components=rows('SELECT c.*,b.name AS bridge FROM components c JOIN bridges b ON b.id=c.bridge_id'))
    @app.get('/inspections/<int:iid>')
    @access()
    def inspection(iid):
        i=one('SELECT i.*,b.name,c.name AS component,u.username FROM inspections i JOIN bridges b ON b.id=i.bridge_id JOIN components c ON c.id=i.component_id JOIN users u ON u.id=i.inspector_id WHERE i.id=?',(iid,))
        if not i: abort(404)
        return render_template('inspection.html',i=i,photos=rows('SELECT * FROM photos WHERE inspection_id=?',(iid,)))
    @app.get('/photos/<filename>')
    @access()
    def photo(filename):
        if not one('SELECT id FROM photos WHERE filename=?',(filename,)): abort(404)
        return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

    @app.route('/rules',methods=['GET','POST'])
    @access('DOM')
    def rules():
        if request.method=='POST':
            try:
                if request.form.get('disable'):
                    rid=get_id('rules',request.form['disable'])['id']; db().execute('UPDATE rules SET active=0 WHERE id=?',(rid,)); audit('Desactivar regla','rules',rid)
                else:
                    required(request.form,'bridge_id','kind','label'); get_id('bridges',request.form['bridge_id'])
                    kind=request.form['kind']; threshold=None; condition=None
                    if kind=='visual':
                        condition=request.form.get('condition')
                        if condition not in CONDITIONS: raise ValueError('Condición visual inválida.')
                    elif kind in KINDS:
                        try: threshold=float(request.form.get('threshold',''))
                        except ValueError: raise ValueError('Indica un umbral numérico.')
                        if not math.isfinite(threshold): raise ValueError('El umbral debe ser finito.')
                    else: raise ValueError('Tipo de regla inválido.')
                    if kind=='vibracion' and threshold<0: raise ValueError('El umbral de vibración no puede ser negativo.')
                    severity=request.form.get('severity')
                    if severity not in SEVERITIES: raise ValueError('Selecciona Atención, Alerta o Crítico.')
                    if kind!='visual' and threshold<0: raise ValueError('El umbral de vibración no puede ser negativo.' if kind=='vibracion' else 'El umbral de variación debe ser no negativo.')
                    if kind!='visual':
                        for other in rows("SELECT * FROM rules WHERE bridge_id=? AND kind=? AND active=1 AND standard='EV2' AND severity!=?",(request.form['bridge_id'],kind,severity)):
                            if (SEVERITIES.index(other['severity'])<SEVERITIES.index(severity) and threshold<=other['threshold']) or (SEVERITIES.index(other['severity'])>SEVERITIES.index(severity) and threshold>=other['threshold']): raise ValueError('Los umbrales deben aumentar de Atención a Alerta y Crítico.')
                    # Version rules instead of changing the rule attached to past alerts.
                    db().execute("UPDATE rules SET active=0 WHERE bridge_id=? AND kind=? AND standard='EV2' AND active=1 AND "+('condition=?' if kind=='visual' else 'severity=?'),(request.form['bridge_id'],kind,condition if kind=='visual' else severity))
                    rid=insert('rules',bridge_id=request.form['bridge_id'],kind=kind,threshold=threshold,condition=condition,label=request.form['label'].strip(),simulated=1,comparison='gte',severity=severity,standard='EV2',unit=KINDS.get(kind),author_id=g.user['id'],created_at=now()); audit('Configurar regla','rules',rid)
                db().commit(); flash('Regla guardada. Se aplica a nuevos registros.','success'); return redirect(url_for('rules'))
            except (ValueError,sqlite3.IntegrityError) as e: db().rollback(); flash(str(e),'error')
        return render_template('rules.html',rules=rows('SELECT r.*,b.name FROM rules r JOIN bridges b ON b.id=r.bridge_id ORDER BY r.id DESC'),bridges=rows('SELECT * FROM bridges'))

    @app.get('/alerts')
    @access()
    def alerts():
        query='SELECT a.*,b.name,r.label FROM alerts a JOIN bridges b ON b.id=a.bridge_id JOIN rules r ON r.id=a.rule_id'
        args=[]; filters=[]
        for field in ['bridge_id','status']:
            if request.args.get(field): filters.append('a.'+field+'=?'); args.append(request.args[field])
        if filters: query+=' WHERE '+' AND '.join(filters)
        return render_template('alerts.html',alerts=rows(query+' ORDER BY a.id DESC',args),bridges=rows('SELECT * FROM bridges'))
    @app.route('/alerts/<int:aid>',methods=['GET','POST'])
    @access()
    def alert(aid):
        a=one('SELECT a.*,b.name,r.label FROM alerts a JOIN bridges b ON b.id=a.bridge_id JOIN rules r ON r.id=a.rule_id WHERE a.id=?',(aid,))
        if not a: abort(404)
        if request.method=='POST':
            if g.user['role'] not in ['DOM','Inspector']: abort(403)
            try:
                required(request.form,'note'); iid=request.form.get('inspection_id') or None
                if iid and get_id('inspections',iid)['bridge_id']!=a['bridge_id']: raise ValueError('La inspección debe ser del mismo puente.')
                status=request.form.get('status',a['status'])
                if status!=a['status'] and g.user['role']!='DOM': abort(403)
                if status not in ['Activa','En atención','Resuelta']: raise ValueError('Estado inválido.')
                insert('alert_notes',alert_id=aid,author_id=g.user['id'],created_at=now(),note=request.form['note'].strip(),inspection_id=iid)
                db().execute('UPDATE alerts SET status=? WHERE id=?',(status,aid)); audit('Seguimiento de alerta','alerts',aid,status+': '+request.form['note'].strip()); db().commit()
                return redirect(url_for('alert',aid=aid))
            except ValueError as e: db().rollback(); flash(str(e),'error')
        return render_template('alert.html',a=a,notes=rows('SELECT n.*,u.username FROM alert_notes n JOIN users u ON u.id=n.author_id WHERE alert_id=? ORDER BY n.id',(aid,)),inspections=rows('SELECT * FROM inspections WHERE bridge_id=?',(a['bridge_id'],)),related_inspection=bool(a['inspection_id'] or one('SELECT id FROM alert_notes WHERE alert_id=? AND inspection_id IS NOT NULL',(aid,))),tasks=rows('SELECT t.*,u.username FROM tasks t JOIN users u ON u.id=t.assignee_id WHERE alert_id=?',(aid,)))

    @app.route('/maintenance',methods=['GET','POST'])
    @access()
    def maintenance():
        if request.method=='POST':
            try:
                if request.form.get('id'):
                    t=get_id('tasks',request.form['id'])
                    if g.user['role']!='DOM' and not (g.user['role']=='Mantención' and t['assignee_id']==g.user['id']): abort(403)
                    status=request.form.get('status')
                    if status not in ['Pendiente','En ejecución','Completada']: raise ValueError('Estado inválido.')
                    if g.user['role']=='DOM':
                        required(request.form,'description','assignee_id','planned_date')
                        assignee=get_id('users',request.form['assignee_id'])
                        if assignee['role']!='Mantención': raise ValueError('Asigna a personal de mantención.')
                        date.fromisoformat(request.form['planned_date'])
                        db().execute('UPDATE tasks SET description=?,assignee_id=?,planned_date=?,status=? WHERE id=?',(request.form['description'].strip(),assignee['id'],request.form['planned_date'],status,t['id']))
                    else: db().execute('UPDATE tasks SET status=? WHERE id=?',(status,t['id']))
                    audit('Actualizar mantenimiento','tasks',t['id'],status)
                else:
                    if g.user['role']!='DOM': abort(403)
                    required(request.form,'bridge_id','description','assignee_id','planned_date')
                    get_id('bridges',request.form['bridge_id'])
                    cid=request.form.get('component_id') or None; aid=request.form.get('alert_id') or None
                    if cid: belongs(cid,request.form['bridge_id'])
                    if aid and get_id('alerts',aid)['bridge_id']!=int(request.form['bridge_id']): raise ValueError('La alerta debe ser del mismo puente.')
                    assignee=get_id('users',request.form['assignee_id'])
                    if assignee['role']!='Mantención': raise ValueError('Asigna a personal de mantención.')
                    date.fromisoformat(request.form['planned_date'])
                    tid=insert('tasks',bridge_id=request.form['bridge_id'],component_id=cid,alert_id=aid,description=request.form['description'].strip(),assignee_id=assignee['id'],planned_date=request.form['planned_date'],author_id=g.user['id'],created_at=now()); audit('Planificar mantenimiento','tasks',tid)
                db().commit(); flash('Actividad guardada. La alerta conserva su estado.','success'); return redirect(url_for('maintenance'))
            except (ValueError,sqlite3.IntegrityError) as e: db().rollback(); flash(str(e),'error')
        query='SELECT t.*,b.name,u.username,c.name AS component FROM tasks t JOIN bridges b ON b.id=t.bridge_id JOIN users u ON u.id=t.assignee_id LEFT JOIN components c ON c.id=t.component_id'
        args=[]; filters=[]
        if g.user['role']=='Mantención': filters.append('t.assignee_id=?'); args.append(g.user['id'])
        if request.args.get('bridge_id'): filters.append('t.bridge_id=?'); args.append(request.args['bridge_id'])
        if filters: query+=' WHERE '+' AND '.join(filters)
        return render_template('maintenance.html',tasks=rows(query+' ORDER BY t.planned_date,t.id',args),bridges=rows('SELECT * FROM bridges'),components=rows('SELECT c.*,b.name AS bridge FROM components c JOIN bridges b ON b.id=c.bridge_id'),assignees=rows("SELECT id,username FROM users WHERE role='Mantención'"),alerts=rows('SELECT a.*,b.name FROM alerts a JOIN bridges b ON b.id=a.bridge_id'))

    @app.get('/audit')
    @access('DOM')
    def audit_page(): return render_template('audit.html',events=rows('SELECT * FROM audit ORDER BY id DESC LIMIT 500'))

    @app.cli.command('init-db')
    def init_db():
        db().executescript(Path(app.root_path,'schema.sql').read_text(encoding='utf-8')); migrate(db()); db().commit(); click.echo('Base de datos inicializada sin borrar registros.')
    @app.cli.command('create-user')
    @click.argument('username')
    @click.option('--role',type=click.Choice(['DOM','Inspector','Mantención']),required=True)
    @click.password_option()
    def create_user(username,role,password):
        if len(password)<12: raise click.ClickException('Usa al menos 12 caracteres.')
        try:
            insert('users',username=username,password=generate_password_hash(password),role=role); db().commit()
        except sqlite3.IntegrityError: raise click.ClickException('El usuario ya existe.')
        click.echo('Usuario creado.')
    @app.cli.command('seed-demo')
    def seed_demo():
        if one('SELECT id FROM bridges LIMIT 1') or one('SELECT id FROM users LIMIT 1'): raise click.ClickException('La demostración requiere una base vacía para no mezclar datos.')
        for username,role in [('dom','DOM'),('inspector','Inspector'),('mantencion','Mantención')]:
            password=secrets.token_urlsafe(14)
            insert('users',username=username,password=generate_password_hash(password),role=role)
            click.echo(f'{username}: {password}')
        for code,name,location in [('DEM-01','Puente Estero Norte','Sector municipal · Biobío'),('DEM-02','Puente Ribera Sur','Sector municipal · Biobío')]:
            bid=insert('bridges',code=code,name=name,location=location,criticality='Alta',simulated=1)
            cid=insert('components',bridge_id=bid,name='Tablero')
            for kind in KINDS: insert('sensors',component_id=cid,code=code+'-'+kind.upper(),kind=kind,unit=KINDS[kind])
        configure_ev2_demo(); db().commit(); click.echo('Dos puentes de demostración configurados con EV2.')

    def _pull_provider():
        items=fetch_measurements(app.config['PROVIDER_URL'],app.config['PROVIDER_TOKEN'])
        result=dict(received=0,duplicates=0,errors=[])
        db().execute('BEGIN IMMEDIATE')  # Serializa recepción manual/automática antes de deduplicar.
        for index,item in enumerate(items):
            db().execute('SAVEPOINT provider_item')
            try:
                if not isinstance(item,dict) or item.get('simulated') is not True: raise ValueError('El proveedor académico debe identificar simulated=true.')
                required(item,'external_id')
                validate_identity(item,provider=True)
                if one('SELECT id FROM measurements WHERE external_id=?',(item['external_id'],)):
                    result['duplicates']+=1
                else: receive(item,True); result['received']+=1
                db().execute('RELEASE provider_item')
            except (ValueError,sqlite3.IntegrityError) as error:
                db().execute('ROLLBACK TO provider_item');db().execute('RELEASE provider_item')
                identity={key:item.get(key) for key in ['external_id','sensor_code','bridge_code','kind']} if isinstance(item,dict) else {'registro':'no es objeto'}
                result['errors'].append(f'Registro {index+1} {identity}: {error}')
        audit('Consultar proveedor ficticio','measurements',None,str(result)); db().commit()
        return result

    def pull_provider():
        try: return _pull_provider()
        except (ValueError,sqlite3.Error) as error:
            db().rollback()
            message=str(error) if isinstance(error,ValueError) else 'Error de persistencia IoT: '+type(error).__name__
            try:
                audit('Error al consultar proveedor ficticio','measurements',None,message);db().commit()
            except sqlite3.Error:
                db().rollback();app.logger.exception('No se pudo persistir el error IoT')
            raise ValueError(message) from error

    @app.cli.command('poll-provider')
    @click.option('--interval',default=None,type=str,help='Segundos entre consultas (1–86400). Predeterminado: IOT_POLL_INTERVAL o 60.')
    def poll_command(interval):
        try:
            seconds=interval_seconds(interval if interval is not None else os.environ.get('IOT_POLL_INTERVAL','60'))
            def cycle():
                # Cierra conexión/transacción en cada ciclo; no comparte g ni conexiones con la web.
                with app.app_context():
                    result=pull_provider()
                    app.logger.info('Consulta IoT simulada: %s',result)
            with single_worker(app.config['DATABASE']):
                click.echo(f'Captura IoT automática simulada: intervalo {seconds:g}s. Ctrl+C para detener.')
                run_polling(cycle,seconds,on_error=lambda error: app.logger.error('Ciclo IoT fallido; se reintentará: %s',error))
        except ValueError as error: raise click.ClickException(str(error))

    @app.post('/provider/pull')
    @access('DOM')
    def provider_pull():
        try:
            result=pull_provider()
            flash(f"Recepción del proveedor: {result['received']} recibidas, {result['duplicates']} duplicadas. "+' '.join(result['errors']),'warning' if result['errors'] else 'success')
        except ValueError as error: flash(str(error),'error')
        return redirect(url_for('measurements'))

    @app.cli.command('pull-provider')
    def pull_command():
        try: click.echo(pull_provider())
        except ValueError as error: raise click.ClickException(str(error))

    @app.cli.command('migrate-db')
    def migrate_command():
        migrate(db()); click.echo('Migración aditiva aplicada. Registros conservados.')

    @app.route('/inspection-plans',methods=['GET','POST'])
    @access()
    def inspection_plans():
        if request.method=='POST':
            if g.user['role']!='DOM': abort(403)
            try:
                if request.form.get('cancel'):
                    plan=get_id('inspection_plans',request.form['cancel'])
                    if plan['status']!='Programada': raise ValueError('Solo puedes cancelar una inspección programada.')
                    db().execute("UPDATE inspection_plans SET status='Cancelada' WHERE id=?",(plan['id'],));pid=plan['id']
                else:
                    required(request.form,'bridge_id','component_id','inspector_id','planned_date','description')
                    belongs(request.form['component_id'],request.form['bridge_id'])
                    inspector=get_id('users',request.form['inspector_id'])
                    if inspector['role']!='Inspector': raise ValueError('Selecciona un inspector municipal.')
                    date.fromisoformat(request.form['planned_date'])
                    pid=insert('inspection_plans',bridge_id=request.form['bridge_id'],component_id=request.form['component_id'],inspector_id=inspector['id'],planned_date=request.form['planned_date'],description=request.form['description'].strip(),author_id=g.user['id'],created_at=now())
                audit('Programar/cancelar inspección','inspection_plans',pid);db().commit()
                return redirect(url_for('inspection_plans'))
            except (ValueError,sqlite3.IntegrityError) as error: db().rollback();flash(str(error),'error')
        return render_template('inspection_plans.html',plans=rows('SELECT p.*,b.name,c.name AS component,u.username FROM inspection_plans p JOIN bridges b ON b.id=p.bridge_id JOIN components c ON c.id=p.component_id JOIN users u ON u.id=p.inspector_id ORDER BY planned_date'),bridges=rows('SELECT * FROM bridges'),components=rows('SELECT * FROM components'),inspectors=rows("SELECT * FROM users WHERE role='Inspector'"))


    def configure_ev2_demo():
        config=json.loads(Path(app.root_path,'config/ev2_pilot.json').read_text(encoding='utf-8'))
        for kind in KINDS:
            values=[float(config['thresholds'][kind][level]) for level in SEVERITIES]
            if any(not math.isfinite(value) or value<0 for value in values) or not values[0]<values[1]<values[2]: raise ValueError('Configuración EV2: umbrales no negativos, finitos y crecientes.')
        if not math.isfinite(float(config['inclination_reference'])): raise ValueError('La referencia de demostración debe ser finita.')
        author=one("SELECT id FROM users WHERE role='DOM' ORDER BY id LIMIT 1")
        if not author: raise ValueError('Crea primero un usuario DOM.')
        for b in rows('SELECT * FROM bridges WHERE simulated=1'):
            for name in ['Tablero','Viga','Estribo']:
                if not one('SELECT id FROM components WHERE bridge_id=? AND name=?',(b['id'],name)):
                    old=one('SELECT id FROM components WHERE bridge_id=? AND name=?',(b['id'],name+' · prueba'))
                    if old: db().execute('UPDATE components SET name=? WHERE id=?',(name,old['id']))
                    else: insert('components',bridge_id=b['id'],name=name)
            # Seed only missing references on demonstration sensors. Real sensors are untouched.
            db().execute("UPDATE sensors SET reference_value=? WHERE kind='inclinacion' AND reference_value IS NULL AND component_id IN (SELECT id FROM components WHERE bridge_id=?)",(config['inclination_reference'],b['id']))
            for kind,levels in config['thresholds'].items():
                for severity,threshold in levels.items():
                    if not one("SELECT id FROM rules WHERE bridge_id=? AND kind=? AND severity=? AND standard='EV2'",(b['id'],kind,severity)):
                        insert('rules',bridge_id=b['id'],kind=kind,threshold=threshold,label=LABELS[kind],simulated=1,comparison='gte',severity=severity,standard='EV2',unit=KINDS[kind],author_id=author['id'],created_at=now())
            for condition,severity in config['visual'].items():
                if not one("SELECT id FROM rules WHERE bridge_id=? AND kind='visual' AND condition=? AND standard='EV2'",(b['id'],condition)):
                    insert('rules',bridge_id=b['id'],kind='visual',condition=condition,label='Condición visual '+condition,simulated=1,comparison='gte',severity=severity,standard='EV2',author_id=author['id'],created_at=now())
        audit('Actualizar demostración EV2','bridges',None);db().commit()

    @app.cli.command('configure-ev2-demo')
    def demo_ev2_command():
        try: configure_ev2_demo();click.echo('Demostración EV2 actualizada sin duplicar infraestructura ni reglas activas.')
        except ValueError as error: raise click.ClickException(str(error))

    return app

if __name__=='__main__':
    create_app().run(host='127.0.0.1',port=5000,debug=False)
