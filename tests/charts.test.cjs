// Utilidades de escala de los gráficos de tendencia (sin navegador).
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {niceMax, domainFor, segments, formatValue, nearest} = require('../static/charts.js');

test('escala desde cero hasta el siguiente umbral por encima de los datos', () => {
  const thresholds = [{severity: 'Atención', value: 0.5}, {severity: 'Alerta', value: 1}, {severity: 'Crítico', value: 2.5}];
  assert.deepEqual(domainFor([[0, 1], [1, 0.8]], thresholds), [0, 3]);
  assert.deepEqual(domainFor([[0, 0.229]], [{severity: 'Alerta', value: 0.229}, {severity: 'Crítico', value: 0.458}]), [0, 0.5]);
  assert.deepEqual(domainFor([[0, 9]], thresholds), [0, 12]);
  assert.deepEqual(domainFor([[0, 0]], []), [0, 1]);
});

test('máximo redondeado nunca queda bajo el valor', () => {
  for (const value of [0.0001, 0.37, 1, 1.01, 7.3, 99, 101, 5760]) assert.ok(niceMax(value) >= value, String(value));
  assert.equal(niceMax(0), 1);
});

test('no interpola intervalos sin datos', () => {
  const hour = 3600000;
  const parts = segments([[0, 1], [hour, 1], [5 * hour, 2], [6 * hour, 2]], 2.5 * hour);
  assert.deepEqual(parts.map(p => p.length), [2, 2]);
});

test('formato de valores y búsqueda del intervalo más cercano', () => {
  assert.equal(formatValue(0.2291), '0.229');
  assert.equal(formatValue(2.5), '2.5');
  assert.equal(formatValue(123.4), '123');
  const points = [[0], [10], [20], [30]];
  assert.equal(nearest(points, 14), 1);
  assert.equal(nearest(points, 16), 2);
  assert.equal(nearest(points, -5), 0);
  assert.equal(nearest(points, 99), 3);
});

const {createRefresher} = require('../static/charts.js');
const flush = () => new Promise(resolve => setImmediate(resolve));
function harness() {
  const timers = new Map(); let id = 0, clock = 0, shown = true, runs = 0, release = () => {};
  const refresher = createRefresher({interval: 60000, isVisible: () => shown, now: () => clock,
    setTimer: (fn, delay) => { timers.set(++id, {fn, delay}); return id; }, clearTimer: t => timers.delete(t),
    run: () => { runs += 1; return new Promise(resolve => { release = resolve; }); }});
  // Los temporizadores no se esperan: cada consulta queda en curso hasta finish().
  const fire = async () => { const [key, t] = [...timers.entries()].pop(); timers.delete(key); t.fn(); await flush(); };
  const finish = async () => { release(); await flush(); };
  return {refresher, timers, fire, finish, runs: () => runs, setVisible: v => { shown = v; }, advance: ms => { clock += ms; }};
}

test('actualiza cada minuto, sin consultas simultáneas', async () => {
  const h = harness();
  h.refresher.now(); assert.equal(h.runs(), 1);
  h.refresher.now(); assert.equal(h.runs(), 1, 'no inicia otra consulta mientras hay una en curso');
  await h.finish(); assert.equal(h.runs(), 2, 'la solicitud inmediata pendiente se ejecuta al terminar');
  await h.finish();
  assert.deepEqual([...h.timers.values()].map(t => t.delay), [60000]);
  await h.fire(); assert.equal(h.runs(), 3);
  await h.finish();
});

test('pausa con la pestaña oculta y se reanuda al volver', async () => {
  const h = harness();
  h.refresher.now(); await h.finish();
  h.setVisible(false); await h.fire();
  assert.equal(h.runs(), 1, 'no consulta con la pestaña oculta');
  assert.equal(h.timers.size, 1, 'sigue programada');
  h.setVisible(true); h.advance(30000); h.refresher.resume();
  assert.equal(h.runs(), 1, 'no repite si la última actualización es reciente');
  h.advance(40000); h.refresher.resume(); assert.equal(h.runs(), 2);
  await h.finish();
});

test('detener cancela las actualizaciones programadas', async () => {
  const h = harness();
  h.refresher.now(); await h.finish();
  h.refresher.stop(); assert.equal(h.timers.size, 0);
  h.refresher.now(); assert.equal(h.runs(), 1);
});
