const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createAlertPoller} = require('../static/notifications.js');

function setup(responses, {saved, visible = true, key = 'user:one'} = {}) {
  const memory = new Map(saved ? [[key, saved]] : []), calls = [], alerts = [], counts = [], statuses = [], timers = new Map();
  let n = 0;
  const poller = createAlertPoller({url: '/api/v1/alert-notifications', key, epoch: 'epoch',
    fetcher: async (url, options) => {
      calls.push({url, options}); const body = responses.shift();
      if (body instanceof Error) throw body;
      return {status: body.status || 200, ok: !body.status, json: async () => body};
    }, storage: {getItem: k => memory.get(k), setItem: (k,v) => memory.set(k,v)},
    onAlert: a => alerts.push(a.id), onCount: c => counts.push(c), onStatus: s => statuses.push(s),
    isVisible: () => visible,
    setTimer: (fn, delay) => { timers.set(++n, {fn, delay}); return n; }, clearTimer: id => timers.delete(id)
  });
  return {poller, memory, calls, alerts, counts, statuses, timers};
}
const body = (cursor, alerts = [], open = 4) => ({cursor, alerts, open_count: open, session_epoch: 'epoch'});

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
