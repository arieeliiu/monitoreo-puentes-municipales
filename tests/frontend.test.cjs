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
       match[2] === 'data-history-components' ? n.historyComponents :
       match[2] === 'data-measurement-bridge' ? n.entryBridge :
       match[2] === 'data-measurement-components' ? n.entryComponents :
       match[2] === 'data-measurement-sensors' ? n.entrySensors :
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

function chainSelect(flag,options,value=''){
 const result={[flag]:true,options,value,listeners:{},addEventListener(type,fn){this.listeners[type]=fn;},replaceChildren(...items){this.options=items;}};
 Object.defineProperty(result,'selectedOptions',{get:()=>result.options.filter(o=>o.value===result.value)});
 return result;
}
function chainSensor(value,bridge,component){return {...option(value,bridge),dataset:{bridge,component,unit:'m/s²'}};}
test('historial encadena puente, componente y sensor, incluyendo componentes vacíos',()=>{
 const bridge=chainSelect('historyBridge',[],'1');
 const components=chainSelect('historyComponents',[option(''),option('10','1'),option('11','1'),option('20','2')],'10');
 const sensors=chainSelect('historySensors',[option(''),chainSensor('abc','1','10'),chainSensor('xyz','2','20')],'abc');
 run([bridge,components,sensors]);
 assert.deepEqual(components.options.map(o=>o.value),['','10','11']);assert.equal(sensors.value,'abc');
 components.value='11';components.listeners.change();assert.deepEqual(sensors.options.map(o=>o.value),['']);assert.equal(sensors.value,'');
 bridge.value='2';bridge.listeners.change();assert.equal(components.value,'');assert.deepEqual(components.options.map(o=>o.value),['','20']);assert.deepEqual(sensors.options.map(o=>o.value),['','xyz']);
 bridge.value='';bridge.listeners.change();assert.equal(components.options.length,4);assert.equal(sensors.options.length,3);
});
test('registro manual exige puente y componente antes de ofrecer sensores y limpia selecciones incompatibles',()=>{
 const bridge=chainSelect('entryBridge',[]);bridge.required=true;
 const components=chainSelect('entryComponents',[option(''),option('10','1'),option('20','2')]);
 const sensors=chainSelect('entrySensors',[option(''),chainSensor('abc','1','10'),chainSensor('xyz','2','20')]);sensors.name='sensor_code';
 const unit={name:'unit',value:''};run([bridge,components,sensors,unit]);
 assert.equal(components.options.length,1);assert.equal(sensors.options.length,1);
 bridge.value='1';bridge.listeners.change();assert.equal(components.options.length,2);assert.equal(sensors.options.length,1);
 components.value='10';components.listeners.change();assert.deepEqual(sensors.options.map(o=>o.value),['','abc']);
 sensors.value='abc';sensors.listeners.change();assert.equal(unit.value,'m/s²');
 bridge.value='2';bridge.listeners.change();assert.equal(components.value,'');assert.equal(sensors.value,'');assert.equal(sensors.options.length,1);
});
