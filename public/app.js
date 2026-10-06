// Studio Podcast — interface (vanilla JS)

const STATUSES = [
  { id: 'idee', label: 'Idée' },
  { id: 'preparation', label: 'Préparation' },
  { id: 'enregistre', label: 'Enregistré' },
  { id: 'montage', label: 'Montage' },
  { id: 'planifie', label: 'Planifié' },
  { id: 'publie', label: 'Publié' },
];
const STATUS = Object.fromEntries(STATUSES.map((s) => [s.id, s]));

const GUEST_STATUSES = [
  { id: 'a_contacter', label: 'À contacter' },
  { id: 'contacte', label: 'Contacté' },
  { id: 'confirme', label: 'Confirmé' },
  { id: 'enregistre', label: 'Enregistré' },
  { id: 'decline', label: 'A décliné' },
];
const GUEST_STATUS = Object.fromEntries(GUEST_STATUSES.map((s) => [s.id, s]));

const DEFAULT_CHECKLIST = [
  'Recherche & questions',
  'Invité confirmé',
  'Enregistrement',
  'Montage',
  'Mixage / mastering',
  'Visuel / miniature',
  "Notes d'épisode",
  'Publication',
  'Promotion réseaux sociaux',
];

const state = {
  episodes: [],
  guests: [],
  tasks: [],
  settings: {},
  episodeView: localStorage.getItem('episodeView') || 'board',
  search: '',
  calMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  taskFilter: 'open',
};

// ---------- Utilitaires ----------

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

