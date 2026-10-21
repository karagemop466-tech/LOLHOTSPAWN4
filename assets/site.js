'use strict';
// Static-first: the published HTML contains every row and original source.
// JavaScript adds only local filtering, pagination, view switching and expiry.
(() => {
  const $ = (id) => document.getElementById(id);
  const expire = () => {
    const now = Date.now();
    const observed = Date.parse(document.body.dataset.inventoryAt || '');
    const stale = !Number.isFinite(observed) || now - observed > 8 * 60 * 60 * 1000;
    if ($('freshness-warning')) $('freshness-warning').hidden = !stale;
    for (const row of document.querySelectorAll('[data-has-probability="true"]')) {
      const until = Date.parse(row.dataset.validUntil || '');
      if (!stale && Number.isFinite(until) && now < until) continue;
      if (row.dataset.invalidated === 'true') continue;
      row.dataset.invalidated = 'true';
      row.classList.add('invalidated');
      for (const value of row.querySelectorAll('.current-probability')) {
        value.textContent = '—';
        value.setAttribute('aria-label', 'Unconfirmed now; refresh required');
      }
      for (const pick of row.querySelectorAll('.current-pick')) pick.textContent = 'Refresh required · no current pick';
      const bar = row.querySelector('.prob-bar');
      if (bar) bar.hidden = true;
    }
  };
  expire();
  window.setInterval(expire, 60000);

  const cards = [...document.querySelectorAll('#match-cards > [data-match-id]')];
  if (!cards.length) return;
  const tableRows = [...document.querySelectorAll('#match-table tbody > [data-match-id]')];
  const search = $('match-search');
  const competition = $('competition-filter');
  const state = $('state-filter');
  const pageSize = 24;
  let page = 0;
  let view = 'cards';
  let filtered = cards;
  const clean = (v) => String(v).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  const paint = () => {
    const query = clean(search.value.trim());
    filtered = cards.filter((card) => (!query || clean(card.dataset.search).includes(query)) &&
      (!competition.value || card.dataset.competition === competition.value) &&
      (!state.value || card.dataset.state === state.value));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    page = Math.min(Math.max(0, page), pages - 1);
    const current = filtered.slice(page * pageSize, (page + 1) * pageSize);
    const visible = new Set(current.map((card) => card.dataset.matchId));
    for (const card of cards) card.hidden = !visible.has(card.dataset.matchId);
    for (const row of tableRows) row.hidden = !visible.has(row.dataset.matchId);
    $('match-cards').hidden = view !== 'cards';
    $('match-table').hidden = view !== 'table';
    $('cards-view').setAttribute('aria-pressed', String(view === 'cards'));
    $('table-view').setAttribute('aria-pressed', String(view === 'table'));
    const start = filtered.length ? page * pageSize + 1 : 0;
    const end = Math.min((page + 1) * pageSize, filtered.length);
    $('result-count').textContent = `${start}–${end} of ${filtered.length} matches`;
    $('page-count').textContent = `Page ${page + 1} of ${pages}`;
    $('previous-page').disabled = page === 0;
    $('next-page').disabled = page >= pages - 1;
    $('no-results').hidden = filtered.length > 0;
  };
  const reset = () => { page = 0; paint(); };
  search.addEventListener('input', reset);
  competition.addEventListener('change', reset);
  state.addEventListener('change', reset);
  $('cards-view').addEventListener('click', () => { view = 'cards'; paint(); });
  $('table-view').addEventListener('click', () => { view = 'table'; paint(); });
  $('previous-page').addEventListener('click', () => { page -= 1; paint(); });
  $('next-page').addEventListener('click', () => { page += 1; paint(); });
  const revealHash = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!id.startsWith('match-')) return;
    const index = cards.findIndex((card) => card.id === id);
    if (index < 0) return;
    search.value = ''; competition.value = ''; state.value = '';
    page = Math.floor(index / pageSize);
    view = 'cards';
    paint();
    const target = cards[index];
    target.scrollIntoView({ block: 'start', behavior: 'instant' });
  };
  window.addEventListener('hashchange', revealHash);
  for (const anchor of document.querySelectorAll('.table-match-link')) {
    anchor.addEventListener('click', () => { view = 'cards'; paint(); });
  }
  paint();
  revealHash();
})();
