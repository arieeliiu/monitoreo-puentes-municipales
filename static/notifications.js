/* Avisos dentro del sitio. Sin permisos del navegador ni servicios externos. */
(() => {
  'use strict';
  function createAlertPoller({url, key, epoch, fetcher, storage, onCount, onAlert, onStatus,
    isVisible = () => true, setTimer = setTimeout, clearTimer = clearTimeout}) {
    let cursor = null, timer, busy = false, stopped = false;
    try { const saved = storage.getItem(key); if (/^\d+$/.test(saved || '')) cursor = saved; } catch {}
    const schedule = () => { if (!stopped) timer = setTimer(poll, 30000); };
    const stop = () => { stopped = true; clearTimer(timer); };
    async function poll() {
      if (stopped || busy) return;
      clearTimer(timer);
      if (!isVisible()) { schedule(); return; }
      busy = true;
      const controller = new AbortController();
      const timeout = setTimer(() => controller.abort(), 8000);
      try {
        const baseline = cursor === null;
        const response = await fetcher(url + (baseline ? '' : '?after=' + encodeURIComponent(cursor)), {
          credentials: 'same-origin', cache: 'no-store', signal: controller.signal,
          headers: {'Accept': 'application/json'}
        });
        if (response.status === 401 || response.status === 403) {
          stop(); onStatus('La sesión terminó o cambió de permisos. Vuelve a iniciar sesión.'); return;
        }
        if (!response.ok) throw new Error('No disponible');
        const data = await response.json();
        if (data.session_epoch !== epoch) {
          stop(); onStatus('La sesión cambió. Vuelve a cargar la página.'); return;
        }
        if (!Number.isSafeInteger(data.open_count) || data.open_count < 0 ||
            !/^\d+$/.test(data.cursor) || !Array.isArray(data.alerts)) throw new Error('Respuesta inválida');
        onCount(data.open_count);
        if (!baseline && !data.reset) {
          for (const alert of data.alerts) {
            if (!/^\d+$/.test(alert.id) || BigInt(alert.id) <= BigInt(cursor)) continue;
            // Guardar antes del aviso evita repetirlo al cambiar de página.
            cursor = alert.id;
            try { storage.setItem(key, cursor); } catch {}
            onAlert(alert);
          }
        }
        cursor = data.cursor;
        try { storage.setItem(key, cursor); } catch {}
        onStatus('Actualizado. Los avisos nuevos aparecerán aquí; el historial completo está en Alertas.');
      } catch {
        if (!stopped) onStatus('No se pudo actualizar. Se reintentará automáticamente.');
      } finally {
        busy = false; clearTimer(timeout); schedule();
      }
    }
    return {poll, stop};
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {createAlertPoller};
  if (typeof document === 'undefined') return;
  const bell = document.querySelector('[data-notifications]');
  if (!bell) return;
  const list = bell.querySelector('[data-notification-list]');
  const toasts = document.querySelector('[data-notification-toasts]');
  const makeLink = alert => {
    const link = document.createElement('a');
    link.href = '/alerts/' + alert.id;
    link.textContent = '#' + alert.id + ' · ' + alert.title + ' · ' + alert.severity + ' · ' + alert.status;
    return link;
  };
  let storage;
  try { storage = window.sessionStorage; } catch { storage = {getItem() {}, setItem() {}}; }
  const poller = createAlertPoller({url: bell.dataset.url, key: bell.dataset.key, epoch: bell.dataset.session,
    fetcher: window.fetch.bind(window), storage,
    isVisible: () => document.visibilityState !== 'hidden',
    onCount(count) { bell.querySelector('[data-open-count]').textContent = String(count); },
    onStatus(text) { bell.querySelector('[data-notification-status]').textContent = text; },
    onAlert(alert) {
      const item = document.createElement('li'); item.append(makeLink(alert)); list.prepend(item);
      while (list.children.length > 10) list.lastElementChild.remove();
      const toast = document.createElement('div'); toast.className = 'notification-toast';
      const dismiss = document.createElement('button'); dismiss.type = 'button'; dismiss.textContent = '×';
      dismiss.setAttribute('aria-label', 'Cerrar aviso de alerta ' + alert.id);
      dismiss.addEventListener('click', () => toast.remove());
      const title = document.createElement('strong'); title.textContent = 'Nueva alerta';
      toast.append(dismiss, title, makeLink(alert)); toasts.append(toast);
      while (toasts.children.length > 3) toasts.firstElementChild.remove();
      setTimeout(() => { if (!toast.contains(document.activeElement)) toast.remove(); }, 12000);
    }
  });
  poller.poll();
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') poller.poll(); });
})();
