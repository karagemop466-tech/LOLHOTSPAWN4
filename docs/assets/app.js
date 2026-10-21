// Hotspawn League of Legends Picks Dashboard Frontend
let GLOBAL_DATA = null;
let CURRENT_VIEW = 'cards'; // 'cards' or 'table'

async function fetchPicksData() {
  const candidates = ['data/picks.json', './data/picks.json', '../data/picks.json'];
  for (const url of candidates) {
    try {
      const resp = await fetch(url, { cache: 'no-store' });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (e) {
      // try next candidate
    }
  }
  throw new Error("Unable to load picks.json data file.");
}

function formatPercent(val) {
  if (val === null || val === undefined) return "50%";
  return Math.round(val * 100) + "%";
}

function formatDate(isoStr, rawStr) {
  if (!isoStr && !rawStr) return "Scheduled";
  if (isoStr) {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {}
  }
  return rawStr || "Scheduled";
}

function getMethodBadge(method) {
  switch (method) {
    case 'MARKET_BOOKS':
      return '<span class="meta-badge market">💰 Esportsbook Line</span>';
    case 'MARKET_POLYMARKET':
      return '<span class="meta-badge market">💰 Polymarket Line</span>';
    case 'MODEL_ELO':
      return '<span class="meta-badge model">🧮 Our Elo Model</span>';
    case 'UNRESOLVED':
    default:
      return '<span class="meta-badge unresolved">⚠️ Unresolved (50/50)</span>';
  }
}

function getCardClass(method) {
  if (method && method.startsWith('MARKET')) return 'market';
  if (method === 'MODEL_ELO') return 'model';
  return 'unresolved';
}

function renderCard(m) {
  const p1 = Math.round((m.prob_team1 || 0.5) * 100);
  const p2 = 100 - p1;
  const isP1Fav = p1 >= p2;
  const isCoinflip = p1 === p2;
  const cardClass = getCardClass(m.method);
  
  const formattedStart = formatDate(m.start_utc, m.start_raw);
  const tierDisplay = m.tier ? `Tier ${m.tier}` : 'Tier ?';
  const pointsDisplay = m.points ? `${m.points} pts` : '10 pts';
  
  // Official source link
  let sourceLinkHtml = '';
  if (m.market_url) {
    sourceLinkHtml = `<a href="${m.market_url}" target="_blank" rel="noopener">Betting Market ↗</a>`;
  } else if (m.source_url) {
    sourceLinkHtml = `<a href="${m.source_url}" target="_blank" rel="noopener">Source Wiki ↗</a>`;
  }
  
  let hotspawnLinkHtml = '';
  if (m.hotspawn_url) {
    hotspawnLinkHtml = `<a href="${m.hotspawn_url}" target="_blank" rel="noopener">Hotspawn Match ↗</a>`;
  }

  return `
  <article class="match-card ${cardClass}" data-team1="${m.team1}" data-team2="${m.team2}" data-tournament="${m.tournament}">
    <div class="card-header">
      <div>
        <span class="tournament">${m.tournament || 'League of Legends'}</span>
        <span> · ${formattedStart}</span>
      </div>
      <div>
        <span class="tier-badge">${tierDisplay} · ${pointsDisplay}</span>
      </div>
    </div>
    
    <div class="match-teams">
      <div class="team-box home">
        <span class="team-name">${m.team1}</span>
        <span class="team-prob ${isP1Fav && !isCoinflip ? 'fav' : ''}">${p1}%</span>
      </div>
      <div class="vs-badge">VS</div>
      <div class="team-box away">
        <span class="team-name">${m.team2}</span>
        <span class="team-prob ${!isP1Fav && !isCoinflip ? 'fav' : ''}">${p2}%</span>
      </div>
    </div>
    
    <div class="prob-bar" role="progressbar" aria-label="Win probability: ${m.team1} ${p1}%, ${m.team2} ${p2}%">
      <div class="fill-left" style="width: ${p1}%;"></div>
      <div class="fill-right" style="width: ${p2}%;"></div>
    </div>
    
    <div class="pick-badge-container">
      <div class="pick-title">🎯 Model Pick</div>
      <div class="pick-winner ${isCoinflip ? 'coinflip' : ''}">
        ${isCoinflip ? '⚖️ 50/50 Split (No Edge)' : `✅ ${m.pick} (${Math.round((m.pick_prob || 0.5) * 100)}%)`}
      </div>
    </div>
    
    <div class="card-footer-meta">
      ${getMethodBadge(m.method)}
      <span class="meta-badge" style="background:#1e2943; color:#cbd5e1;">${m.confidence || 'Standard'}</span>
      <div style="margin-left:auto; display:flex; gap:10px;">
        ${sourceLinkHtml}
        ${hotspawnLinkHtml}
      </div>
    </div>
  </article>`;
}

function renderTableRow(m) {
  const p1 = Math.round((m.prob_team1 || 0.5) * 100);
  const p2 = 100 - p1;
  const formattedStart = formatDate(m.start_utc, m.start_raw);
  
  let sourceLinkHtml = '—';
  if (m.market_url) {
    sourceLinkHtml = `<a href="${m.market_url}" target="_blank" rel="noopener">Market ↗</a>`;
  } else if (m.source_url) {
    sourceLinkHtml = `<a href="${m.source_url}" target="_blank" rel="noopener">Source ↗</a>`;
  }
  
  let hotspawnLink = m.hotspawn_url ? `<a href="${m.hotspawn_url}" target="_blank" rel="noopener">Match ↗</a>` : '—';

  return `
  <tr>
    <td><b>${formattedStart}</b></td>
    <td>${m.tournament || 'LoL'}</td>
    <td><span class="tier-badge" style="font-size:0.75rem;">${m.tier || '?'}</span></td>
    <td><b>${m.team1}</b> (${p1}%) vs <b>${m.team2}</b> (${p2}%)</td>
    <td class="table-pick-highlight">✅ ${m.pick} (${Math.round((m.pick_prob || 0.5)*100)}%)</td>
    <td>${getMethodBadge(m.method)}</td>
    <td><small>${m.confidence || '—'}</small></td>
    <td>${sourceLinkHtml}</td>
    <td>${hotspawnLink}</td>
  </tr>`;
}

function switchView(viewType) {
  CURRENT_VIEW = viewType;
  const cardsContainer = document.getElementById('cards-container');
  const tableContainer = document.getElementById('table-container');
  const btnCards = document.getElementById('btn-view-cards');
  const btnTable = document.getElementById('btn-view-table');

  if (viewType === 'table') {
    if (cardsContainer) cardsContainer.classList.add('hidden');
    if (tableContainer) tableContainer.classList.remove('hidden');
    if (btnCards) btnCards.classList.remove('active');
    if (btnTable) btnTable.classList.add('active');
  } else {
    if (cardsContainer) cardsContainer.classList.remove('hidden');
    if (tableContainer) tableContainer.classList.add('hidden');
    if (btnCards) btnCards.classList.add('active');
    if (btnTable) btnTable.classList.remove('active');
  }
}
