/* Interacciones de interfaz: avisos, confirmaciones, estado de envío y formulario de reglas.
   Mejora progresiva: sin este archivo los formularios y enlaces funcionan igual. */
(() => {
  'use strict';
  const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Navegación móvil desplazable: mostrar la opción activa.
  const nav = document.querySelector('.sidebar nav');
  const current = nav?.querySelector('a.selected');
  if (nav && current && nav.scrollWidth > nav.clientWidth) {
    nav.scrollLeft = Math.max(current.offsetLeft - (nav.clientWidth - current.offsetWidth) / 2, 0);
  }

  // Avisos descartables: el botón solo aparece cuando hay JavaScript.
  document.querySelectorAll('[data-dismiss]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => button.closest('.notice')?.remove());
  });

  // Registro manual de mediciones: app.js alterna el panel; aquí se sincronizan
  // todos los controles asociados y se mueve el foco al formulario o de vuelta.
  document.addEventListener('click', event => {
    const toggle = event.target.closest?.('[data-manual-toggle]');
    if (!toggle) return;
    const panel = document.getElementById(toggle.getAttribute('aria-controls'));
    if (!panel) return;
    document.querySelectorAll('[aria-controls="' + panel.id + '"]').forEach(control => control.setAttribute('aria-expanded', String(!panel.hidden)));
    if (!panel.hidden) {
      panel.querySelector('select, input:not([type=hidden])')?.focus({preventScroll: true});
      panel.scrollIntoView({block: 'nearest', behavior: reducedMotion ? 'auto' : 'smooth'});
    } else if (panel.contains(toggle)) {
      Array.from(document.querySelectorAll('[data-manual-toggle]')).find(control => !panel.contains(control))?.focus();
    }
  });

  // Diálogo de confirmación accesible (elemento <dialog> nativo).
  let dialog;
  function confirmAction({title, message, action}) {
    if (typeof HTMLDialogElement === 'undefined') return Promise.resolve(window.confirm(message));
    if (!dialog) {
      dialog = document.createElement('dialog');
      dialog.className = 'confirm-dialog';
      dialog.setAttribute('aria-labelledby', 'confirm-title');
      dialog.setAttribute('aria-describedby', 'confirm-message');
      dialog.innerHTML = '<form method="dialog"><div class="confirm-body"><span class="kpi-icon"><span class="i i-triangle" aria-hidden="true"></span></span><div><h2 id="confirm-title"></h2><p id="confirm-message"></p></div></div><div class="confirm-actions"><button value="cancel" class="secondary" data-cancel>Volver</button><button value="confirm" class="danger" data-accept></button></div></form>';
      document.body.append(dialog);
    }
    dialog.querySelector('#confirm-title').textContent = title || '¿Confirmar la operación?';
    dialog.querySelector('#confirm-message').textContent = message;
    dialog.querySelector('[data-accept]').textContent = action || 'Confirmar';
    dialog.returnValue = '';
    return new Promise(resolve => {
      dialog.addEventListener('close', () => resolve(dialog.returnValue === 'confirm'), {once: true});
      dialog.showModal();
      dialog.querySelector('[data-cancel]').focus();
    });
  }

  function confirmation(form, submitter) {
    const source = submitter?.dataset.confirm ? submitter : form;
    if (source.dataset.confirm) {
      return {title: source.dataset.confirmTitle, message: source.dataset.confirm, action: source.dataset.confirmAction};
    }
    // Seguimiento de alertas: cerrar una alerta requiere confirmación explícita.
    if (form.dataset.confirmResolve !== undefined) {
      const status = form.querySelector('[name=status]');
      if (status && status.value === 'Resuelta' && form.dataset.confirmResolve !== 'Resuelta') {
        return {title: '¿Marcar la alerta como resuelta?', action: 'Resolver alerta',
          message: 'La alerta quedará cerrada con esta nota como justificación. El cierre queda registrado en el historial.'};
      }
    }
    return null;
  }

  // Fase de captura: se resuelve antes que otros controladores del formulario.
  document.addEventListener('submit', event => {
    const form = event.target;
    if (form.dataset.confirmed === '1') { delete form.dataset.confirmed; return; }
    const request = confirmation(form, event.submitter);
    if (!request) return;
    event.preventDefault();
    event.stopPropagation();
    const submitter = event.submitter;
    confirmAction(request).then(accepted => {
      if (!accepted) return;
      form.dataset.confirmed = '1';
      if (submitter && typeof form.requestSubmit === 'function') form.requestSubmit(submitter);
      else form.requestSubmit ? form.requestSubmit() : form.submit();
    });
  }, true);

  // Estado de envío: evita envíos duplicados sin deshabilitar el botón
  // (un botón deshabilitado no enviaría su nombre y valor).
  document.addEventListener('submit', event => {
    if (event.defaultPrevented) return;
    const form = event.target;
    if ((form.getAttribute('method') || 'get').toLowerCase() !== 'post') return;
    if (form.dataset.submitting === '1') { event.preventDefault(); return; }
    form.dataset.submitting = '1';
    const button = event.submitter || form.querySelector('button:not([type=button])');
    if (button) { button.classList.add('is-loading'); button.setAttribute('aria-busy', 'true'); }
  });
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    document.querySelectorAll('form[data-submitting]').forEach(form => delete form.dataset.submitting);
    document.querySelectorAll('.is-loading').forEach(button => { button.classList.remove('is-loading'); button.removeAttribute('aria-busy'); });
  });

  // Reglas: mostrar solo el campo pertinente a la variable (umbral o condición).
  document.querySelectorAll('[data-rule-form]').forEach(form => {
    const kind = form.querySelector('[data-rule-kind]');
    const threshold = form.querySelector('[data-rule-field=threshold]');
    const condition = form.querySelector('[data-rule-field=condition]');
    const unit = form.querySelector('[data-rule-unit]');
    if (!kind || !threshold || !condition) return;
    const update = () => {
      const visual = kind.value === 'visual';
      threshold.hidden = visual;
      condition.hidden = !visual;
      threshold.querySelector('input').required = !visual;
      if (unit && !visual) {
        unit.textContent = 'Unidad: ' + (kind.selectedOptions[0]?.dataset.unit || '') +
          (kind.value === 'inclinacion' ? ' · cambio absoluto respecto de la referencia del sensor' : ' · aceleración vertical pico');
      }
    };
    kind.addEventListener('change', update);
    update();
  });
})();
