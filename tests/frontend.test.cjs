// Native Node test runner: no browser packages or npm dependencies required.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {runInNewContext} = require('node:vm');
const script = readFileSync(resolve(__dirname, '../static/app.js'), 'utf8');

function option(value, bridge) {
  return {tag: 'option', value, dataset: {bridge}, hidden: false, disabled: false, addEventListener() {}};
}
function componentSelect() {
  const control = {tag: 'select', components: true, value: '10',
    options: [option('', undefined), option('10', '1'), option('20', '2')]};
  Object.defineProperty(control, 'selectedOptions', {get: () => control.options.filter(o => o.value === control.value)});
  return control;
}
function run(nodes) {
  // Minimal DOM surface used by the production script; options also carry data-bridge.
  const form = {querySelector(selector) {
    const match = /^(select)?\[([^=\]]+)(?:=([^\]]+))?\]$/.exec(selector);
    if (!match) throw new Error('Unsupported fixture selector: ' + selector);
    return nodes.find(n => (!match[1] || n.tag === match[1]) &&
      (match[2] === 'data-bridge' ? n.dataset?.bridge !== undefined :
       match[2] === 'data-components' ? n.components :
       match[2] === 'data-history-bridge' ? n.historyBridge :
       match[2] === 'data-history-sensors' ? n.historySensors :
       match[2] === 'name' ? n.name === match[3] : false)) || null;
  }};
  runInNewContext(script, {document: {querySelectorAll: () => [form], addEventListener() {}}});
}

test('sensor form without bridge selector keeps every component available', () => {
  const components = componentSelect();
  run([components, ...components.options]);
  assert.equal(components.value, '10');
  assert.ok(components.options.every(o => !o.disabled && !o.hidden));
});

test('bridge selector still filters components and clears an incompatible choice', () => {
  let change;
  const bridge = {tag: 'select', value: '1', dataset: {bridge: ''}, addEventListener: (_, fn) => {change = fn;}};
  const components = componentSelect();
  run([bridge, components, ...components.options]);
  assert.equal(components.options[1].disabled, false);
  assert.equal(components.options[2].disabled, true);
  assert.equal(components.value, '10');
  bridge.value = '2'; change();
  assert.equal(components.options[1].disabled, true);
  assert.equal(components.options[2].disabled, false);
  assert.equal(components.value, '');
  assert.equal(components.options[0].disabled, false);
});

test('measurement sensor selection still updates EV2 units', () => {
  let change;
  const sensor = {name: 'sensor_code', selectedOptions: [{dataset: {unit: 'm/s²'}}], addEventListener: (_, fn) => {change = fn;}};
  const unit = {name: 'unit', value: ''};
  run([sensor, unit]);
  assert.equal(unit.value, 'm/s²');
  sensor.selectedOptions = [{dataset: {unit: '°'}}]; change();
  assert.equal(unit.value, '°');
});

test('historial reconstruye sensores por relación y conserva o reinicia selección',()=>{
 let change;
 const bridge={historyBridge:true,value:'1',addEventListener:(_,fn)=>change=fn};
 const sensors={historySensors:true,value:'10',options:[option(''),option('10','1'),option('20','2')],replaceChildren(...items){this.options=items;}};
 run([bridge,sensors]);
 assert.deepEqual(sensors.options.map(o=>o.value),['','10']);
 assert.equal(sensors.value,'10');
 bridge.value='2';change();assert.deepEqual(sensors.options.map(o=>o.value),['','20']);assert.equal(sensors.value,'');
 sensors.value='20';change();assert.equal(sensors.value,'20');
 bridge.value='';change();assert.deepEqual(sensors.options.map(o=>o.value),['','10','20']);assert.equal(sensors.value,'20');
});
