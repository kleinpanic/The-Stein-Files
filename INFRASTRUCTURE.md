# Infrastructure Analysis - Eppie Project

## The Numbers

### Current State (0.3% of announced content)
- **Documents:** 947
- **Pages:** 9,999
- **Raw storage:** 1.5 GB
- **Derived data:** 36 MB
- **Metadata:** 6.1 MB

### Projected Full Collection (3.5M pages)
- **Documents:** ~331,000
- **Pages:** 3,500,000
- **Raw storage:** **496 GB**
- **Derived data:** ~12 GB (scaled)
- **Metadata:** ~2 GB (scaled)
- **Total:** **~510 GB**

---

## GitHub Infrastructure Assessment

### Current Setup
- Raw PDFs: Git LFS (1.5 GB currently)
- Derived text/indexes: Regular Git (42 MB)
- Site: GitHub Pages (static HTML/JS/CSS)
- Ingestion: GitHub Actions workflow

### GitHub Limits
| Resource | Limit | Projected Need | Status |
|----------|-------|----------------|--------|
| **Repo size (hard limit)** | 100 GB | 510 GB | ❌ **5x over limit** |
| **Git LFS (free)** | 1 GB storage<br>1 GB bandwidth/month | 496 GB storage<br>∞ bandwidth | ❌ **496x over** |
| **GitHub Actions runtime** | 6 hours/job | Days for full ingest | ❌ **Impossible** |
| **GitHub Pages** | Static hosting | 500+ GB PDF serving | ❌ **Wrong tool** |

### Verdict: **GitHub is NOT viable infrastructure for this project.**

---

## Alternative Architectures

### Option 1: Archive-First Model (RECOMMENDED)
**Concept:** Full archive on dedicated storage, GitHub for metadata + search UI only

**Infrastructure:**
- **Raw PDFs:** External storage (S3, Wasabi, or local NAS)
  - AWS S3: ~$11.40/month storage + bandwidth
  - Wasabi: ~$6/month storage, free egress
  - Local NAS: One-time hardware cost (~$500 for 1TB drive + enclosure)
- **Derived data:** GitHub repo (text extracts, indexes, metadata)
- **Search UI:** GitHub Pages (points to external PDFs)
- **Ingestion:** Run locally, push metadata to GitHub

**Pros:**
- Scales to any size
- Separates archive (expensive) from search (cheap)
- GitHub Pages works great for search UI
- Can seed torrents for distributed access

**Cons:**
- Users can't get PDFs directly from GitHub
- Need external hosting account (or local server)
- Bandwidth costs if hosted on cloud

**Cost:** $6-12/month (cloud) or $500 one-time (local)

---

### Option 2: Torrent + Local Index
**Concept:** Torrent for PDF distribution, GitHub for search/metadata

**Infrastructure:**
- **Raw PDFs:** BitTorrent (seed from local machine or seedbox)
- **Derived data:** GitHub repo
- **Search UI:** GitHub Pages (magnet links to torrents)
- **Ingestion:** Local only

**Pros:**
- Zero ongoing hosting cost
- Distributed bandwidth (seeders help)
- Censorship resistant
- Proper for "full archive" goal

**Cons:**
- Users must use torrent client
- Requires seeding infrastructure (your machine or seedbox ~$10/month)
- Slow initial distribution

**Cost:** $0-10/month (if using seedbox)

---

### Option 3: Hybrid - Metadata on GitHub, PDFs Local
**Concept:** Keep everything local, publish search index + metadata to GitHub

**Infrastructure:**
- **Raw PDFs:** Local disk only (no upload)
- **Derived data:** GitHub repo (text, indexes, metadata)
- **Search UI:** GitHub Pages (says "download torrent for PDFs")
- **Ingestion:** Local only
- **Distribution:** Create periodic torrent snapshots

**Pros:**
- Works entirely within GitHub limits
- No cloud costs
- Full local control
- Can release periodic "data drops" as torrents

**Cons:**
- PDFs not accessible via web
- Users need separate download
- Two-step access (search on web, download via torrent)

**Cost:** $0/month

---

### Option 4: Full Local Deployment (No GitHub)
**Concept:** Run everything on local machine(s)

**Infrastructure:**
- **Raw PDFs:** Local disk (~500 GB)
- **Search backend:** Local Elasticsearch or MeiliSearch
- **Web UI:** Local nginx/Apache
- **Access:** Via VPN or open to internet (if IP allows)

**Pros:**
- Complete control
- No external dependencies
- No size limits
- Can handle full 3.5M pages

**Cons:**
- Requires local server uptime
- Need static IP or dynamic DNS
- Bandwidth on your connection
- Single point of failure

