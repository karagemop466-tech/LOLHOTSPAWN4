document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("match-search");
  const tournSelect = document.getElementById("tourn-filter");
  const filterBtns = document.querySelectorAll(".filter-btn[data-filter-group]");
  const countEl = document.getElementById("visible-count");
  const rows = Array.from(document.querySelectorAll("tr.match-row"));

  let state = {
    section: "ALL",
    confidence: "ALL",
    special: "ALL"
  };

  function applyFilters() {
    if (!rows.length) return;
    const q = (searchInput ? searchInput.value : "").trim().toLowerCase();
    const t = tournSelect ? tournSelect.value : "ALL";
    let visible = 0;

    rows.forEach((row) => {
      const rSec = row.getAttribute("data-section");
      const rTourn = row.getAttribute("data-tournament");
      const rConf = row.getAttribute("data-confidence");
      const rFlag = row.getAttribute("data-flagged");
      const rEdge = parseFloat(row.getAttribute("data-edge") || "0");
      const rSearch = row.getAttribute("data-search") || "";

      let ok = true;
      if (state.section !== "ALL" && rSec !== state.section) ok = false;
      if (t !== "ALL" && rTourn !== t) ok = false;
      if (state.confidence !== "ALL" && rConf !== state.confidence) ok = false;
      if (state.special === "CONTRARIAN" && rEdge < 15.0) ok = false;
      if (state.special === "FLAGGED" && rFlag !== "true") ok = false;
      if (q && !rSearch.includes(q)) ok = false;

      row.style.display = ok ? "" : "none";
      if (ok) visible++;
    });

    if (countEl) countEl.textContent = visible;
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (tournSelect) tournSelect.addEventListener("change", applyFilters);

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const grp = btn.getAttribute("data-filter-group");
      const val = btn.getAttribute("data-filter-val");
      document.querySelectorAll(`.filter-btn[data-filter-group="${grp}"]`).forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state[grp] = val;
      applyFilters();
    });
  });

  const viewToggle = document.getElementById("toggle-mobile-cards");
  if (viewToggle) {
    viewToggle.addEventListener("click", () => {
      document.querySelectorAll("table.data-table").forEach((tbl) => {
        tbl.classList.toggle("mobile-cards");
      });
    });
  }
});
