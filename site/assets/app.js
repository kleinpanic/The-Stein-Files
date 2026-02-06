function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const SEARCH_MODE_FIELDS = {
  full: ["title", "content", "tags", "source_name", "file_name", "id"],
  title: ["title"],
  tags: ["tags"],
  source: ["source_name"],
  file: ["file_name", "id"],
};

const SEARCH_MODE_PLACEHOLDERS = {
  full: "Search names, places, or terms",
  title: "Search document titles",
  tags: "Search tags",
  source: "Search sources",
  file: "Search filename or ID",
};

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
  if (dateStr.length >= 10) return dateStr;
  return dateStr;
}

function buildSnippet(content, query) {
  const text = content || "";
  if (!query) return text.slice(0, 220);
  const lower = text.toLowerCase();
  const q = query.toLowerCase();
  const idx = lower.indexOf(q);
  if (idx === -1) return text.slice(0, 220);
  const start = Math.max(0, idx - 90);
  const end = Math.min(text.length, idx + 130);
  return text.slice(start, end);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlightSnippet(snippet, query) {
  if (!query) return escapeHtml(snippet);
  const escaped = escapeHtml(snippet);
  const escapedQuery = escapeRegExp(escapeHtml(query));
  const regex = new RegExp(`(${escapedQuery})`, "ig");
  return escaped.replace(regex, "<mark>$1</mark>");
}

function applyFilters(docs, { source, year, tag }) {
  return docs.filter((doc) => {
    if (source && doc.source_name !== source) return false;
    if (year) {
      const docYear = (doc.release_date || "").slice(0, 4);
      if (docYear !== year) return false;
    }
    if (tag && !(doc.tags || []).includes(tag)) return false;
    return true;
  });
}

function sortResults(results, sortBy) {
  if (sortBy === "date") {
    return results.sort((a, b) => (b.release_date || "").localeCompare(a.release_date || ""));
  }
  return results.sort((a, b) => (b.score || 0) - (a.score || 0));
}

function getStateFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return {
    q: params.get("q") || "",
    source: params.get("source") || "",
    year: params.get("year") || "",
    tag: params.get("tag") || "",
    sort: params.get("sort") || "relevance",
    mode: params.get("mode") || "full",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  if (state.q) params.set("q", state.q);
  if (state.source) params.set("source", state.source);
  if (state.year) params.set("year", state.year);
  if (state.tag) params.set("tag", state.tag);
  if (state.sort && state.sort !== "relevance") params.set("sort", state.sort);
  if (state.mode && state.mode !== "full") params.set("mode", state.mode);
  const query = params.toString();
  const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  window.history.replaceState({}, "", newUrl);
}

function renderResults(target, results, metaById, query) {
  target.innerHTML = "";
  results.forEach((result) => {
    const meta = metaById[result.id];
    if (!meta) return;
    const tags = (meta.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
    const snippet = buildSnippet(result.content, query);
    const snippetHtml = highlightSnippet(snippet, query);
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <h3>${escapeHtml(meta.title)}</h3>
      <div class="result-meta">
        <span>${formatDate(meta.release_date)}</span>
        <span>${escapeHtml(meta.source_name)}</span>
      </div>
      <div class="result-tags">${tags}</div>
      <p class="result-snippet">${snippetHtml}</p>
      <div class="result-actions">
        <a class="button" href="${meta.source_url || meta.file_path}">Original</a>
        <a class="button outline" href="data/derived/text/${meta.id}.txt">Text</a>
        <a class="button ghost" href="documents/${meta.id}.html">Details</a>
      </div>
    `;
    target.appendChild(card);
  });
}

async function init() {
  const loadingState = document.getElementById("loadingState");
  const emptyState = document.getElementById("emptyState");
  const noResultsState = document.getElementById("noResultsState");
  const resultCount = document.getElementById("resultCount");
  const loadStatus = document.getElementById("loadStatus");
  const resultsEl = document.getElementById("results");

  loadingState.hidden = false;
  const [manifest, catalog] = await Promise.all([
    loadJson("data/derived/index/manifest.json"),
    loadJson("data/meta/catalog.json"),
  ]);

  const hasCatalog = catalog.length > 0;
  if (!hasCatalog) {
    emptyState.hidden = false;
    noResultsState.hidden = true;
  }

  const metaById = {};
  catalog.forEach((doc) => {
    metaById[doc.id] = doc;
  });

  const sources = uniqueSorted(catalog.map((doc) => doc.source_name));
  const years = uniqueSorted(
    catalog
      .map((doc) => (doc.release_date ? doc.release_date.slice(0, 4) : ""))
      .filter((year) => year && /\d{4}/.test(year))
  );
  const tags = uniqueSorted(catalog.flatMap((doc) => doc.tags || []));

  const filterSource = document.getElementById("filterSource");
  const filterYear = document.getElementById("filterYear");
  const filterTag = document.getElementById("filterTag");
  const sortBy = document.getElementById("sortBy");
  const searchInput = document.getElementById("searchInput");
  const searchMode = document.getElementById("searchMode");
  const clearFilters = document.getElementById("clearFilters");

  filterSource.innerHTML = `<option value="">All sources</option>${sources
    .map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`)
    .join("")}`;
  filterYear.innerHTML = `<option value="">All years</option>${years
    .map((y) => `<option value="${y}">${y}</option>`)
    .join("")}`;
  filterTag.innerHTML = `<option value="">All tags</option>${tags
    .map((t) => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`)
    .join("")}`;

  const state = getStateFromUrl();
  searchInput.value = state.q;
  filterSource.value = state.source;
  filterYear.value = state.year;
  filterTag.value = state.tag;
  sortBy.value = state.sort;
  searchMode.value = state.mode;

  searchInput.placeholder = SEARCH_MODE_PLACEHOLDERS[searchMode.value] || SEARCH_MODE_PLACEHOLDERS.full;

  const shardLookup = manifest.shards || [];

  const loadedShards = new Map();
  let indexDocs = [];
  let lunrIndex = null;

  function rebuildIndex() {
    lunrIndex = lunr(function () {
      this.ref("id");
      this.field("title");
      this.field("content");
      this.field("source_name");
      this.field("tags");
      this.field("file_name");
      this.field("id");
      indexDocs.forEach((doc) => this.add(doc));
    });
  }

  async function loadShard(path) {
    if (loadedShards.has(path)) return;
    const docs = await loadJson(path);
    loadedShards.set(path, docs);
    indexDocs = Array.from(loadedShards.values()).flat();
    rebuildIndex();
    if (loadingState.hidden === false) {
      loadingState.hidden = true;
    }
  }

  async function loadShardsForState(currentState) {
    const desired = shardLookup.filter((shard) => {
      if (currentState.source && shard.source_name !== currentState.source) return false;
      if (currentState.year && shard.year !== currentState.year) return false;
      return true;
    });
    if (!desired.length) return;
    for (const shard of desired) {
      await loadShard(shard.path);
      loadStatus.textContent = `Loaded ${loadedShards.size} of ${shardLookup.length} shards`;
      performSearch();
    }
  }

  async function loadAllShardsProgressively() {
    for (const shard of shardLookup) {
      await loadShard(shard.path);
      loadStatus.textContent = `Loaded ${loadedShards.size} of ${shardLookup.length} shards`;
      performSearch();
    }
  }

  function performSearch() {
    if (!indexDocs.length) {
      resultsEl.innerHTML = "";
      resultCount.textContent = "0 results";
      if (!hasCatalog) {
        noResultsState.hidden = true;
      } else {
        noResultsState.hidden = loadingState.hidden === false;
      }
      return;
    }
    const query = searchInput.value.trim();
    const filters = {
      source: filterSource.value,
      year: filterYear.value,
      tag: filterTag.value,
    };

    let docs = indexDocs;
    if (query && lunrIndex) {
      const fields = SEARCH_MODE_FIELDS[searchMode.value] || SEARCH_MODE_FIELDS.full;
      // Normalize query terms so search is case-insensitive.
      const terms = query
        .split(/\s+/)
        .filter(Boolean)
        .map((term) => term.toLowerCase());
      const hits = lunrIndex.query((q) => {
        terms.forEach((term) => {
          q.term(term, { fields });
        });
      });
      const hitMap = new Map(hits.map((h) => [h.ref, h.score]));
      docs = indexDocs
        .filter((doc) => hitMap.has(doc.id))
        .map((doc) => ({ ...doc, score: hitMap.get(doc.id) }));
    }

    docs = applyFilters(docs, filters);
    const sorted = sortResults(docs, sortBy.value);
    renderResults(resultsEl, sorted, metaById, query);
    resultCount.textContent = `${sorted.length} results`;
    noResultsState.hidden = sorted.length > 0;
  }

  function syncAndSearch() {
    const nextState = {
      q: searchInput.value.trim(),
      source: filterSource.value,
      year: filterYear.value,
      tag: filterTag.value,
      sort: sortBy.value,
      mode: searchMode.value,
    };
    updateUrl(nextState);
    performSearch();
  }

  [filterSource, filterYear, filterTag, sortBy, searchMode].forEach((el) =>
    el.addEventListener("change", () => {
      if (el === searchMode) {
        searchInput.placeholder =
          SEARCH_MODE_PLACEHOLDERS[searchMode.value] || SEARCH_MODE_PLACEHOLDERS.full;
      }
      syncAndSearch();
      if (!filterSource.value && !filterYear.value) {
        loadAllShardsProgressively();
      } else {
        loadShardsForState({
          source: filterSource.value,
          year: filterYear.value,
        });
      }
    })
  );
  searchInput.addEventListener("input", syncAndSearch);
  clearFilters.addEventListener("click", () => {
    searchInput.value = "";
    filterSource.value = "";
    filterYear.value = "";
    filterTag.value = "";
    sortBy.value = "relevance";
    searchMode.value = "full";
    searchInput.placeholder = SEARCH_MODE_PLACEHOLDERS.full;
    syncAndSearch();
    loadAllShardsProgressively();
  });

  const filtersPanel = document.getElementById("filtersPanel");
  const openFilters = document.getElementById("openFilters");
  const closeFilters = document.getElementById("closeFilters");
  const backdrop = document.getElementById("filtersBackdrop");
  openFilters.addEventListener("click", () => {
    filtersPanel.classList.add("open");
    backdrop.hidden = false;
  });
  closeFilters.addEventListener("click", () => {
    filtersPanel.classList.remove("open");
    backdrop.hidden = true;
  });
  backdrop.addEventListener("click", () => {
    filtersPanel.classList.remove("open");
    backdrop.hidden = true;
  });

  if (filterSource.value || filterYear.value) {
    await loadShardsForState({ source: filterSource.value, year: filterYear.value });
  } else {
    await loadAllShardsProgressively();
  }

  syncAndSearch();
}

init().catch((err) => {
  console.error(err);
});
