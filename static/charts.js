/* Gráficos de tendencia en SVG propio (sin librerías externas; compatible con la CSP del sitio).
   Datos: /api/v1/measurement-series — máximo por intervalo de lecturas válidas. */
(() => {
  'use strict';
  const SEVERITY = {'Atención': 'attention', 'Alerta': 'alert', 'Crítico': 'critical'};

  // ---------- Utilidades puras (probadas con node --test) ----------
  function niceMax(value) {
    if (!(value > 0)) return 1;
    const base = 10 ** Math.floor(Math.log10(value));
    for (const factor of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) {
      const candidate = Number((factor * base).toPrecision(6));
      if (candidate >= value - 1e-12) return candidate;
    }
    return 10 * base;
  }
  // Escala desde cero que incluye los datos y el siguiente umbral por encima de ellos.
  function domainFor(points, thresholds) {
    const max = points.reduce((m, p) => Math.max(m, p[1]), 0);
    const above = thresholds.map(t => t.value).filter(v => v > max).sort((a, b) => a - b)[0];
    const target = Math.max(max * 1.15, above !== undefined ? above * 1.08 : 0);
    return [0, niceMax(target || 1)];
  }
  // Corta la línea cuando faltan intervalos (no se interpolan datos ausentes).
  function segments(points, gap) {
    const result = [];
    let current = [];
    for (const point of points) {
      if (current.length && point[0] - current[current.length - 1][0] > gap) { result.push(current); current = []; }
      current.push(point);
    }
    if (current.length) result.push(current);
    return result;
  }
  function formatValue(value) {
    const size = Math.abs(value);
    const digits = size >= 100 ? 0 : size >= 10 ? 1 : size >= 1 ? 2 : 3;
    return String(Number(value.toFixed(digits)));
  }
  function nearest(points, time) {
    let low = 0, high = points.length - 1;
    while (low < high) {
      const mid = (low + high) >> 1;
      if (points[mid][0] < time) low = mid + 1; else high = mid;
    }
    if (low > 0 && Math.abs(points[low - 1][0] - time) < Math.abs(points[low][0] - time)) return low - 1;
    return low;
  }
  // Actualización periódica: sin consultas simultáneas y en pausa con la pestaña oculta.
  // Una solicitud inmediata durante una consulta en curso se ejecuta al terminar esta.
  function createRefresher({run, interval = 60000, isVisible = () => true, now = () => Date.now(),
    setTimer = setTimeout, clearTimer = clearTimeout}) {
    let timer, busy = false, queued = false, stopped = false, last = -Infinity;
    const schedule = () => { clearTimer(timer); if (!stopped) timer = setTimer(() => tick(false), interval); };
    async function tick(force) {
      if (stopped) return;
      if (busy) { if (force) queued = true; return; }
      if (!force && !isVisible()) { schedule(); return; }
      busy = true;
      try { await run(); last = now(); } catch { /* run informa su propio estado */ } finally {
        busy = false;
        if (queued && !stopped) { queued = false; tick(true); } else schedule();
      }
    }
    return {
      now: () => tick(true),
      resume: () => { if (now() - last >= interval) tick(true); },
      stop: () => { stopped = true; clearTimer(timer); },
    };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {niceMax, domainFor, segments, formatValue, nearest, createRefresher};
  if (typeof document === 'undefined') return;

  // ---------- Dibujo ----------
  const NS = 'http://www.w3.org/2000/svg';
  const svgEl = (name, attrs = {}) => {
    const node = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  };
  const htmlEl = (name, className, text) => {
    const node = document.createElement(name);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const chileTime = new Intl.DateTimeFormat('es-CL', {timeZone: 'America/Santiago', hour: '2-digit', minute: '2-digit', hour12: false});
  const chileDay = new Intl.DateTimeFormat('es-CL', {timeZone: 'America/Santiago', day: '2-digit', month: '2-digit'});
  const chileHour = new Intl.DateTimeFormat('en-GB', {timeZone: 'America/Santiago', hour: '2-digit', hour12: false});

  function timeTicks(start, end, days) {
    const ticks = [];
    const hour = 3600000;
    let midnight = 0;
    for (let t = Math.ceil(start / hour) * hour; t <= end; t += hour) {
      const local = Number(chileHour.format(new Date(t))) % 24;
      if (days === 1) { if (local % 4 === 0) ticks.push([t, chileTime.format(new Date(t))]); }
      else if (local === 0) {
        if (days === 7 || midnight % 5 === 0) ticks.push([t, chileDay.format(new Date(t))]);
        midnight += 1;
      }
    }
    return ticks;
  }

  function draw(host, series, options) {
    const {start, end, days, compact} = options;
    host.replaceChildren();
    host.classList.add('chart');
    const points = series.points;
    const unit = series.unit;
    if (series.reference_missing && !points.length) {
      host.append(htmlEl('p', 'chart-status', 'Referencia de inclinación no configurada: lecturas no evaluables.'));
      return;
    }
    if (!points.length) {
      host.append(htmlEl('p', 'chart-status', 'Sin lecturas válidas en ' + (days === 1 ? 'las últimas 24 horas.' : 'los últimos ' + days + ' días.')));
      return;
    }
    const width = Math.max(Math.round(host.clientWidth || 300), 200);
    const height = compact ? 46 : 230;
    const pad = compact ? {l: 1, r: 4, t: 5, b: 5} : {l: 46, r: 14, t: 26, b: 28};
    const [y0, y1] = domainFor(points, series.thresholds);
    const x = t => pad.l + (t - start) / (end - start) * (width - pad.l - pad.r);
    const y = v => pad.t + (1 - (v - y0) / (y1 - y0)) * (height - pad.t - pad.b);
    const max = points.reduce((m, p) => Math.max(m, p[1]), 0);
    const last = points[points.length - 1];
    const summary = series.label + ' ' + series.code + ': máximo ' + formatValue(max) + ' ' + unit + ' en el período; último intervalo ' + formatValue(last[1]) + ' ' + unit + ' (' + last[2] + ').';
    const svg = svgEl('svg', {viewBox: `0 0 ${width} ${height}`, width, height, role: 'img', 'aria-label': summary});
    if (!compact) svg.setAttribute('tabindex', '0');
    const lineClass = series.kind === 'inclinacion' ? '2' : '1';

    if (!compact) {
      const grid = svgEl('g', {class: 'grid'});
      for (let n = 0; n <= 4; n++) {
        const value = y0 + (y1 - y0) * n / 4;
        const py = Math.round(y(value)) + .5;
        grid.append(svgEl('line', {x1: pad.l, x2: width - pad.r, y1: py, y2: py}));
        const label = svgEl('text', {x: pad.l - 8, y: py + 4, 'text-anchor': 'end'});
        label.textContent = formatValue(value);
        grid.append(label);
      }
      for (const [t, text] of timeTicks(start, end, days)) {
        const px = Math.round(x(t)) + .5;
        grid.append(svgEl('line', {x1: px, x2: px, y1: height - pad.b, y2: height - pad.b + 4}));
        const label = svgEl('text', {x: px, y: height - 8, 'text-anchor': 'middle'});
        label.textContent = text;
        grid.append(label);
      }
      svg.append(grid);
      const unitLabel = svgEl('text', {x: 0, y: 10, 'text-anchor': 'start'});
      unitLabel.textContent = unit;
      svg.append(unitLabel);
    }
    for (const threshold of series.thresholds) {
      if (threshold.value > y1 || threshold.value < y0) continue;
      const tone = SEVERITY[threshold.severity] || 'alert';
      const py = Math.round(y(threshold.value)) + .5;
      svg.append(svgEl('line', {class: 'threshold threshold-' + tone, x1: pad.l, x2: width - pad.r, y1: py, y2: py}));
      if (!compact) {
        const label = svgEl('text', {class: 'label-' + tone, x: width - pad.r, y: py - 5, 'text-anchor': 'end'});
        label.textContent = threshold.severity + ' ≥ ' + formatValue(threshold.value);
        svg.append(label);
      }
    }
    const gap = (days === 1 ? 10 : 60) * 60000 * 2.5;
    for (const part of segments(points, gap)) {
      const line = part.map((p, i) => (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ' ' + y(p[1]).toFixed(1)).join('');
      if (part.length > 1) {
        const area = line + 'L' + x(part[part.length - 1][0]).toFixed(1) + ' ' + y(y0).toFixed(1) + 'L' + x(part[0][0]).toFixed(1) + ' ' + y(y0).toFixed(1) + 'Z';
        svg.append(svgEl('path', {class: 'area-' + lineClass, d: area}));
        svg.append(svgEl('path', {class: 'series series-' + lineClass, d: line}));
      } else {
        svg.append(svgEl('circle', {class: 'series series-' + lineClass, cx: x(part[0][0]).toFixed(1), cy: y(part[0][1]).toFixed(1), r: 2}));
      }
    }
    svg.append(svgEl('circle', {class: 'focus-dot series-' + lineClass, cx: x(last[0]).toFixed(1), cy: y(last[1]).toFixed(1), r: compact ? 2.5 : 3.5}));

    // Interacción: puntero y teclado (flechas) muestran el valor del intervalo.
    const focusLine = svgEl('line', {class: 'focus-line', y1: pad.t, y2: height - pad.b, visibility: 'hidden'});
    const focusDot = svgEl('circle', {class: 'focus-dot series-' + lineClass, r: 4, visibility: 'hidden'});
    const overlay = svgEl('rect', {x: pad.l, y: 0, width: Math.max(width - pad.l - pad.r, 1), height, fill: 'transparent'});
    svg.append(focusLine, focusDot, overlay);
    const tip = htmlEl('div', 'chart-tip');
    tip.setAttribute('aria-hidden', 'true');
    host.append(svg, tip);
    let index = points.length - 1;
    const show = i => {
      index = Math.max(0, Math.min(points.length - 1, i));
      const p = points[index];
      const px = x(p[0]), py = y(p[1]);
      focusLine.setAttribute('x1', px); focusLine.setAttribute('x2', px); focusLine.setAttribute('visibility', 'visible');
      focusDot.setAttribute('cx', px); focusDot.setAttribute('cy', py); focusDot.setAttribute('visibility', 'visible');
      tip.replaceChildren(htmlEl('strong', '', formatValue(p[1]) + ' ' + unit), htmlEl('span', '', p[2] + ' · ' + p[3] + ' lectura' + (p[3] === 1 ? '' : 's')));
      tip.classList.add('visible');
      const left = Math.min(Math.max(px - tip.offsetWidth / 2, 0), width - tip.offsetWidth);
      tip.style.transform = `translate(${Math.round(left)}px, ${Math.round(compact ? -tip.offsetHeight - 6 : Math.max(py - tip.offsetHeight - 12, -8))}px)`;
    };
    const hide = () => { focusLine.setAttribute('visibility', 'hidden'); focusDot.setAttribute('visibility', 'hidden'); tip.classList.remove('visible'); };
    overlay.addEventListener('pointermove', event => {
      const box = svg.getBoundingClientRect();
      const ratio = (event.clientX - box.left) / box.width * width;
      show(nearest(points, start + (ratio - pad.l) / (width - pad.l - pad.r) * (end - start)));
    });
    overlay.addEventListener('pointerleave', hide);
    svg.addEventListener('focus', () => show(index));
    svg.addEventListener('blur', hide);
    svg.addEventListener('keydown', event => {
      const step = {ArrowLeft: -1, ArrowRight: 1, Home: -Infinity, End: Infinity}[event.key];
      if (step === undefined) return;
      event.preventDefault();
      show(Number.isFinite(step) ? index + step : (step < 0 ? 0 : points.length - 1));
    });
  }

  const LIVE_INTERVAL = 60000; // el proveedor de nube registra lecturas cada minuto
  const clock = new Intl.DateTimeFormat('es-CL', {timeZone: 'America/Santiago', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false});
  class SessionEnded extends Error {}
  async function load(params) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/api/v1/measurement-series?' + new URLSearchParams(params), {
        credentials: 'same-origin', cache: 'no-store', headers: {Accept: 'application/json'}, signal: controller.signal});
      if (response.status === 401) throw new SessionEnded('La sesión terminó. Vuelve a iniciar sesión para ver datos actualizados.');
      if (!response.ok) throw new Error('No fue posible cargar la tendencia.');
      return await response.json();
    } catch (error) {
      if (error instanceof SessionEnded) throw error;
      throw new Error('No fue posible cargar la tendencia.');
    } finally { clearTimeout(timeout); }
  }
  const windowFor = data => {
    const end = Date.parse(data.generated_at) || Date.now();
    return {start: end - data.days * 86400000, end, days: data.days};
  };
  // Solo se redibuja si llegaron datos nuevos o la ventana avanzó más de 5 minutos.
  const signature = data => JSON.stringify(data.series.map(s => [s.id, s.points.length, s.points[s.points.length - 1], s.counts, s.thresholds]));
  const needsDraw = (previous, data, span) => !previous || previous.signature !== signature(data) || span.end - previous.end > 300000;
  const liveText = () => 'actualizado ' + clock.format(new Date()) + ' · se actualiza cada minuto';

  const redraws = [], refreshers = [];
  if (typeof ResizeObserver !== 'undefined') {
    let pending = false;
    const observer = new ResizeObserver(() => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => { pending = false; redraws.forEach(fn => fn()); });
    });
    observer.observe(document.querySelector('.main') || document.body);
  }
  const visible = () => document.visibilityState !== 'hidden';
  document.addEventListener('visibilitychange', () => { if (visible()) refreshers.forEach(r => r.resume()); });

  // Minigráficos del panel: una consulta para todos los sensores, renovada cada minuto.
  const sparks = document.querySelectorAll('[data-spark]');
  if (sparks.length) {
    let drawn = null, byId = new Map(), span = null;
    const render = () => sparks.forEach(host => {
      const series = byId.get(host.dataset.spark);
      if (!series) return;
      draw(host, series, {...span, compact: true});
      if (series.points.length) {
        const max = series.points.reduce((m, p) => Math.max(m, p[1]), 0);
        host.append(htmlEl('small', 'muted', (series.kind === 'inclinacion' ? 'Cambio máx.' : 'Máx.') + ' 7 días: ' + formatValue(max) + ' ' + series.unit));
      }
    });
    redraws.push(() => { if (span) render(); });
    const refresher = createRefresher({interval: LIVE_INTERVAL, isVisible: visible, run: async () => {
      try {
        const data = await load({days: '7'});
        const nextSpan = windowFor(data);
        if (!needsDraw(drawn, data, nextSpan)) return;
        byId = new Map(data.series.map(s => [String(s.id), s]));
        span = nextSpan;
        drawn = {signature: signature(data), end: nextSpan.end};
        render();
      } catch (error) {
        if (error instanceof SessionEnded) refresher.stop();
        // Se conservan los últimos minigráficos; solo se informa si nunca se cargaron.
        if (!drawn || error instanceof SessionEnded) sparks.forEach(host => host.replaceChildren(htmlEl('p', 'chart-status', error.message)));
        throw error;
      }
    }});
    refreshers.push(refresher);
    refresher.now();
  }

  // Gráfico de detalle con selector de período y actualización en vivo.
  document.querySelectorAll('[data-series-chart]').forEach(host => {
    const scope = {};
    if (host.dataset.bridge) scope.bridge_id = host.dataset.bridge;
    if (host.dataset.sensor) scope.sensor_id = host.dataset.sensor;
    let days = host.dataset.days || '7';
    let drawn = null;
    const controls = htmlEl('div', 'segmented');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Período del gráfico');
    const body = htmlEl('div');
    const status = htmlEl('p', 'chart-status', 'Cargando tendencia…');
    const live = htmlEl('span', 'live-indicator');
    live.setAttribute('aria-hidden', 'true');
    live.hidden = true;
    const meta = htmlEl('div', 'chart-meta');
    meta.append(live, status);
    const head = htmlEl('div', 'chart-head');
    head.append(controls, meta);
    host.replaceChildren(head, body);
    let render = () => {};
    redraws.push(() => render());
    const refresher = createRefresher({interval: LIVE_INTERVAL, isVisible: visible, run: async () => {
      const requested = days;
      try {
        const data = await load({...scope, days: requested});
        if (requested !== days) return; // el período cambió durante la consulta
        host.removeAttribute('aria-busy');
        const span = windowFor(data);
        const period = 'Período: ' + (span.days === 1 ? 'últimas 24 horas' : 'últimos ' + span.days + ' días') + ' · hora de Chile';
        live.hidden = !data.series.length;
        live.classList.remove('is-stale');
        status.textContent = data.series.length ? period + ' · ' + liveText() : 'Sin sensores para esta selección.';
        if (!needsDraw(drawn, data, span)) return;
        drawn = {signature: signature(data), end: span.end};
        const cards = data.series.map(series => {
          const card = htmlEl('article', 'chart-card');
          const title = htmlEl('div', 'chart-head');
          const heading = htmlEl('h3', '', series.label + ' · ');
          heading.append(htmlEl('span', 'mono', series.code));
          const valid = series.counts.valido || 0;
          const other = (series.counts.invalido || 0) + (series.counts.no_disponible || 0);
          title.append(heading, htmlEl('span', 'muted', series.component + ' · ' + series.bridge_code + ' · ' + valid + ' lecturas válidas' + (other ? ', ' + other + ' inválidas o no disponibles' : '')));
          const plot = htmlEl('div', 'chart');
          const legend = htmlEl('div', 'chart-legend');
          const swatch = htmlEl('span');
          const line = htmlEl('i', 'sw-line');
          if (series.kind === 'inclinacion') line.classList.add('sw-line-2');
          swatch.append(line, document.createTextNode(series.metric + ' (' + series.unit + ')'));
          legend.append(swatch);
          for (const threshold of series.thresholds) {
            const item = htmlEl('span');
            item.append(htmlEl('i', 'sw-dash-' + (SEVERITY[threshold.severity] || 'alert')), document.createTextNode(threshold.severity + ' ≥ ' + formatValue(threshold.value) + ' ' + series.unit));
            legend.append(item);
          }
          card.append(title, plot, legend);
          return {card, plot, series};
        });
        body.replaceChildren(...cards.map(c => c.card));
        render = () => cards.forEach(c => draw(c.plot, c.series, {...span, compact: false}));
        render();
      } catch (error) {
        host.removeAttribute('aria-busy');
        if (error instanceof SessionEnded) { refresher.stop(); live.hidden = true; status.textContent = error.message; }
        else if (drawn) { live.classList.add('is-stale'); status.textContent = 'No se pudo actualizar a las ' + clock.format(new Date()) + '. Se reintentará en un minuto; se muestran los últimos datos recibidos.'; }
        else status.textContent = error.message;
        throw error;
      }
    }});
    refreshers.push(refresher);
    for (const [value, label] of [['1', '24 horas'], ['7', '7 días'], ['30', '30 días']]) {
      const button = htmlEl('button', '', label);
      button.type = 'button';
      button.dataset.range = value;
      button.setAttribute('aria-pressed', String(value === days));
      button.addEventListener('click', () => {
        if (days === value) return;
        days = value;
        drawn = null;
        controls.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.range === days)));
        status.textContent = 'Cargando tendencia…';
        host.setAttribute('aria-busy', 'true');
        refresher.now();
      });
      controls.append(button);
    }
    host.setAttribute('aria-busy', 'true');
    refresher.now();
  });
})();
