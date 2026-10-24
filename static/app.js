document.querySelectorAll('form').forEach(form=>{
  const historyBridge=form.querySelector('[data-history-bridge]');
  const historySensors=form.querySelector('[data-history-sensors]');
  if(historyBridge && historySensors){
    const options=Array.from(historySensors.options);
    const update=()=>{
      const selected=historySensors.value;
      const visible=options.filter(o=>!o.value || !historyBridge.value || o.dataset.bridge===historyBridge.value);
      historySensors.replaceChildren(...visible);
      historySensors.value=visible.some(o=>o.value===selected)?selected:'';
    };
    historyBridge.addEventListener('change',update);update();
  }
  const bridge=form.querySelector('select[data-bridge]');
  const components=form.querySelector('[data-components]');
  if(bridge && components){
    const update=()=>{for(const option of components.options){option.hidden=!!option.value && option.dataset.bridge!==bridge.value;option.disabled=option.hidden;}if(components.selectedOptions[0]?.disabled)components.value='';};
    bridge.addEventListener('change',update);update();
  }
  const sensor=form.querySelector('[name=sensor_code]'), unit=form.querySelector('[name=unit]');
  if(sensor && unit){const update=()=>{unit.value=sensor.selectedOptions[0]?.dataset.unit||'m/s²';};sensor.addEventListener('change',update);update();}
});

// Abrir el calendario desde cualquier punto del campo, sin bloquear la escritura.
document.addEventListener('click',event=>{
  const field=event.target;
  if(!field.matches?.('input[type="date"]') || field.disabled || field.readOnly || typeof field.showPicker!=='function')return;
  try{field.showPicker();}catch{
    // Si el navegador no permite abrirlo, conservar su control nativo sin cambios.
  }
});
