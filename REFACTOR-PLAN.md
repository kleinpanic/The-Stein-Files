# Epstein Archive - Production Refactor Plan

## Architecture Overview

### Current State (broklein - prototype)
- Research/development version
- GitHub Pages + LFS (broken for full scale)
- 947 docs, 10K pages (0.3% of target)
- Stays as-is for reference

### New State (mt - production)
- **Location:** /srv/epstein on mt server
- **Storage:** 700GB dedicated LV (ext4)
- **Access:** mt → WireGuard → edge-gateway (DigitalOcean VPS) → HAProxy → Internet
- **Goal:** Full 3.5M pages, rich search, people/email sections, downloads

---

## Infrastructure Stack

### Backend (mt)
- **Web Server:** nginx or Caddy (reverse proxy + static files)
- **Search Engine:** MeiliSearch or Typesense (better than lunr.js for 331K docs)
- **Database:** PostgreSQL (metadata, people, relationships)
- **Storage:**
  - Raw PDFs: /srv/epstein/data/raw (496 GB)
  - Derived text: /srv/epstein/data/derived (12 GB)
  - Indexes: /srv/epstein/data/indexes (2 GB)
  - Database: /srv/epstein/data/db (2 GB)

### Frontend
- **Framework:** Keep current static site approach but generate richer pages
- **CDN:** Edge-gateway serves via HAProxy
- **Features:**
  - Full-text search across all documents
  - Person profiles with relationship graphs
  - Email browser with threading
  - Document viewer with annotations
  - Bulk download by category/date/person
  - API for programmatic access

### Access Layer (edge-gateway)
- HAProxy config:
  - SSL termination
  - Rate limiting
  - Caching headers
  - Gzip compression
- Cloudflare DNS (if using CF)

---

## Domain Strategy

### Option 1: Dedicated Domain (RECOMMENDED)
**Examples:**
- `epsteinlibrary.org` - official, neutral
- `epsteinarchive.org` - archive-focused
- `epsteinfiles.com` - direct, SEO-friendly
- `steindocs.org` - your current name scheme

**Pros:**
- Professional, authoritative
- SEO-optimized
- No association with personal brand
- Can register non-profit TLD (.org)

**Cons:**
- Domain cost (~$12-15/year)
- Separate identity to maintain

**Recommendation:** `epsteinlibrary.org` - neutral, authoritative, .org signals non-profit/public service

---

### Option 2: Subdomain on kleinpanic.com
**Examples:**
- `archive.kleinpanic.com` - generic
- `epstein.kleinpanic.com` - direct
- `docs.kleinpanic.com` - document-focused
- `library.kleinpanic.com` - softer tone

**Pros:**
- Uses existing domain
- No additional cost
- Part of your portfolio
- Easier DNS management

**Cons:**
- Associates sensitive content with personal brand
- Less discoverable via search
- Potential controversy linkage

**Recommendation:** `archive.kleinpanic.com` - if you want it under your brand, keep it generic

---

### Option 3: Hybrid Approach
- Primary: `epsteinlibrary.org` (public-facing)
- Mirror: `archive.kleinpanic.com` (backup/dev)

**Use case:** Professional primary with personal backup

---

## My Recommendation

**Go with `epsteinlibrary.org`**

**Why:**
1. **Separates concerns:** This is public archive, not personal portfolio
2. **SEO:** People searching "epstein documents" will find it
3. **Professional:** .org signals this is a public service project
4. **Safe:** No personal brand association with controversial content
5. **Scalable:** Can add other archives later (epsteinlibrary.org/fbi, /court-records, etc.)

**Fallback:** If you want to start fast with no domain cost, use `archive.kleinpanic.com` now and migrate to dedicated domain later (easy with HAProxy redirect rules).

---

## Tech Stack Recommendation

### For Production Deployment

**Web Server:** Caddy
- Auto HTTPS
- Simple config
- Perfect for reverse proxy
- Built-in compression/caching

**Search:** MeiliSearch
- Fast (Rust-based)
- Typo-tolerant
- Faceted search (filter by person/date/category)
- 1GB RAM per 100K docs = 3-4GB RAM for 331K docs (mt has this)

