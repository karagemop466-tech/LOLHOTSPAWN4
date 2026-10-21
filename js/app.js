/* LOL Hotspawn Pick Desk - renders data/matches.json on each page.
   No external dependencies; everything is local to the site. */
(function () {
  "use strict";

  var DATA_URL = "data/matches.json";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pct(p) {
    if (p == null || isNaN(p)) return null;
    return (Math.round(p * 1000) / 10).toString().replace(/\.0$/, "") + "%";
  }
  function fmtUTC(iso) {
    if (!iso) return "time TBA";
    var d = new Date(iso);
    if (isNaN(d)) return "time TBA";
    var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    return months[d.getUTCMonth()] + " " + d.getUTCDate() + ", " +
      String(d.getUTCHours()).padStart(2, "0") + ":" + String(d.getUTCMinutes()).padStart(2, "0") + " UTC";
  }
  function lockLabel(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d)) return "";
    var ms = d - Date.now();
    if (ms <= 0) return "picks locked";
    var h = Math.floor(ms / 3600000), m = Math.floor((ms % 3600000) / 60000);
    if (h >= 48) return "locks " + fmtUTC(iso);
    return "picks lock in " + h + "h " + String(m).padStart(2, "0") + "m (" + fmtUTC(iso) + ")";
  }
  function basisBadge(b) {
    if (b === "market-line") return '<span class="badge basis-line">Market line</span>';
    if (b === "derived-estimate") return '<span class="badge basis-derived">Derived (our line)</span>';
    return '<span class="badge unresolved">No external market</span>';
  }

  function matchCard(m) {
    var pa = m.prob_team_a, pb = m.prob_team_b;
    var hasProbs = pa != null && pb != null;
    var favA = hasProbs && pa > pb;
    var favB = hasProbs && pb > pa;

    function team(mo, p, fav) {
      var bar = hasProbs ? '<div class="bar"><i style="width:' + Math.round(p * 100) + '%"></i></div>' : "";
      var pick = fav ? '<span class="picktag">Pick</span>' : "";
      var name = esc(mo.name);
      var logo = mo.logo_url ? '<img src="' + esc(mo.logo_url) + '" alt="" loading="lazy" onerror="this.remove()">' : "";
      return '<div class="team' + (fav ? " fav" : "") + '">' +
        '<div class="name">' + logo + "<span>" + name + "</span>" + pick + "</div>" +
        (hasProbs ? '<div class="sub"><span class="pct">' + pct(p) + "</span> win prob</div>" + bar :
          '<div class="sub">no verified line</div>') +
        "</div>";
    }

    var lineHtml = (m.lines || []).map(function (l) {
      var label = l.source + " · " + l.kind;
      if (l.kind === "match-winner-market") label = "Polymarket match market";
      if (l.kind === "derived-estimate") label = "Our derived line (futures ratio model)";
      if (l.kind === "derived-estimate-input") return ""; // covered by derived line
      if (l.kind === "listed-matchup-coverage") label = "Pinnacle lists a line (no public price)";
      var href = l.url || l.api_url;
      var when = l.fetched_at ? "fetched " + esc(l.fetched_at.slice(0, 16)) : "";
      if (!href) return "<span>" + esc(label) + " " + esc(when) + "</span>";
      return '<a href="' + esc(href) + '" target="_blank" rel="noopener">' + esc(label) + "</a>" +
        (when ? " <span>" + esc(when) + "</span>" : "");
    }).filter(Boolean).join(" · ");

    var pin = m.pinnacle_covered ? ' <span class="badge pin">Pinnacle lists it</span>' : "";
    var unres = !hasProbs
      ? '<div class="unresolved-banner">No verified external market found for this match — ' +
        'pick intentionally left blank. See <a href="flagged.html">Flagged for Review</a>.</div>'
      : "";
    var note = m.pick_note ? '<div class="note">' + esc(m.pick_note) + "</div>" : "";
    var stale = (m.lines || []).some(function (l) { return l.stale; });

    return '<article class="card match" data-basis="' + esc(m.pick_basis || "unresolved") + '">' +
      '<div class="meta">' +
        '<span class="tourney">' + esc(m.tournament || "Tournament TBA") + "</span>" +
        "<span>" + fmtUTC(m.start_utc) + "</span>" +
        "<span>" + lockLabel(m.lock_utc) + "</span>" +
        (m.tier && m.tier !== "waiting for information" ? '<span class="badge tier">Tier ' + esc(String(m.tier).toUpperCase()) + "</span>" : "") +
        (m.stage && m.stage !== "waiting for information" ? '<span class="badge tier">' + esc(m.stage) + "</span>" : "") +
        (m.offered_points ? '<span class="badge tier">' + esc(m.offered_points) + " pts</span>" : "") +
        pin + (stale ? ' <span class="badge tier">stale data</span>' : "") +
      "</div>" +
      basisBadge(m.pick_basis) +
      '<div class="teamrow" style="margin-top:10px">' +
      team(m.team_a, pa, favA) + team(m.team_b, pb, favB) +
      "</div>" +
      unres +
      (lineHtml ? '<div class="lines">' + lineHtml + "</div>" : "") +
      note +
      '</article>';
  }

  function staleBanners(data) {
    var out = "";
    Object.keys(data.sources || {}).forEach(function (k) {
      var s = data.sources[k];
      if (s.stale) out += '<div class="stale-banner">WARNING: ' + esc(s.name) +
        " data is STALE (fetch failed on last refresh; showing previous snapshot from " +
        esc(s.fetched_at || "?") + ").</div>";
    });
    return out;
  }

  function renderAllMatches(data, rootSel) {
    var root = $(rootSel);
    if (!root) return;
    if (!data.matches || !data.matches.length) {
      root.innerHTML = '<div class="loading">No matches in the dataset. The refresh workflow may still be running.</div>';
      return;
    }
    root.innerHTML = data.matches.map(matchCard).join("");
    // summary chips
    var s = data.summary || {};
    var chips = $("#summaryChips");
    if (chips) {
      chips.innerHTML =
        '<span class="chip">Matches <b>' + (s.total_matches || 0) + "</b></span>" +
        '<span class="chip ok">Market line <b>' + (s.market_line || 0) + "</b></span>" +
        '<span class="chip warn">Derived <b>' + (s.derived_estimate || 0) + "</b></span>" +
        '<span class="chip bad">Unresolved <b>' + (s.unresolved || 0) + "</b></span>" +
        '<span class="chip">Pinnacle coverage <b>' + (s.pinnacle_covered || 0) + "</b></span>" +
        '<span class="chip">Updated <b>' + esc((data.generated_at || "").slice(0, 16)) + " UTC</b></span>";
    }
    var up = $("#updatedStamp");
    if (up) up.textContent = "Updated " + (data.generated_at || "unknown") + " (auto-refresh every 4 hours)";
  }

  function setFilters(rootSel) {
    var root = $(rootSel);
    if (!root) return;
    var active = "all";
    document.querySelectorAll(".filters button").forEach(function (b) {
      b.addEventListener("click", function () {
        active = b.getAttribute("data-filter");
        document.querySelectorAll(".filters button").forEach(function (x) {
          x.classList.toggle("active", x === b);
        });
        root.querySelectorAll(".match").forEach(function (card) {
          var basis = card.getAttribute("data-basis");
          var show =
            active === "all" ||
            (active === "line" && basis === "market-line") ||
            (active === "derived" && basis === "derived-estimate") ||
            (active === "unresolved" && basis === "unresolved");
          card.style.display = show ? "" : "none";
        });
      });
    });
  }

  window.PickDesk = {
    load: function (done) {
      var doneOnce = false;
      function finish(err, data) {
        if (doneOnce) return;
        doneOnce = true;
        done(err, data);
      }
      fetch(DATA_URL, { cache: "no-store" })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status + " loading " + DATA_URL);
          return r.json();
        })
        .then(function (d) { finish(null, d); })
        .catch(function (e) { finish(e, null); });
    },
    renderAllMatches: renderAllMatches,
    setFilters: setFilters,
    staleBanners: staleBanners,
    esc: esc, pct: pct, fmtUTC: fmtUTC,
    matchCard: matchCard,
  };
})();
