'use strict';
const $ = (selector) => document.querySelector(selector);
const labels = {nueva: 'Nueva', revisada: 'Revisada', solicitada: 'Solicitada', descartada: 'Descartada'};
const titles = {'': 'Todas las ofertas', nueva: 'Ofertas nuevas', revisada: 'Ofertas revisadas', solicitada: 'Candidaturas enviadas', descartada: 'Ofertas descartadas'};
const state = {estado: 'nueva', pagina: 1, selected: null, request: 0, detailRequest: 0, saving: false};
const csrf = $('meta[name="csrf-token"]').content;
const detailPlaceholder = $('#detail').cloneNode(true);
let searchTimer;

function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $('#theme').setAttribute('aria-label', theme === 'dark' ? 'Activar tema claro' : 'Activar tema oscuro');
  $('#theme span').textContent = theme === 'dark' ? 'Claro' : 'Oscuro';
}
try { applyTheme(localStorage.getItem('cjh-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')); }
catch { applyTheme('light'); }
$('#theme').addEventListener('click', () => {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(theme);
  try { localStorage.setItem('cjh-theme', theme); } catch { /* Browser storage is optional. */ }
});
function notice(text, error = false) {
  $('#notice').textContent = text;
  $('#notice').classList.toggle('error', error);
  $('#notice').hidden = !text;
}
async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(path, {...options, signal: controller.signal, cache: 'no-store', credentials: 'same-origin'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se ha podido completar la operación.');
    return data;
  } catch (error) {
    if (error.name === 'AbortError' || error instanceof TypeError) throw new Error('No se ha podido conectar. Comprueba que el panel siga abierto e inténtalo de nuevo.');
    throw error;
  } finally { clearTimeout(timeout); }
}
function dateText(value) {
  // PostgreSQL currently stores a timestamp without timezone: preserve its calendar date.
  if (!value) return 'Fecha no disponible';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Fecha no disponible' : date.toLocaleDateString('es-ES', {day: 'numeric', month: 'short', year: 'numeric'});
}
function badge(priority) {
  const valid = ['alta', 'media', 'baja'].includes(priority);
  return node('span', `badge ${valid ? priority : ''}`, valid ? `Prioridad ${priority}` : 'Sin prioridad');
}
function closeDetail(restoreFocus = true) {
  const oldId = state.selected;
  state.selected = null;
  state.detailRequest++;
  $('#detail').replaceChildren(...Array.from(detailPlaceholder.childNodes).map(n => n.cloneNode(true)));
  $('#detail').classList.remove('open');
  document.body.classList.remove('detail-open');
  document.querySelectorAll('.offer').forEach(el => { el.classList.remove('selected'); el.setAttribute('aria-pressed', 'false'); });
  if (restoreFocus) document.querySelector(`.offer[data-id="${oldId}"]`)?.focus();
}
function renderOffers(offers) {
  const list = $('#offers');
  list.replaceChildren();
  if (!offers.length) {
    const empty = node('div', 'empty');
    empty.append(node('strong', '', 'Un poco de espacio para lo que viene.'), node('p', '', 'No hay ofertas con estos filtros. Prueba otro estado o actualiza cuando lleguen nuevas oportunidades.'));
    list.append(empty);
    return;
  }
  for (const offer of offers) {
    const button = node('button', 'offer');
    button.dataset.id = offer.id;
    button.classList.toggle('selected', offer.id === state.selected);
    button.setAttribute('aria-pressed', String(offer.id === state.selected));
    const top = node('div', 'offer-top');
    top.append(node('span', 'offer-domain', offer.dominio), node('span', '', '·'), node('span', '', dateText(offer.fecha_detectada)));
    const meta = node('div', 'offer-meta');
    meta.append(badge(offer.prioridad), node('span', '', labels[offer.estado] || 'Estado desconocido'), node('span', 'score', offer.puntuacion_relevancia == null ? 'Sin puntuación' : `${offer.puntuacion_relevancia} pts`));
    button.append(top, node('h3', 'offer-title', offer.titulo), meta);
    button.addEventListener('click', () => { if (!state.saving) openDetail(offer.id); });
    list.append(button);
  }
}
async function loadOffers() {
  const requestId = ++state.request;
  $('#offers').setAttribute('aria-busy', 'true');
  $('#refresh').disabled = true;
  $('#previous').disabled = $('#next').disabled = true;
  $('#results').textContent = 'Cargando…';
  const params = new URLSearchParams({estado: state.estado, prioridad: $('#priority').value, q: $('#search').value.trim(), orden: $('#sort').value, pagina: state.pagina});
  try {
    const [data, stats] = await Promise.all([api(`/api/ofertas?${params}`), api('/api/estadisticas')]);
    if (requestId !== state.request) return;
    const pages = Math.max(1, Math.ceil(data.total / data.tamano));
    if (state.pagina > pages) { state.pagina = pages; return await loadOffers(); }
    renderOffers(data.ofertas);
    $('#results').textContent = `${data.total} ${data.total === 1 ? 'oferta' : 'ofertas'}`;
    $('#page-label').textContent = `Página ${state.pagina} de ${pages}`;
    $('#previous').disabled = state.pagina <= 1;
    $('#next').disabled = state.pagina >= pages;
    document.querySelectorAll('[data-count]').forEach(el => { el.textContent = el.dataset.count === 'total' ? stats.total : stats.estados[el.dataset.count]; });
  } catch (error) {
    if (requestId !== state.request) return;
    notice(error.message, true);
    $('#results').textContent = 'No disponible';
    $('#offers').replaceChildren(node('div', 'empty', 'No se han podido cargar las ofertas. Pulsa «Actualizar ofertas» para volver a intentarlo.'));
    document.querySelectorAll('[data-count]').forEach(el => { el.textContent = '—'; });
  } finally {
    if (requestId === state.request) { $('#offers').setAttribute('aria-busy', 'false'); $('#refresh').disabled = false; }
  }
}
async function openDetail(id) {
  state.selected = id;
  const requestId = ++state.detailRequest;
  const panel = $('#detail');
  panel.classList.add('open');
  document.body.classList.add('detail-open');
  panel.replaceChildren(closeButton(), node('p', 'empty', 'Cargando oferta…'));
  panel.focus();
  document.querySelectorAll('.offer').forEach(el => { const selected = Number(el.dataset.id) === id; el.classList.toggle('selected', selected); el.setAttribute('aria-pressed', String(selected)); });
  try {
    const offer = await api(`/api/ofertas/${id}`);
    if (requestId !== state.detailRequest) return;
    renderDetail(offer);
  } catch (error) {
    if (requestId !== state.detailRequest) return;
    panel.replaceChildren(node('p', 'empty', error.message), closeButton());
  }
}
function closeButton() {
  const close = node('button', 'subtle-button', 'Cerrar ×');
  close.addEventListener('click', () => { if (!state.saving) closeDetail(); });
  return close;
}
function renderDetail(offer) {
  const panel = $('#detail');
  const toolbar = node('div', 'detail-toolbar');
  toolbar.append(node('span', '', 'DETALLE DE LA OFERTA'), closeButton());
  const meta = node('div', 'detail-meta');
  meta.append(badge(offer.prioridad), node('span', 'badge', offer.puntuacion_relevancia == null ? 'Sin puntuación' : `${offer.puntuacion_relevancia} puntos`));
  panel.replaceChildren(toolbar, node('p', 'detail-note', offer.dominio), node('h2', '', offer.titulo), meta);
  if (offer.url) {
    const link = node('a', 'external-link', 'Ver oferta original ↗');
    const url = new URL(offer.url);
    if (['http:', 'https:'].includes(url.protocol)) {
      link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer'; panel.append(link);
    }
  }
  panel.append(node('p', 'detail-note', `Detectada el ${dateText(offer.fecha_detectada)}. La fecha de detección no indica cuándo se publicó.`));
  panel.append(node('h3', 'detail-section-title', 'Sobre esta oportunidad'), node('div', 'description', offer.descripcion || 'Esta oferta no incluye una descripción. Consulta el enlace original para conocer los detalles.'));
  const form = node('div', 'status-form');
  const label = node('label', 'detail-section-title', 'Estado de la oferta'); label.htmlFor = 'offer-status';
  const controls = node('div', 'status-controls');
  const select = node('select'); select.id = 'offer-status';
  for (const [value, text] of Object.entries(labels)) { const option = node('option', '', text); option.value = value; select.append(option); }
  select.value = offer.estado;
  const save = node('button', 'button save-button', 'Guardar'); save.disabled = true;
  const feedback = node('p', 'detail-note');
  feedback.setAttribute('role', 'status');
  select.addEventListener('change', () => { save.disabled = select.value === offer.estado; });
  save.addEventListener('click', async () => {
    const nextState = select.value;
    state.saving = true; save.disabled = select.disabled = true; save.textContent = 'Guardando…';
    feedback.textContent = 'Guardando el cambio…';
    try {
      await api(`/api/ofertas/${offer.id}/estado`, {method: 'PATCH', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf}, body: JSON.stringify({estado: nextState})});
      offer.estado = nextState;
      feedback.textContent = 'Cambio guardado.';
      notice(`Oferta marcada como ${labels[nextState].toLowerCase()}.`);
      await loadOffers();
      if (state.estado && state.estado !== nextState) closeDetail(false);
    } catch (error) { feedback.textContent = error.message; notice(error.message, true); }
    finally { state.saving = false; select.disabled = false; save.disabled = select.value === offer.estado; save.textContent = 'Guardar'; }
  });
  controls.append(select, save);
  form.append(label, controls, feedback, node('p', 'detail-note', 'Puedes cambiar de estado en cualquier momento. Marcar como solicitada no envía una candidatura.'));
  panel.append(form);
}
function filtersChanged() { state.pagina = 1; closeDetail(false); notice(''); loadOffers(); }
$('#states').addEventListener('click', event => {
  const button = event.target.closest('[data-state]');
  if (!button || state.saving) return;
  state.estado = button.dataset.state;
  document.querySelectorAll('[data-state]').forEach(el => { el.classList.toggle('active', el === button); if (el === button) el.setAttribute('aria-current', 'page'); else el.removeAttribute('aria-current'); });
  $('#view-title').replaceChildren(document.createTextNode(titles[state.estado]), node('span', 'title-dot', '.'));
  filtersChanged();
});
$('#search').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(filtersChanged, 300); });
$('#priority').addEventListener('change', filtersChanged);
$('#sort').addEventListener('change', filtersChanged);
$('#refresh').addEventListener('click', () => { notice(''); loadOffers(); if (state.selected !== null && !state.saving) openDetail(state.selected); });
$('#previous').addEventListener('click', () => { state.pagina--; closeDetail(false); loadOffers(); });
$('#next').addEventListener('click', () => { state.pagina++; closeDetail(false); loadOffers(); });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !state.saving) closeDetail();
  // Keep keyboard focus inside the full-screen detail on small screens.
  if (event.key === 'Tab' && state.selected !== null && matchMedia('(max-width: 850px)').matches) {
    const items = Array.from($('#detail').querySelectorAll('a[href],button:not(:disabled),select:not(:disabled)'));
    const first = items[0], last = items.at(-1);
    if (!first) { event.preventDefault(); return; }
    if (event.shiftKey && (document.activeElement === first || document.activeElement === $('#detail'))) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});
loadOffers();
