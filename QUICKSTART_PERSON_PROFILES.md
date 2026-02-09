# Person Profiles Quick Start

## What Was Built

Person profile pages for the 3 major people in the Epstein files (5+ mentions):
- Jeffrey Epstein (119 mentions)
- Ghislaine Maxwell (67 mentions)
- Lesley Groff (20 mentions)

## User Flows

### Flow 1: Discover People
1. Click "People" in navigation
2. See grid of major people with mention counts
3. Click any person card → detail page

### Flow 2: Search → Person Profile
1. Search for anything (e.g., "Maxwell")
2. See person names in results (with 👤 icon)
3. Click person name → auto-filter by that person
4. See "»" link next to major people → click for profile

### Flow 3: Person Detail Page
1. Navigate to person page (e.g., `/people/jeffrey-epstein.html`)
2. See overview stats (mentions, document types, timeline span)
3. View document type breakdown (visual bars)
4. Browse timeline (grouped by year, sortable)
5. Search/filter within that person's documents

## URLs

- Hub: `/people.html`
- Jeffrey Epstein: `/people/jeffrey-epstein.html`
- Ghislaine Maxwell: `/people/ghislaine-maxwell.html`
- Lesley Groff: `/people/lesley-groff.html`

## Key Files

**Templates:**
- `site/templates/people.html` - Hub page
- `site/templates/person.html` - Detail page

**Data Generation:**
- `scripts/prepare_person_data.py` - Run before build
- `scripts/build_site.py` - Generates all pages

**Enhanced Search:**
- `site/assets/app.js` - Clickable person names
- `site/assets/styles.css` - Person link styles

## Build Commands

```bash
# 1. Prepare person data
python3 scripts/prepare_person_data.py

# 2. Build site
PYTHONPATH=. python3 scripts/build_site.py

# 3. Deploy (push to GitHub)
git push origin main
```

## Data Files

Generated at build time:
- `data/derived/people.json` - Master index
- `data/derived/people/{slug}.json` - Individual person data
- `dist/people.html` - Hub page
- `dist/people/{slug}.html` - Detail pages

## Features

✅ Person hub landing page  
✅ Individual person detail pages  
✅ Timeline view (chronological, sortable)  
✅ Document type breakdown (visual bars)  
✅ Searchable document lists per person  
✅ Clickable person names in search results  
✅ Profile links for major people (» icon)  
✅ Search integration (click → filter)  
✅ Fully static (GitHub Pages compatible)  
✅ Responsive design  

## Documentation

- Strategy: `docs/PERSON_PROFILES_STRATEGY.md`
- Implementation Report: `docs/PERSON_PROFILES_IMPLEMENTATION_REPORT.md`
- This Quickstart: `QUICKSTART_PERSON_PROFILES.md`