async function api(path, opts = {}) {
  const res = await fetch('/api/' + path, {
    headers: opts.body && !(opts.body instanceof Blob) ? { 'Content-Type': 'application/json' } : opts.headers,
    ...opts,
    body: opts.body && !(opts.body instanceof Blob) ? JSON.stringify(opts.body) : opts.body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Erreur ${res.status}`);
  return data;
}

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove('show'), 2200);
}

const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

function fmtDate(s, withTime = false) {
  if (!s) return '';
  const d = new Date(s.length <= 10 ? s + 'T00:00' : s);
  if (isNaN(d)) return s;
  const opts = { day: 'numeric', month: 'short', year: 'numeric' };
  if (withTime && s.length > 10) Object.assign(opts, { hour: '2-digit', minute: '2-digit' });
  return d.toLocaleDateString('fr-FR', opts);
}

function fmtDuration(sec) {
  sec = Number(sec) || 0;
  if (!sec) return '';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.round(sec % 60);
  return h ? `${h}h${String(m).padStart(2, '0')}` : `${m}:${String(s).padStart(2, '0')}`;
}

function parseDuration(str) {
  str = String(str || '').trim();
  if (!str) return 0;
  const parts = str.split(':').map(Number);
  if (parts.some(isNaN)) return 0;
  return parts.reduce((acc, n) => acc * 60 + n, 0);
}

const epLabel = (e) => [e.season ? `S${e.season}` : '', e.number ? `É${e.number}` : ''].filter(Boolean).join(' · ');
const statusBadge = (id) =>
  `<span class="badge status" style="background:var(--s-${id})">${esc(STATUS[id]?.label || id)}</span>`;
const guestNames = (ids = []) =>
  ids.map((id) => state.guests.find((g) => g.id === id)?.name).filter(Boolean);
const checklistProgress = (e) => {
  const list = e.checklist || [];
  if (!list.length) return 0;
  return Math.round((list.filter((c) => c.done).length / list.length) * 100);
};
const dateOnly = (s) => (s || '').slice(0, 10);

async function loadAll() {
  [state.episodes, state.guests, state.tasks, state.settings] = await Promise.all([
    api('episodes'),
    api('guests'),
    api('tasks'),
    api('settings'),
  ]);
  $('#brand-title').textContent = state.settings.title || 'Studio Podcast';
  document.title = `${state.settings.title || 'Studio'} — Podcast`;
}

// ---------- Routage ----------

const views = { dashboard, episodes, calendar, guests, tasks, settings };

function render() {
  const name = location.hash.slice(1) || 'dashboard';
  const view = views[name] ? name : 'dashboard';
  $$('nav a').forEach((a) => a.classList.toggle('active', a.dataset.view === view));
  $('#view').innerHTML = views[view]();
  bind[view]?.();
}
window.addEventListener('hashchange', render);

// ---------- Tableau de bord ----------

function dashboard() {
  const eps = state.episodes;
  const today = todayStr();
  const count = (s) => eps.filter((e) => e.status === s).length;
  const inProgress = eps.filter((e) => !['idee', 'publie'].includes(e.status)).length;

  const upcomingRec = eps
    .filter((e) => e.recordDate && dateOnly(e.recordDate) >= today && e.status !== 'publie')
    .sort((a, b) => a.recordDate.localeCompare(b.recordDate))
    .slice(0, 6);
  const upcomingPub = eps
    .filter((e) => e.publishDate && dateOnly(e.publishDate) >= today && e.status !== 'publie')
    .sort((a, b) => a.publishDate.localeCompare(b.publishDate))
    .slice(0, 6);
  const lateTasks = state.tasks
    .filter((t) => !t.done && t.due && t.due < today)
    .sort((a, b) => a.due.localeCompare(b.due));
  const soonTasks = state.tasks
    .filter((t) => !t.done && (!t.due || t.due >= today))
    .sort((a, b) => (a.due || '9999').localeCompare(b.due || '9999'))
    .slice(0, 6);
  const active = eps
    .filter((e) => !['idee', 'publie'].includes(e.status))
    .sort((a, b) => STATUSES.findIndex((s) => s.id === b.status) - STATUSES.findIndex((s) => s.id === a.status));
  const totalDuration = eps.filter((e) => e.status === 'publie').reduce((a, e) => a + (Number(e.duration) || 0), 0);

  const epLi = (e, field, icon) => `
    <li class="clickable" data-ep="${e.id}">
      <span>${icon}</span>
      <div class="grow"><div>${esc(e.title || 'Sans titre')}</div>
      <div class="muted small">${fmtDate(e[field], true)} ${guestNames(e.guestIds).length ? '· avec ' + esc(guestNames(e.guestIds).join(', ')) : ''}</div></div>
      ${statusBadge(e.status)}
    </li>`;
  const taskLi = (t) => `
    <li class="task-row">
      <input type="checkbox" data-task-done="${t.id}" ${t.done ? 'checked' : ''} />
      <div class="grow">${esc(t.title)}
        ${t.episodeId ? `<div class="muted small">🎧 ${esc(state.episodes.find((e) => e.id === t.episodeId)?.title || '')}</div>` : ''}
      </div>
      ${t.due ? `<span class="small ${t.due < today ? 'overdue' : 'muted'}">${fmtDate(t.due)}</span>` : ''}
    </li>`;

  return `
    <div class="page-head"><h1>Bonjour 👋</h1><div class="spacer"></div>
      <button class="primary" data-new-ep>＋ Nouvel épisode</button></div>
    <div class="grid g4" style="margin-bottom:16px">
      <div class="card"><div class="stat">${count('publie')}</div><div class="stat-label">Épisodes publiés</div></div>
      <div class="card"><div class="stat">${inProgress}</div><div class="stat-label">En production</div></div>
      <div class="card"><div class="stat">${count('idee')}</div><div class="stat-label">Idées en réserve</div></div>
      <div class="card"><div class="stat">${state.guests.filter((g) => g.status === 'confirme').length}<span class="muted" style="font-size:16px"> / ${state.guests.length}</span></div><div class="stat-label">Invités confirmés / total</div></div>
    </div>
    <div class="grid g2">
      <div class="card"><h3>🎙️ Prochains enregistrements</h3>
        <ul class="list">${upcomingRec.map((e) => epLi(e, 'recordDate', '🎙️')).join('') || '<li class="empty">Aucun enregistrement prévu</li>'}</ul></div>
      <div class="card"><h3>📢 Prochaines publications</h3>
        <ul class="list">${upcomingPub.map((e) => epLi(e, 'publishDate', '📢')).join('') || '<li class="empty">Aucune publication prévue</li>'}</ul></div>
      <div class="card"><h3>🛠️ En production</h3>
        <ul class="list">${
          active
            .map(
              (e) => `<li class="clickable" data-ep="${e.id}"><div class="grow"><div>${esc(e.title || 'Sans titre')}</div>
                <div class="progress" style="margin-top:6px"><div style="width:${checklistProgress(e)}%"></div></div></div>
                ${statusBadge(e.status)}</li>`
            )
            .join('') || '<li class="empty">Rien en cours</li>'
        }</ul></div>
      <div class="card"><h3>✅ Tâches ${lateTasks.length ? `<span class="badge" style="background:var(--danger);color:#fff">${lateTasks.length} en retard</span>` : ''}</h3>
        <ul class="list">${[...lateTasks, ...soonTasks].map(taskLi).join('') || '<li class="empty">Aucune tâche</li>'}</ul>
        <p class="small muted" style="margin:10px 0 0">Durée totale publiée : ${fmtDuration(totalDuration) || '0:00'}</p></div>
    </div>`;
}

// ---------- Épisodes ----------

function filteredEpisodes() {
  const q = state.search.trim().toLowerCase();
  if (!q) return state.episodes;
  return state.episodes.filter((e) =>
    [e.title, e.description, e.notes, (e.tags || []).join(' '), guestNames(e.guestIds).join(' ')]
      .join(' ')
      .toLowerCase()
      .includes(q)
  );
}

function sortEpisodes(list) {
  return [...list].sort(
    (a, b) =>
      (Number(b.season) || 0) - (Number(a.season) || 0) ||
      (Number(b.number) || 0) - (Number(a.number) || 0) ||
      String(b.createdAt).localeCompare(String(a.createdAt))
  );
}

function epCard(e) {
  const g = guestNames(e.guestIds);
  const pct = checklistProgress(e);
  return `<div class="ep-card" draggable="true" data-ep="${e.id}">
    ${epLabel(e) ? `<div class="num">${esc(epLabel(e))}</div>` : ''}
    <div class="title">${esc(e.title || 'Sans titre')}</div>
    <div class="meta">
      ${g.length ? `<span>👤 ${esc(g.join(', '))}</span>` : ''}
      ${e.recordDate && e.status !== 'publie' ? `<span>🎙️ ${fmtDate(e.recordDate, true)}</span>` : ''}
      ${e.publishDate ? `<span>📢 ${fmtDate(e.publishDate, true)}</span>` : ''}
      ${e.audio ? `<span>🔊 Audio${e.duration ? ' · ' + fmtDuration(e.duration) : ''}</span>` : ''}
    </div>
    ${(e.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join('')}
    ${(e.checklist || []).length ? `<div class="progress" style="margin-top:8px" title="${pct}%"><div style="width:${pct}%"></div></div>` : ''}
  </div>`;
}

function episodes() {
  const list = sortEpisodes(filteredEpisodes());
  const head = `
    <div class="page-head"><h1>Épisodes</h1>
      <span class="muted">${state.episodes.length} au total</span>
      <div class="spacer"></div>
      <input type="search" id="ep-search" placeholder="Rechercher…" value="${esc(state.search)}" style="width:220px" />
      <div class="seg"><button data-epview="board" class="${state.episodeView === 'board' ? 'on' : ''}">Tableau</button><button data-epview="list" class="${state.episodeView === 'list' ? 'on' : ''}">Liste</button></div>
      <button class="primary" data-new-ep>＋ Nouvel épisode</button>
    </div>`;
  if (state.episodeView === 'list') {
    return (
      head +
      `<table><thead><tr><th>N°</th><th>Titre</th><th>Statut</th><th>Invités</th><th>Enregistrement</th><th>Publication</th><th>Durée</th></tr></thead><tbody>
      ${
        list
          .map(
            (e) => `<tr class="clickable" data-ep="${e.id}"><td class="muted">${esc(epLabel(e))}</td><td><strong>${esc(e.title || 'Sans titre')}</strong></td>
            <td>${statusBadge(e.status)}</td><td>${esc(guestNames(e.guestIds).join(', '))}</td>
            <td>${fmtDate(e.recordDate, true)}</td><td>${fmtDate(e.publishDate, true)}</td><td>${fmtDuration(e.duration)}</td></tr>`
          )
          .join('') || '<tr><td colspan="7" class="empty">Aucun épisode</td></tr>'
      }</tbody></table>`
    );
  }
  return (
    head +
    `<div class="board">${STATUSES.map((s) => {
      const items = list.filter((e) => (e.status || 'idee') === s.id);
      return `<div class="column" data-status="${s.id}">
        <div class="column-head"><span class="dot" style="background:var(--s-${s.id})"></span>${s.label}<span class="muted">${items.length}</span>
          <span style="flex:1"></span><button class="icon-btn" title="Ajouter" data-new-ep="${s.id}">＋</button></div>
        ${items.map(epCard).join('')}
      </div>`;
    }).join('')}</div>
    <p class="muted small">Astuce : glissez-déposez une carte pour changer son statut.</p>`
  );
}

function nextEpisodeNumber() {
  return Math.max(0, ...state.episodes.map((e) => Number(e.number) || 0)) + 1;
}

function openEpisode(id, defaults = {}) {
  const existing = state.episodes.find((e) => e.id === id);
  const e = existing
    ? structuredClone(existing)
    : {
        title: '',
        status: 'idee',
        number: nextEpisodeNumber(),
        season: Math.max(1, ...state.episodes.map((x) => Number(x.season) || 0)),
        guestIds: [],
        tags: [],
        checklist: DEFAULT_CHECKLIST.map((label) => ({ label, done: false })),
        ...defaults,
      };

  const renderChecklist = () =>
    e.checklist
      .map(
        (c, i) => `<label><input type="checkbox" data-ci="${i}" ${c.done ? 'checked' : ''}/> ${esc(c.label)}
        <button type="button" class="icon-btn rm" data-ci-rm="${i}" title="Retirer">✕</button></label>`
      )
      .join('');
  const renderAudio = () =>
    e.audio
      ? `<span class="small">${esc(e.audio.split('/').pop())}</span>
         <button type="button" class="icon-btn danger" data-rm-audio title="Retirer">✕</button>
         <audio controls preload="metadata" src="${esc(/^https?:/.test(e.audio) ? e.audio : '/' + e.audio)}"></audio>`
      : '<span class="muted small">Aucun fichier</span>';
  const renderCover = () =>
    e.cover
      ? `<img class="cover-preview" src="${esc(/^https?:/.test(e.cover) ? e.cover : '/' + e.cover)}" alt="" />
         <button type="button" class="icon-btn danger" data-rm-cover title="Retirer">✕</button>`
      : '<span class="muted small">Aucune image</span>';

  openModal({
    title: existing ? 'Modifier l’épisode' : 'Nouvel épisode',
    body: `
      <div class="grid g4">
        <label class="field span-all">Titre<input name="title" required value="${esc(e.title)}" placeholder="Titre de l’épisode" /></label>
        <label class="field">Saison<input name="season" type="number" min="0" value="${esc(e.season)}" /></label>
        <label class="field">Numéro<input name="number" type="number" min="0" value="${esc(e.number)}" /></label>
        <label class="field span2">Statut<select name="status">${STATUSES.map(
          (s) => `<option value="${s.id}" ${e.status === s.id ? 'selected' : ''}>${s.label}</option>`
        ).join('')}</select></label>
        <label class="field span2">Date d’enregistrement<input name="recordDate" type="datetime-local" value="${esc(e.recordDate || '')}" /></label>
        <label class="field span2">Date de publication<input name="publishDate" type="datetime-local" value="${esc(e.publishDate || '')}" /></label>
        <label class="field">Durée (h:mm:ss)<input name="duration" placeholder="45:30" value="${esc(fmtDurationInput(e.duration))}" /></label>
        <label class="field span2">Tags (séparés par des virgules)<input name="tags" value="${esc((e.tags || []).join(', '))}" /></label>
        <label class="field">Lien externe<input name="link" type="url" placeholder="https://…" value="${esc(e.link || '')}" /></label>
        <div class="field span-all"><span class="muted small" style="font-weight:500">Invités</span>
          <div class="guest-picks">${
            state.guests.length
              ? state.guests
                  .map(
                    (g) => `<label><input type="checkbox" name="guestIds" value="${g.id}" ${(e.guestIds || []).includes(g.id) ? 'checked' : ''}/> ${esc(g.name)}</label>`
                  )
                  .join('')
              : '<span class="muted small">Aucun invité — ajoutez-en depuis l’onglet Invités.</span>'
          }</div></div>
        <label class="field span-all">Description / notes d’épisode (publiques)<textarea name="description" placeholder="Résumé, liens cités, chapitres…">${esc(e.description || '')}</textarea></label>
        <label class="field span-all">Préparation / script / questions (privé)<textarea name="notes" style="min-height:140px">${esc(e.notes || '')}</textarea></label>
        <div class="field span2"><span class="muted small" style="font-weight:500">Fichier audio</span>
          <div class="file-row" id="audio-row">${renderAudio()}</div>
          <input type="file" id="audio-file" accept="audio/*" /></div>
        <div class="field span2"><span class="muted small" style="font-weight:500">Visuel de l’épisode</span>
          <div class="file-row" id="cover-row">${renderCover()}</div>
          <input type="file" id="cover-file" accept="image/*" /></div>
        <div class="field span-all"><span class="muted small" style="font-weight:500">Checklist de production</span>
          <div class="checklist" id="checklist">${renderChecklist()}</div>
          <div style="display:flex;gap:8px;margin-top:6px"><input id="new-check" placeholder="Ajouter une étape…" /><button type="button" id="add-check">Ajouter</button></div></div>
      </div>`,
    footer: `${existing ? '<button type="button" class="danger" data-delete>Supprimer</button>' : ''}<span class="spacer"></span>
      <button type="button" data-close>Annuler</button><button type="submit" class="primary">Enregistrer</button>`,
    onOpen(root) {
      const cl = $('#checklist', root);
      cl.addEventListener('change', (ev) => {
        if (ev.target.dataset.ci != null) e.checklist[ev.target.dataset.ci].done = ev.target.checked;
      });
      cl.addEventListener('click', (ev) => {
        const rm = ev.target.closest('[data-ci-rm]');
        if (rm) {
          e.checklist.splice(Number(rm.dataset.ciRm), 1);
          cl.innerHTML = renderChecklist();
        }
      });
      const addCheck = () => {
        const v = $('#new-check', root).value.trim();
        if (!v) return;
        e.checklist.push({ label: v, done: false });
        $('#new-check', root).value = '';
        cl.innerHTML = renderChecklist();
      };
      $('#add-check', root).onclick = addCheck;
      $('#new-check', root).addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
          ev.preventDefault();
          addCheck();
        }
      });

      $('#audio-file', root).onchange = async (ev) => {
        const file = ev.target.files[0];
        if (!file) return;
        $('#audio-row', root).innerHTML = '<span class="muted small">Envoi en cours…</span>';
        const up = await upload(file);
        e.audio = up.path;
        $('#audio-row', root).innerHTML = renderAudio();
        const audio = $('#audio-row audio', root);
        audio.addEventListener('loadedmetadata', () => {
          if (isFinite(audio.duration) && !parseDuration(root.querySelector('[name=duration]').value)) {
            root.querySelector('[name=duration]').value = fmtDurationInput(audio.duration);
          }
        });
        ev.target.value = '';
      };
      $('#cover-file', root).onchange = async (ev) => {
        const file = ev.target.files[0];
        if (!file) return;
        const up = await upload(file);
        e.cover = up.path;
        $('#cover-row', root).innerHTML = renderCover();
        ev.target.value = '';
      };
      root.addEventListener('click', (ev) => {
        if (ev.target.closest('[data-rm-audio]')) {
          e.audio = '';
          $('#audio-row', root).innerHTML = renderAudio();
        }
        if (ev.target.closest('[data-rm-cover]')) {
          e.cover = '';
          $('#cover-row', root).innerHTML = renderCover();
        }
      });
      $('[data-delete]', root.closest('form'))?.addEventListener('click', async () => {
        if (!confirm('Supprimer cet épisode et ses tâches associées ?')) return;
        await api('episodes/' + id, { method: 'DELETE' });
        closeModal();
        await refresh('Épisode supprimé');
      });
    },
    async onSubmit(form) {
      const fd = new FormData(form);
      const data = {
        title: fd.get('title').trim(),
        season: fd.get('season'),
        number: fd.get('number'),
        status: fd.get('status'),
        recordDate: fd.get('recordDate'),
        publishDate: fd.get('publishDate'),
        duration: parseDuration(fd.get('duration')),
        tags: fd.get('tags').split(',').map((t) => t.trim()).filter(Boolean),
        link: fd.get('link'),
        guestIds: fd.getAll('guestIds'),
        description: fd.get('description'),
        notes: fd.get('notes'),
        audio: e.audio || '',
        cover: e.cover || '',
        checklist: e.checklist,
      };
      if (existing) await api('episodes/' + id, { method: 'PUT', body: data });
      else await api('episodes', { method: 'POST', body: data });
      await refresh(existing ? 'Épisode mis à jour' : 'Épisode créé');
    },
  });
}

function fmtDurationInput(sec) {
  sec = Math.round(Number(sec) || 0);
  if (!sec) return '';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return (h ? `${h}:${String(m).padStart(2, '0')}` : `${m}`) + `:${String(s).padStart(2, '0')}`;
}

async function upload(file) {
  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      headers: { 'X-Filename': encodeURIComponent(file.name) },
      body: file,
    });
    if (!res.ok) throw new Error('Échec de l’envoi');
    toast('Fichier envoyé');
    return await res.json();
  } catch (err) {
    toast(err.message);
    throw err;
  }
}

// ---------- Calendrier ----------

function calendar() {
  const m = state.calMonth;
  const first = new Date(m.getFullYear(), m.getMonth(), 1);
  const start = new Date(first);
  start.setDate(1 - ((first.getDay() + 6) % 7)); // lundi
  const today = todayStr();
  const key = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;

  const events = {};
  const add = (date, ev) => (events[dateOnly(date)] ||= []).push(ev);
  for (const e of state.episodes) {
    if (e.recordDate) add(e.recordDate, { type: 'rec', e });
    if (e.publishDate) add(e.publishDate, { type: 'pub', e });
  }
  for (const t of state.tasks) if (t.due && !t.done) add(t.due, { type: 'task', t });

  let cells = '';
  for (let i = 0; i < 42; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    const k = key(d);
    cells += `<div class="day ${d.getMonth() !== m.getMonth() ? 'other' : ''} ${k === today ? 'today' : ''}">
      <span class="d">${d.getDate()}</span>
      ${(events[k] || [])
        .map((ev) =>
          ev.type === 'task'
            ? `<div class="ev" style="background:var(--muted)" title="Tâche : ${esc(ev.t.title)}" data-goto-tasks>☐ ${esc(ev.t.title)}</div>`
            : `<div class="ev" data-ep="${ev.e.id}" style="background:var(--s-${ev.type === 'rec' ? 'enregistre' : 'publie'})" title="${esc(ev.e.title)}">${ev.type === 'rec' ? '🎙️' : '📢'} ${esc(ev.e.title || 'Sans titre')}</div>`
        )
        .join('')}
    </div>`;
  }
  const monthName = m.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
  return `
    <div class="page-head"><h1>Calendrier éditorial</h1><div class="spacer"></div>
      <button data-cal="-1">‹</button><strong style="min-width:150px;text-align:center;text-transform:capitalize">${monthName}</strong><button data-cal="1">›</button>
      <button data-cal="0">Aujourd’hui</button></div>
    <p class="small muted" style="margin-top:-10px">🎙️ enregistrement · 📢 publication · ☐ tâche</p>
    <div class="cal">${['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((d) => `<div class="dow">${d}</div>`).join('')}${cells}</div>`;
}

// ---------- Invités ----------

function guests() {
  const list = [...state.guests].sort((a, b) => (a.name || '').localeCompare(b.name || '', 'fr'));
  return `
    <div class="page-head"><h1>Invités</h1><span class="muted">${list.length}</span><div class="spacer"></div>
      <button class="primary" data-new-guest>＋ Nouvel invité</button></div>
    <table><thead><tr><th>Nom</th><th>Statut</th><th>Contact</th><th>Sujet</th><th>Épisodes</th></tr></thead><tbody>
    ${
      list
        .map((g) => {
          const eps = state.episodes.filter((e) => (e.guestIds || []).includes(g.id));
          return `<tr class="clickable" data-guest="${g.id}">
            <td><strong>${esc(g.name)}</strong>${g.role ? `<div class="muted small">${esc(g.role)}</div>` : ''}</td>
            <td><span class="badge">${esc(GUEST_STATUS[g.status]?.label || '—')}</span></td>
            <td class="small">${g.email ? esc(g.email) + '<br>' : ''}${g.phone ? esc(g.phone) + '<br>' : ''}${g.social ? esc(g.social) : ''}</td>
            <td class="small">${esc(g.topic || '')}</td>
            <td class="small">${eps.map((e) => esc(e.title || 'Sans titre')).join('<br>') || '<span class="muted">—</span>'}</td></tr>`;
        })
        .join('') || '<tr><td colspan="5" class="empty">Aucun invité pour l’instant</td></tr>'
    }</tbody></table>`;
}

function openGuest(id) {
  const existing = state.guests.find((g) => g.id === id);
  const g = existing || { status: 'a_contacter' };
  openModal({
    title: existing ? 'Modifier l’invité' : 'Nouvel invité',
    body: `<div class="grid g2">
      <label class="field">Nom<input name="name" required value="${esc(g.name || '')}" /></label>
      <label class="field">Fonction / activité<input name="role" value="${esc(g.role || '')}" /></label>
      <label class="field">Email<input name="email" type="email" value="${esc(g.email || '')}" /></label>
      <label class="field">Téléphone<input name="phone" value="${esc(g.phone || '')}" /></label>
      <label class="field">Réseaux / site<input name="social" value="${esc(g.social || '')}" placeholder="@pseudo, https://…" /></label>
      <label class="field">Statut<select name="status">${GUEST_STATUSES.map(
        (s) => `<option value="${s.id}" ${g.status === s.id ? 'selected' : ''}>${s.label}</option>`
      ).join('')}</select></label>
      <label class="field span2">Sujet proposé<input name="topic" value="${esc(g.topic || '')}" /></label>
      <label class="field span2">Bio<textarea name="bio">${esc(g.bio || '')}</textarea></label>
      <label class="field span2">Notes (échanges, disponibilités…)<textarea name="notes">${esc(g.notes || '')}</textarea></label>
    </div>`,
    footer: `${existing ? '<button type="button" class="danger" data-delete>Supprimer</button>' : ''}<span class="spacer"></span>
      <button type="button" data-close>Annuler</button><button type="submit" class="primary">Enregistrer</button>`,
    onOpen(root) {
      $('[data-delete]', root.closest('form'))?.addEventListener('click', async () => {
        if (!confirm('Supprimer cet invité ?')) return;
        await api('guests/' + id, { method: 'DELETE' });
        closeModal();
        await refresh('Invité supprimé');
      });
    },
    async onSubmit(form) {
      const data = Object.fromEntries(new FormData(form));
      if (existing) await api('guests/' + id, { method: 'PUT', body: data });
      else await api('guests', { method: 'POST', body: data });
      await refresh(existing ? 'Invité mis à jour' : 'Invité ajouté');
    },
  });
}

// ---------- Tâches ----------

function tasks() {
  const today = todayStr();
  let list = [...state.tasks];
  if (state.taskFilter === 'open') list = list.filter((t) => !t.done);
  if (state.taskFilter === 'done') list = list.filter((t) => t.done);
  list.sort((a, b) => Number(a.done) - Number(b.done) || (a.due || '9999').localeCompare(b.due || '9999'));
  const epOptions = sortEpisodes(state.episodes)
    .filter((e) => e.status !== 'publie')
    .map((e) => `<option value="${e.id}">${esc((epLabel(e) ? epLabel(e) + ' — ' : '') + (e.title || 'Sans titre'))}</option>`)
    .join('');
  return `
    <div class="page-head"><h1>Tâches</h1><div class="spacer"></div>
      <div class="seg">${[
        ['open', 'À faire'],
        ['done', 'Terminées'],
        ['all', 'Toutes'],
      ]
        .map(([k, l]) => `<button data-tfilter="${k}" class="${state.taskFilter === k ? 'on' : ''}">${l}</button>`)
        .join('')}</div></div>
    <form class="card grid" id="task-form" style="grid-template-columns: 1fr 170px 220px auto; margin-bottom:16px; align-items:end">
      <label class="field">Nouvelle tâche<input name="title" required placeholder="Ex : envoyer les questions à l’invité" /></label>
      <label class="field">Échéance<input name="due" type="date" /></label>
      <label class="field">Épisode lié<select name="episodeId"><option value="">—</option>${epOptions}</select></label>
      <button class="primary">Ajouter</button>
    </form>
    <div class="card"><ul class="list">
      ${
        list
          .map((t) => {
            const ep = state.episodes.find((e) => e.id === t.episodeId);
            return `<li class="task-row ${t.done ? 'done' : ''}">
              <input type="checkbox" data-task-done="${t.id}" ${t.done ? 'checked' : ''} />
              <div class="grow">${esc(t.title)}${ep ? `<div class="muted small clickable" data-ep="${ep.id}">🎧 ${esc(ep.title || 'Sans titre')}</div>` : ''}</div>
              ${t.due ? `<span class="small ${!t.done && t.due < today ? 'overdue' : 'muted'}">${fmtDate(t.due)}</span>` : ''}
              <button class="icon-btn danger" data-task-rm="${t.id}" title="Supprimer">✕</button></li>`;
          })
          .join('') || '<li class="empty">Rien ici 🎉</li>'
      }</ul></div>`;
}

// ---------- Paramètres ----------

function settings() {
  const s = state.settings;
  const rss = `${location.origin}/rss.xml`;
  return `
    <div class="page-head"><h1>Paramètres</h1></div>
    <form class="card grid g2" id="settings-form" style="margin-bottom:16px">
      <h3 class="span2">Informations du podcast</h3>
      <label class="field">Titre<input name="title" value="${esc(s.title)}" /></label>
      <label class="field">Auteur / animateur<input name="author" value="${esc(s.author)}" /></label>
      <label class="field">Email de contact<input name="email" type="email" value="${esc(s.email)}" /></label>
      <label class="field">Site web<input name="website" type="url" value="${esc(s.website)}" /></label>
      <label class="field">Langue<input name="language" value="${esc(s.language)}" /></label>
      <label class="field">Catégorie (Apple Podcasts)<input name="category" value="${esc(s.category)}" /></label>
      <label class="field span2">Description<textarea name="description">${esc(s.description)}</textarea></label>
      <div class="field"><span class="muted small" style="font-weight:500">Pochette du podcast</span>
        <div class="file-row" id="pod-cover">${s.cover ? `<img class="cover-preview" src="/${esc(s.cover)}" alt="" />` : '<span class="muted small">Aucune image</span>'}</div>
        <input type="file" id="pod-cover-file" accept="image/*" /></div>
      <div class="field">
        <label class="field">URL publique (pour le flux RSS)<input name="publicUrl" value="${esc(s.publicUrl)}" /></label>
        <label style="display:flex;gap:8px;align-items:center;margin-top:10px"><input type="checkbox" name="explicit" ${s.explicit ? 'checked' : ''}/> Contenu explicite</label>
      </div>
      <div class="span2"><button class="primary">Enregistrer</button></div>
    </form>
    <div class="grid g2">
      <div class="card"><h3>📡 Flux RSS</h3>
        <p class="small muted">Généré automatiquement à partir des épisodes au statut « Publié » ayant un fichier audio.</p>
        <div style="display:flex;gap:8px"><input readonly value="${esc(rss)}" id="rss-url" /><button type="button" id="copy-rss">Copier</button></div>
        <p><a href="/rss.xml" target="_blank">Ouvrir le flux ↗</a></p></div>
      <div class="card"><h3>💾 Sauvegarde</h3>
        <p class="small muted">Exportez toutes vos données (épisodes, invités, tâches, paramètres) dans un fichier JSON, ou restaurez une sauvegarde. Les fichiers audio/images restent dans <code>data/uploads</code>.</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap"><a class="btn" href="/api/export">⬇️ Exporter</a>
          <label class="btn">⬆️ Importer<input type="file" id="import-file" accept="application/json" hidden /></label></div></div>
    </div>`;
}

// ---------- Liaisons d'événements par vue ----------

const bind = {
  episodes() {
    $('#ep-search').addEventListener('input', (ev) => {
      state.search = ev.target.value;
      const pos = ev.target.selectionStart;
      render();
      const input = $('#ep-search');
      input.focus();
      input.setSelectionRange(pos, pos);
    });
    let dragId = null;
    $$('.ep-card').forEach((c) => {
      c.addEventListener('dragstart', (ev) => {
        dragId = c.dataset.ep;
        c.classList.add('dragging');
        ev.dataTransfer.effectAllowed = 'move';
      });
      c.addEventListener('dragend', () => c.classList.remove('dragging'));
    });
    $$('.column').forEach((col) => {
      col.addEventListener('dragover', (ev) => {
        ev.preventDefault();
        col.classList.add('drop');
      });
      col.addEventListener('dragleave', () => col.classList.remove('drop'));
      col.addEventListener('drop', async (ev) => {
        ev.preventDefault();
        col.classList.remove('drop');
        const ep = state.episodes.find((e) => e.id === dragId);
        if (!ep || ep.status === col.dataset.status) return;
        const patch = { status: col.dataset.status };
        if (patch.status === 'publie' && !ep.publishDate) patch.publishDate = new Date().toISOString().slice(0, 16);
        await api('episodes/' + ep.id, { method: 'PUT', body: patch });
        await refresh(`→ ${STATUS[patch.status].label}`);
      });
    });
  },
  tasks() {
    $('#task-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const data = Object.fromEntries(new FormData(ev.target));
      await api('tasks', { method: 'POST', body: { ...data, done: false } });
      await refresh('Tâche ajoutée');
    });
  },
  settings() {
    $('#settings-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const data = Object.fromEntries(new FormData(ev.target));
      data.explicit = ev.target.explicit.checked;
      await api('settings', { method: 'PUT', body: data });
      await refresh('Paramètres enregistrés');
    });
    $('#pod-cover-file').onchange = async (ev) => {
      const file = ev.target.files[0];
      if (!file) return;
      const up = await upload(file);
      await api('settings', { method: 'PUT', body: { cover: up.path } });
      await refresh('Pochette mise à jour');
    };
    $('#copy-rss').onclick = () => {
      navigator.clipboard?.writeText($('#rss-url').value);
      toast('Lien copié');
    };
    $('#import-file').onchange = async (ev) => {
      const file = ev.target.files[0];
      if (!file) return;
      if (!confirm('Remplacer toutes les données actuelles par cette sauvegarde ?')) return;
      try {
        await api('import', { method: 'POST', body: JSON.parse(await file.text()) });
        await refresh('Sauvegarde restaurée');
      } catch (err) {
        toast('Import impossible : ' + err.message);
      }
    };
  },
};

// Délégation globale des clics
document.addEventListener('click', async (ev) => {
  const t = ev.target;
  if (t.closest('dialog')) return;
  const newEp = t.closest('[data-new-ep]');
  if (newEp) return openEpisode(null, newEp.dataset.newEp ? { status: newEp.dataset.newEp } : {});
  const ep = t.closest('[data-ep]');
  if (ep && !t.matches('input')) return openEpisode(ep.dataset.ep);
  if (t.closest('[data-new-guest]')) return openGuest(null);
  const g = t.closest('[data-guest]');
  if (g) return openGuest(g.dataset.guest);
  const view = t.closest('[data-epview]');
  if (view) {
    state.episodeView = view.dataset.epview;
    localStorage.setItem('episodeView', state.episodeView);
    return render();
  }
  const cal = t.closest('[data-cal]');
  if (cal) {
    const d = Number(cal.dataset.cal);
    const m = state.calMonth;
    state.calMonth = d ? new Date(m.getFullYear(), m.getMonth() + d, 1) : new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    return render();
  }
  if (t.closest('[data-goto-tasks]')) return (location.hash = 'tasks');
  const tf = t.closest('[data-tfilter]');
  if (tf) {
    state.taskFilter = tf.dataset.tfilter;
    return render();
  }
  const rm = t.closest('[data-task-rm]');
  if (rm) {
    await api('tasks/' + rm.dataset.taskRm, { method: 'DELETE' });
    return refresh('Tâche supprimée');
  }
});

document.addEventListener('change', async (ev) => {
  const id = ev.target.dataset?.taskDone;
  if (!id || ev.target.closest('dialog')) return;
  await api('tasks/' + id, { method: 'PUT', body: { done: ev.target.checked } });
  await refresh();
});

// ---------- Modale ----------

let modalHandlers = null;

function openModal({ title, body, footer, onOpen, onSubmit }) {
  const dlg = $('#modal');
  $('#modal-title').textContent = title;
  $('#modal-body').innerHTML = body;
  $('#modal-footer').innerHTML = footer;
  modalHandlers = { onSubmit };
  dlg.showModal();
  onOpen?.($('#modal-body'));
  $('#modal-body input:not([type=checkbox])')?.focus();
}

function closeModal() {
  $('#modal').close();
  modalHandlers = null;
}

$('#modal-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  if (!modalHandlers?.onSubmit) return closeModal();
  try {
    await modalHandlers.onSubmit($('#modal-form'));
    closeModal();
  } catch (err) {
    toast(err.message);
  }
});
$('#modal').addEventListener('click', (ev) => {
  if (ev.target.closest('[data-close]')) closeModal();
});

async function refresh(msg) {
  await loadAll();
  render();
  if (msg) toast(msg);
}

refresh().catch((err) => {
  $('#view').innerHTML = `<div class="card">Impossible de joindre le serveur : ${esc(err.message)}</div>`;
});
