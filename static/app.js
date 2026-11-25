document.querySelectorAll('form').forEach(form=>{
  const chainBridge=form.querySelector('[data-history-bridge]') || form.querySelector('[data-measurement-bridge]');
  const chainComponents=form.querySelector('[data-history-components]') || form.querySelector('[data-measurement-components]');
  const chainSensors=form.querySelector('[data-history-sensors]') || form.querySelector('[data-measurement-sensors]');
  if(chainBridge && chainSensors){
    const components=chainComponents?Array.from(chainComponents.options):[];
    const sensors=Array.from(chainSensors.options);
    const replace=(select,options)=>{
      const selected=select.value;
      select.replaceChildren(...options);
      select.value=options.some(o=>o.value===selected)?selected:'';
    };
    const update=()=>{
      const bridge=chainBridge.value;
      if(chainComponents)replace(chainComponents,components.filter(o=>!o.value || (bridge?o.dataset.bridge===bridge:!chainBridge.required)));
      const component=chainComponents?.value || '';
      replace(chainSensors,sensors.filter(o=>!o.value ||
        ((!bridge || o.dataset.bridge===bridge) && (!component || o.dataset.component===component) &&
        (!chainBridge.required || (bridge && component)))));
      const unit=form.querySelector('[name=unit]');
      if(unit)unit.value=chainSensors.selectedOptions[0]?.dataset.unit || 'm/s²';
    };
    chainBridge.addEventListener('change',update);
    chainComponents?.addEventListener('change',update);
    update();
  }
  const bridge=form.querySelector('select[data-bridge]');
  // Componentes y alertas dependientes del puente: se ocultan las opciones de otros puentes.
  const scoped=bridge?[...form.querySelectorAll('[data-components],[data-bridge-options]')]:[];
  if(scoped.length){
    const update=()=>{for(const select of scoped){for(const option of select.options){option.hidden=!!option.value && option.dataset.bridge!==bridge.value;option.disabled=option.hidden;}if(select.selectedOptions[0]?.disabled)select.value='';}};
    bridge.addEventListener('change',update);update();
  }
  const sensor=form.querySelector('[name=sensor_code]'), unit=form.querySelector('[name=unit]');
  if(sensor && unit){const update=()=>{unit.value=sensor.selectedOptions[0]?.dataset.unit||'m/s²';};sensor.addEventListener('change',update);update();}
});

// Abrir el calendario desde cualquier punto del campo, sin bloquear la escritura.
document.addEventListener('click',event=>{
  const field=event.target;
  if(field.matches?.('[data-manual-toggle]')){
    const panel=document.getElementById(field.getAttribute('aria-controls'));
    panel.hidden=!panel.hidden;
    field.setAttribute('aria-expanded',String(!panel.hidden));
    return;
  }
  if(!field.matches?.('input[type="date"]') || field.disabled || field.readOnly || typeof field.showPicker!=='function')return;
  try{field.showPicker();}catch{
    // Si el navegador no permite abrirlo, conservar su control nativo sin cambios.
  }
});
