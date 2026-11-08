const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createAlertPoller} = require('../static/notifications.js');

function setup(responses, {saved, visible = true, key = 'user:one'} = {}) {
  const memory = new Map(saved ? [[key, saved]] : []), calls = [], alerts = [], counts = [], statuses = [], timers = new Map();
  let n = 0, shown = visible;
  const poller = createAlertPoller({url: '/api/v1/alert-notifications', key, epoch: 'epoch',
    fetcher: async (url, options) => {
      calls.push({url, options}); const body = responses.shift();
      if (body instanceof Error) throw body;
      return {status: body.status || 200, ok: !body.status, json: async () => body};
    }, storage: {getItem: k => memory.get(k), setItem: (k,v) => memory.set(k,v)},
    onAlert: a => alerts.push(a.id), onCount: c => counts.push(c), onStatus: s => statuses.push(s),
    isVisible: () => shown,
    setTimer: (fn, delay) => { timers.set(++n, {fn, delay}); return n; }, clearTimer: id => timers.delete(id)
  });
  return {poller, memory, calls, alerts, counts, statuses, timers, setVisible: value => { shown = value; }};
}
const body = (cursor, alerts = [], open = 4, more = false) => ({cursor, alerts, open_count: open, session_epoch: 'epoch', has_more: more});

test('baseline ignores historical alerts and open count is not unread count', async () => {
  const s = setup([body('50', [{id:'50'}], 42)]); await s.poller.poll();
  assert.deepEqual(s.alerts, []); assert.deepEqual(s.counts, [42]);
  assert.equal(s.calls[0].url, '/api/v1/alert-notifications');
  assert.equal(s.calls[0].options.credentials, 'same-origin');
  assert.deepEqual([...s.timers.values()].map(t => t.delay), [30000]);
});
test('new alerts notify once and cursor survives navigation', async () => {
  const s = setup([body('5'), body('7', [{id:'6'}, {id:'7'}]), body('7', [{id:'7'}])]);
  await s.poller.poll(); await s.poller.poll(); await s.poller.poll();
  assert.deepEqual(s.alerts, ['6','7']); assert.equal(s.memory.get('user:one'), '7');
  const next = setup([body('8',[{id:'8'}])], {saved:'7'}); await next.poller.poll();
  assert.equal(next.calls[0].url, '/api/v1/alert-notifications?after=7'); assert.deepEqual(next.alerts,['8']);
});
test('new user or login starts its own baseline', async () => {
  const s = setup([body('90',[{id:'89'}])], {key:'user:two:new-login'}); await s.poller.poll();
  assert.deepEqual(s.alerts,[]); assert.equal(s.calls[0].url,'/api/v1/alert-notifications');
});
test('expiry and session switch stop polling without displaying another user response', async () => {
  for (const response of [{status:401}, {status:403}, {...body('9',[{id:'9'}]),session_epoch:'another'}]) {
    const s = setup([response], {saved:'8'}); await s.poller.poll(); await s.poller.poll();
    assert.equal(s.calls.length,1); assert.deepEqual(s.alerts,[]); assert.equal(s.timers.size,0);
  }
});
test('errors retry without advancing cursor, hidden pages do not fetch, reset is silent', async () => {
  const s = setup([new Error('offline'), {...body('0',[{id:'1'}]),reset:true}],{saved:'99'});
  await s.poller.poll(); assert.equal(s.memory.get('user:one'),'99');
  await s.poller.poll(); assert.equal(s.memory.get('user:one'),'0'); assert.deepEqual(s.alerts,[]);
  const hidden = setup([], {visible:false}); await hidden.poller.poll(); assert.equal(hidden.calls.length,0);
  assert.equal(hidden.timers.size,1);
});
test('overlapping calls issue only one request', async () => {
  const s = setup([body('20')]); await Promise.all([s.poller.poll(),s.poller.poll()]);
  assert.equal(s.calls.length,1);
});

const delay = state => [...state.timers.values()].map(t => t.delay);
const batch = (first, last) => Array.from({length:last-first+1}, (_,i) => ({id:String(first+i)}));
test('pending batches drain in one-second steps and return to normal polling', async () => {
  const s=setup([body('5'),body('25',batch(6,25),45,true),body('45',batch(26,45),45,true),body('50',batch(46,50),45)]);
  await s.poller.poll();assert.deepEqual(delay(s),[30000]);
  await s.poller.poll();assert.deepEqual(delay(s),[1000]);
  await [...s.timers.values()][0].fn();assert.deepEqual(delay(s),[1000]);
  await [...s.timers.values()][0].fn();assert.deepEqual(delay(s),[30000]);
  assert.equal(s.alerts.length,45);assert.equal(new Set(s.alerts).size,45);
  assert.equal(s.memory.get('user:one'),'50');
  assert.deepEqual(s.calls.map(c=>c.url),['/api/v1/alert-notifications','/api/v1/alert-notifications?after=5','/api/v1/alert-notifications?after=25','/api/v1/alert-notifications?after=45']);
});
test('large backlog pauses after four batches instead of flooding the server', async () => {
  const s=setup([body('20',batch(1,20),100,true),body('40',batch(21,40),100,true),body('60',batch(41,60),100,true),body('80',batch(61,80),100,true),body('100',batch(81,100),100)],{saved:'0'});
  for (const expected of [1000,1000,1000,5000,30000]) {
    await s.poller.poll();assert.deepEqual(delay(s),[expected]);
  }
  assert.equal(s.alerts.length,100);assert.equal(new Set(s.alerts).size,100);
});
test('failed or non-progressing drains fall back to 30 seconds and retain cursor', async () => {
  const s=setup([body('20',batch(1,20),40,true),new Error('offline'),body('20',[],40,true)],{saved:'0'});
  await s.poller.poll();assert.deepEqual(delay(s),[1000]);
  await s.poller.poll();assert.deepEqual(delay(s),[30000]);assert.equal(s.memory.get('user:one'),'20');
  await s.poller.poll();assert.deepEqual(delay(s),[30000]);assert.equal(s.alerts.length,20);
});
test('hidden page suspends backlog queries and resumes without duplicate alerts', async () => {
  const s=setup([body('20',batch(1,20),25,true),body('25',batch(21,25),25)],{saved:'0'});
  await s.poller.poll();s.setVisible(false);await s.poller.poll();
  assert.equal(s.calls.length,1);assert.deepEqual(delay(s),[30000]);
  s.setVisible(true);await s.poller.poll();assert.equal(s.alerts.length,25);
  assert.equal(new Set(s.alerts).size,25);assert.deepEqual(delay(s),[30000]);
});
