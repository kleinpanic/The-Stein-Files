# Post-Change Review Checklist

Run this checklist after every commit before pushing to origin.

## Version Control
- [ ] Version number updated in `VERSION` file (if needed)
  - Bug fix (z): Increment last digit (1.5.0 → 1.5.1)
  - Minor feature (y): Increment middle digit (1.5.1 → 1.6.0)
  - Major release (x): Increment first digit (1.6.0 → 2.0.0)
- [ ] CHANGELOG.md updated with changes
  - Added entries under [Unreleased]
  - Moved to version section if releasing
- [ ] Git commit message is clear and descriptive
  - Format: `type: description` (feat:, fix:, docs:, refactor:, test:)
  - Includes context and rationale

## Code Quality
- [ ] All tests pass: `make test`
- [ ] No linting errors (if applicable)
- [ ] No hardcoded secrets or API keys
- [ ] Dependencies updated in requirements.txt (if added)
- [ ] Scripts are executable: `chmod +x scripts/*.py`

## Data Integrity
- [ ] Catalog structure validated: `python scripts/validate.py`
- [ ] Sample data spot-checked (5-10 random docs)
- [ ] No data loss (compare before/after counts)
- [ ] Backups exist for modified files

## UI/UX
- [ ] Changes tested in browser (if UI changes)
- [ ] Mobile responsiveness checked (if applicable)
- [ ] Accessibility: ARIA labels, keyboard navigation
- [ ] No JavaScript console errors
- [ ] Asset loading verified (CSS, JS, images)

## Performance
- [ ] Large operations batched/paginated
- [ ] No excessive file I/O in loops
- [ ] Database queries optimized (if applicable)
- [ ] Asset sizes reasonable (<1MB for images)

## Documentation
- [ ] README.md updated (if user-facing changes)
- [ ] Script docstrings clear and accurate
- [ ] Configuration changes documented
- [ ] Known issues/limitations noted

## Deployment
- [ ] CI/CD workflow will pass (check .github/workflows/)
- [ ] No breaking changes to existing data format
- [ ] Rollback plan considered
- [ ] Monitoring/alerting configured (if production)

## Post-Push Validation
- [ ] GitHub Actions green (check after push)
- [ ] Deployed site validated (if auto-deploys)
- [ ] Key features spot-checked on live site
- [ ] Error logs reviewed (if monitoring exists)

## Continuous Improvement
- [ ] Technical debt noted in issues/TODO.md
- [ ] Performance bottlenecks identified
- [ ] Future enhancements documented
- [ ] Lessons learned captured

---

## Quick Checks (Every Commit)
```bash
# Version check
cat VERSION

# Test suite
make test

# Catalog validation
.venv/bin/python scripts/validate.py

# Git status
git status --short

# Commit
git add <files>
git commit -m "type: clear description"
git push origin main
```

## Release Checklist (Major/Minor Only)
- [ ] Version bumped in VERSION file
- [ ] CHANGELOG.md: Move [Unreleased] to [X.Y.0]
- [ ] Git tag created: `git tag vX.Y.0`
- [ ] Tag pushed: `git push origin vX.Y.0`
- [ ] GitHub release created (if auto-release fails)
- [ ] Deployment validated on live site
- [ ] Announcement prepared (if major release)