**Database:** PostgreSQL
- Relational data (people, documents, relationships)
- Full-text search backup
- JSON fields for flexibility
- Proven, stable

**Frontend:** Static site generator (keep current approach but enhanced)
- Pre-build all person pages, category pages, etc.
- Use MeiliSearch for live search
- Progressive enhancement (works without JS, better with JS)

---

## Migration Plan

### Phase 1: Setup Infrastructure (This Week)
1. ✅ Clone repo to mt:/srv/epstein
2. ✅ Remove .git, start fresh repo
3. Install stack on mt:
   - Caddy
   - MeiliSearch
   - PostgreSQL
   - Python 3.11+
4. Set up HAProxy on edge-gateway
5. Choose domain and configure DNS

### Phase 2: Fix Ingestion (Week 1-2)
1. Implement EFTA enumeration (not HTML scraping)
2. Test on DataSets 1-5 (~50K docs)
3. Measure actual storage/time
4. Run full ingestion (DataSets 1-100+)
5. Verify 3.5M pages

### Phase 3: Build Search Backend (Week 2-3)
1. Import all metadata to PostgreSQL
2. Index all text in MeiliSearch
3. Extract people/relationships to DB
4. Build API endpoints
5. Test search performance

### Phase 4: Build Frontend (Week 3-4)
1. Redesign with backend integration
2. Person pages with real data
3. Email browser
4. Document viewer
5. Bulk download features

### Phase 5: Deploy & Test (Week 4)
1. Full deployment to mt
2. HAProxy config on edge-gateway
3. DNS cutover
4. Load testing
5. Public announcement

---

## Resource Requirements

### mt server needs:
- **RAM:** 8GB minimum (4GB for MeiliSearch, 2GB for PostgreSQL, 2GB for OS/web)
- **CPU:** 4+ cores (ingestion is CPU-heavy for OCR)
- **Storage:** 700GB ✅ (already allocated)
- **Network:** Stable connection to edge-gateway via WireGuard

### edge-gateway VPS needs:
- **RAM:** 1GB (just HAProxy)
- **CPU:** 1 core
- **Bandwidth:** Unlimited preferred (users downloading PDFs)

---

## Security Considerations

1. **Access Control:** None needed (public archive), but rate-limit to prevent scraping
2. **DDoS Protection:** Cloudflare (if using CF DNS) or HAProxy rate limits
3. **Backups:** 
   - Database: daily dumps to external storage
   - PDFs: consider torrent seeding as distributed backup
4. **Monitoring:** 
   - Uptime monitoring (UptimeRobot, etc.)
   - Disk space alerts
   - Error logging

---

## Cost Breakdown

### One-time:
- Domain registration: $12-15/year (if dedicated domain)
- Development time: Already invested

### Monthly:
- edge-gateway VPS: Already running
- Bandwidth: Depends on traffic (potentially $0 with CloudFlare)
- Domain renewal: $1/month amortized

**Total: ~$1-2/month or $0 if using subdomain + existing infra**

---

## Next Steps (IMMEDIATE)

1. **Klein decides:** Domain choice?
   - `epsteinlibrary.org` (dedicated) OR
   - `archive.kleinpanic.com` (subdomain)

2. **I will:**
   - Initialize new git repo on mt
   - Create ARCHITECTURE.md with tech stack details
   - Set up tmux workflow for mt development
   - Begin ingestion refactor (enumeration-based)

3. **Klein sets up:**
   - DNS pointing to edge-gateway
   - HAProxy config for chosen domain
   - WireGuard if not already configured

---

## Questions for Klein

1. **Domain:** Dedicated or subdomain? (Recommend: `epsteinlibrary.org`)
2. **mt specs:** Can you confirm RAM/CPU on mt? (Need 8GB+ RAM for search)
3. **Bandwidth:** Any limits on edge-gateway VPS?
4. **Timeline:** Rush to launch or build it right over 4 weeks?
5. **Features:** Any must-haves beyond search/browse/download?

Ready to start building as soon as you pick the domain.
