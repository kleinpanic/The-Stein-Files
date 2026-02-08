// PDF.js viewer integration for Eppie
import * as pdfjsLib from './pdfjs/pdf.mjs';

// PDF.js configuration
pdfjsLib.GlobalWorkerOptions.workerSrc = 'assets/pdfjs/pdf.worker.mjs';

async function initPDFViewer() {
  const container = document.getElementById("pdf-container");
  const titleEl = document.getElementById("viewer-title");
  const originalLink = document.getElementById("viewer-original");
  const githubLink = document.getElementById("viewer-github");
  const textLink = document.getElementById("viewer-text");
  const pageInfo = document.getElementById("page-info");
  const prevBtn = document.getElementById("prev-page");
  const nextBtn = document.getElementById("next-page");

  if (!container) return;

  const params = new URLSearchParams(window.location.search);
  const id = params.get("id") || "";
  if (!id) {
    if (titleEl) titleEl.textContent = "Missing document id";
    return;
  }

  // Fetch catalog
  const catalogResp = await fetch("data/meta/catalog.json");
  const catalog = await catalogResp.json();
  const entry = (catalog || []).find((item) => item.id === id);
  if (!entry) {
    if (titleEl) titleEl.textContent = `Unknown document: ${id}`;
    return;
  }

  // Set metadata
  if (titleEl) titleEl.textContent = entry.title || id;
  if (originalLink) originalLink.href = entry.source_url || "#";
  if (textLink) textLink.href = `data/derived/text/${encodeURIComponent(id)}.txt`;

  const buildSha = document.querySelector('meta[name="build-sha"]')?.content || "";
  const repoSlug = document.querySelector('meta[name="repo-slug"]')?.content || "kleinpanic/The-Stein-Files";
  const filePath = entry.file_path || "";

  // Use source_url (original DOJ URL) as primary PDF source
  // GitHub Pages doesn't serve LFS files, so we load from original source
  let pdfUrl = entry.source_url || "";
  
  // If no source_url, can't display PDF
  if (!pdfUrl) {
    if (titleEl) titleEl.textContent = `${entry.title || id} (no PDF available)`;
    container.innerHTML = '<p class="error">PDF source URL not available.</p>';
    return;
  }

  if (githubLink && filePath && buildSha) {
    githubLink.href = `https://github.com/${repoSlug}/blob/${buildSha}/${filePath.split('/').map(encodeURIComponent).join('/')}`;
  }

  // Load PDF with PDF.js
  container.innerHTML = '<p class="loading">Loading PDF...</p>';

  try {
    const loadingTask = pdfjsLib.getDocument({
      url: pdfUrl,
      withCredentials: false,
    });

    const pdf = await loadingTask.promise;
    let currentPage = 1;
    const totalPages = pdf.numPages;

    // Update page info
    if (pageInfo) {
      pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }

    // Render function
    async function renderPage(num) {
      const page = await pdf.getPage(num);
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      // Scale for high-DPI displays
      const scale = window.devicePixelRatio || 1;
      const viewport = page.getViewport({ scale: 1.5 });

      canvas.height = viewport.height * scale;
      canvas.width = viewport.width * scale;
      canvas.style.width = `${viewport.width}px`;
      canvas.style.height = `${viewport.height}px`;

      ctx.scale(scale, scale);

      await page.render({
        canvasContext: ctx,
        viewport: viewport,
      }).promise;

      container.innerHTML = '';
      container.appendChild(canvas);

      if (pageInfo) {
        pageInfo.textContent = `Page ${num} of ${totalPages}`;
      }

      // Enable/disable buttons
      if (prevBtn) prevBtn.disabled = (num <= 1);
      if (nextBtn) nextBtn.disabled = (num >= totalPages);
    }

    // Initial render
    await renderPage(currentPage);

    // Navigation buttons
    if (prevBtn) {
      prevBtn.addEventListener('click', async () => {
        if (currentPage > 1) {
          currentPage--;
          await renderPage(currentPage);
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', async () => {
        if (currentPage < totalPages) {
          currentPage++;
          await renderPage(currentPage);
        }
      });
    }

  } catch (error) {
    console.error('PDF loading error:', error);
    container.innerHTML = `<p class="error">Failed to load PDF. <a href="${pdfUrl}" target="_blank">Try opening directly</a></p>`;
  }
}

// Initialize when DOM is ready
if (document.getElementById("pdf-container")) {
  initPDFViewer().catch((err) => {
    console.error(err);
    const container = document.getElementById("pdf-container");
    if (container) {
      container.innerHTML = '<p class="error">An error occurred loading the viewer.</p>';
    }
  });
}
