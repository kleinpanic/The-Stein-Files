async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return res.json();
}

function uniqueSorted(values) {
  return Array.from(new Set(values)).sort();
}

function formatDate(dateStr) {
  if (!dateStr) return "Unknown";
  return dateStr;
}

function buildSnippet(content, query) {
  const text = content || "";
  if (!query) return text.slice(0, 200);
  const lower = text.toLowerCase();
  const q = query.toLowerCase();
  const idx = lower.indexOf(q);
  if (idx === -1) return text.slice(0, 200);
  const start = Math.max(0, idx - 80);
  const end = Math.min(text.length, idx + 120);
  return text.slice(start, end);
}

function renderResults(target, results, metaById, query) {
  target.innerHTML = "";
  results.forEach((result) => {
    const meta = metaById[result.id];
    if (!meta) return;
    const card = document.createElement("div");
    card.className = "result-card";
    const tags = (meta.tags || []).map((tag) => `<span class="tag">${tag}</span>`).join("");
    card.innerHTML = `
      <h3>${meta.title}</h3>
      <div class="result-meta">${formatDate(meta.release_date)} | ${meta.source_name}</div>
      <div class="result-tags">${tags}</div>
      <p>${buildSnippet(result.content, query)}</p>
      <div class="result-actions">
        <a class="button" href="${meta.file_path}">View original</a>
        <a class="button" href="data/derived/text/${meta.id}.txt">View text</a>
        <a class="button" href="documents/${meta.id}.html">Details</a>
      </div>
    `;
    target.appendChild(card);
  });
}

function sortResults(results, sortBy) {
  if (sortBy === "date") {
    return results.sort((a, b) => (b.release_date || "").localeCompare(a.release_date || ""));
  }
  return results.sort((a, b) => (b.score || 0) - (a.score || 0));
}

function applyFilters(docs, { source, year, tag }) {
  return docs.filter((doc) => {
    if (source && doc.source_name !== source) return false;
    if (year && (!doc.release_date || !doc.release_date.startsWith(year))) return false;
    if (tag && !(doc.tags || []).includes(tag)) return false;
    return true;
  });
}

async function init() {
  const [indexDocs, catalog] = await Promise.all([
    loadJson("data/derived/index/search-index.json"),
    loadJson("data/meta/catalog.json"),
  ]);

  const metaById = {};
  catalog.forEach((doc) => {
    metaById[doc.id] = doc;
  });

  const sources = uniqueSorted(catalog.map((doc) => doc.source_name));
  const years = uniqueSorted(
    catalog
      .map((doc) => (doc.release_date ? doc.release_date.slice(0, 4) : null))
      .filter(Boolean)
  );
  const tags = uniqueSorted(catalog.flatMap((doc) => doc.tags || []));

  const filterSource = document.getElementById("filterSource");
  const filterYear = document.getElementById("filterYear");
  const filterTag = document.getElementById("filterTag");
  const sortBy = document.getElementById("sortBy");
  const searchInput = document.getElementById("searchInput");
  const resultsEl = document.getElementById("results");
  const resultCount = document.getElementById("resultCount");

  filterSource.innerHTML = `<option value="">All</option>${sources
    .map((s) => `<option value="${s}">${s}</option>`)
    .join("")}`;
  filterYear.innerHTML = `<option value="">All</option>${years
    .map((y) => `<option value="${y}">${y}</option>`)
    .join("")}`;
  filterTag.innerHTML = `<option value="">All</option>${tags
    .map((t) => `<option value="${t}">${t}</option>`)
    .join("")}`;

  const lunrIndex = lunr(function () {
    this.ref("id");
    this.field("title");
    this.field("content");
    this.field("source_name");
    this.field("tags");
    indexDocs.forEach((doc) => this.add(doc));
  });

  function performSearch() {
    const query = searchInput.value.trim();
    const filters = {
      source: filterSource.value,
      year: filterYear.value,
      tag: filterTag.value,
    };

    let docs = indexDocs;
    if (query) {
      const hits = lunrIndex.search(query);
      const hitMap = new Map(hits.map((h) => [h.ref, h.score]));
      docs = indexDocs
        .filter((doc) => hitMap.has(doc.id))
        .map((doc) => ({ ...doc, score: hitMap.get(doc.id) }));
    }

    docs = applyFilters(docs, filters);
    const sorted = sortResults(docs, sortBy.value);
    renderResults(resultsEl, sorted, metaById, query);
    resultCount.textContent = `${sorted.length} results`;
  }

  [filterSource, filterYear, filterTag, sortBy].forEach((el) =>
    el.addEventListener("change", performSearch)
  );
  searchInput.addEventListener("input", performSearch);

  const filters = document.getElementById("filters");
  const toggle = document.getElementById("filtersToggle");
  toggle.addEventListener("click", () => {
    filters.classList.toggle("collapsed");
  });

  performSearch();
}

init().catch((err) => {
  console.error(err);
});