**Cost:** $0/month (hardware you already have)

---

## Recommendation: Option 1 (Archive-First with Wasabi/S3)

**Why:**
1. **Separates concerns:** PDFs live where they belong (cheap bulk storage), metadata lives where it works best (GitHub/Git)
2. **Scales indefinitely:** Can grow to 10M pages without changing architecture
3. **Best user experience:** Search on GitHub Pages, click to download PDF from CDN
4. **Professional:** Proper infrastructure for "official archival project"
5. **Costs ~$10/month:** Sustainable for long-term project

**Implementation:**
1. **Now:** Continue using GitHub for metadata, text extracts, search UI
2. **For PDFs:** 
   - Upload to Wasabi ($6/month for 500GB) or AWS S3 (~$11/month)
   - OR: Set up local NAS + Cloudflare tunnel for free CDN
3. **Site changes:**
   - PDF links point to `https://archive.eppie-files.com/EFTA00001234.pdf` (S3/Wasabi)
   - Keep current search/browse UI on GitHub Pages
4. **Ingestion:**
   - Run locally (not GitHub Actions)
   - Upload PDFs to S3/Wasabi
   - Push metadata/indexes to GitHub

**Storage providers comparison:**
| Provider | 500GB/month | Egress (download) | Notes |
|----------|-------------|-------------------|-------|
| **Wasabi** | $5.99 | Free | Best for archives, 90-day retention |
| **AWS S3** | $11.50 | $0.09/GB | Standard option, pay-as-you-go |
| **Backblaze B2** | $3.00 | $0.01/GB | Cheapest storage, moderate egress |
| **Cloudflare R2** | $7.50 | Free | Free egress with Cloudflare CDN |

---

## Alternative: Local NAS + Cloudflare Tunnel (FREE CDN)

If you have local machine that can stay up:
1. **Get external drive:** 1TB USB 3.0 HDD ($50) or use existing storage
2. **Run Cloudflare tunnel:** Free CDN, no open ports needed
3. **Serve PDFs locally:** nginx or Python SimpleHTTPServer
4. **Result:** Free, unlimited bandwidth via Cloudflare, ~500GB local storage

**Setup:**
```bash
# Install Cloudflare tunnel
cloudflared tunnel create eppie-archive
cloudflared tunnel route dns eppie-archive archive.eppie-files.com
# Run tunnel pointing to local nginx serving PDFs
```

**Cost:** $0/month (if you have disk and uptime)

---

## Decision Matrix

| Criteria | GitHub Only | S3/Wasabi | Torrent | Local NAS+CF |
|----------|-------------|-----------|---------|--------------|
| **Supports 3.5M pages** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **User-friendly access** | N/A | ✅ Direct links | ⚠️ Torrent client | ✅ Direct links |
| **Monthly cost** | $0 (but broken) | $6-12 | $0-10 | $0 |
| **Setup complexity** | Low | Medium | Medium | High |
| **Bandwidth scaling** | N/A | ✅ CDN | ✅ Distributed | ✅ Cloudflare |
| **Censorship resistant** | No | No | ✅ Yes | ⚠️ Depends |
| **Long-term viable** | ❌ No | ✅ Yes | ✅ Yes | ⚠️ Uptime dependent |

---

## Immediate Action Plan

**Phase 1: Prove Ingestion (This Week)**
1. Fix discovery to enumerate all EFTA files across all DataSets
2. Run on DataSets 1-5 (~50,000 docs?) to local storage
3. Measure actual storage per 10K docs
4. Re-calculate total storage needed with real data

**Phase 2: Choose Infrastructure (Next Week)**
1. Based on Phase 1 data, pick: S3/Wasabi vs Local NAS vs Torrent
2. If S3/Wasabi: set up account, test upload/download
3. If Local NAS: set up Cloudflare tunnel, test serving
4. Update site to point to new PDF storage

**Phase 3: Full Ingestion (Week 3-4)**
1. Run complete enumeration ingestion (DataSets 1-100+)
2. Upload PDFs to chosen storage
3. Generate metadata/indexes
4. Deploy complete search site

**Phase 4: Validation & Launch**
1. Verify person extraction works properly
2. Test search quality
3. Announce complete archive

---

## Recommendation

**START WITH:** Local NAS + Cloudflare Tunnel (free, fast to set up, infinite scale)
**FALLBACK TO:** Wasabi if local uptime is unreliable (~$6/month)
**NEVER USE:** GitHub for PDF storage (wrong tool, will fail)

The search UI and metadata on GitHub Pages is PERFECT and should stay. Just move the PDFs elsewhere.
