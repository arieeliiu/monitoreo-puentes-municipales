document.querySelectorAll('form').forEach(form=>{
  const bridge=form.querySelector('[data-bridge]');
  const components=form.querySelector('[data-components]');
  if(bridge && components){
    const update=()=>{for(const option of components.options){option.hidden=!!option.value && option.dataset.bridge!==bridge.value;option.disabled=option.hidden;}if(components.selectedOptions[0]?.disabled)components.value='';};
    bridge.addEventListener('change',update);update();
  }
  const sensor=form.querySelector('[name=sensor_code]'), unit=form.querySelector('[name=unit]');
  if(sensor && unit){const update=()=>{unit.value=sensor.selectedOptions[0]?.dataset.unit||'mm/s';};sensor.addEventListener('change',update);update();}
});
