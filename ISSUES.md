# Issues Tracker - Autonomous Session

## Active Issues (Must Fix Before Push)

_None currently blocking_

---

## Found Issues (To Be Fixed)

### High Priority

_None - live site works correctly_

### Medium Priority

**Local Testing Limitation**
- `make dev` serves from root, but `<base href="/The-Stein-Files/">` expects GitHub Pages path
- Workaround: Test on live site after deployment
- Fix: Add `EPPIE_LOCAL_DEV=1` env to use `<base href="/">` for local testing

### Low Priority

**Category dropdown outdated on live site**
- Live site shows old categories (pre-v1.5.2)
- Will update after next push + CI/CD completion

---

## Fixed This Session

| Issue | Fix | Commit |
|-------|-----|--------|
| Email metadata 100% missing | Improved extraction patterns | a0148c9 |
| Categorization 48.8% | Added 16 new categories | b3390d8 |

---

## Validation Checklist (Each Heartbeat)

- [ ] `make test` passes
- [ ] Local site loads (`make dev`)
- [ ] Main page renders
- [ ] Search works
- [ ] Filters work
- [ ] Individual documents load
- [ ] PDF viewer works
- [ ] Emails section works
- [ ] People section works
- [ ] Stats page loads
- [ ] Mobile responsive

---

## Notes

_Updated during browser validation_
