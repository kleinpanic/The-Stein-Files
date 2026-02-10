# Autonomous Work Workflow - Corrected

**Key principle**: Work continuously but carefully. Build complex things over time through small, validated steps.

## What I Misunderstood

❌ **Wrong approach** (what I did):
- Pushed 10 commits in 90 minutes
- No local validation
- No screenshots/visual review
- Rushed complex features
- Pushed to main constantly
- Didn't check CI/CD status

✅ **Correct approach** (what to do):
- Work on feature branches
- Validate locally before merging to main
- Review UI with screenshots
- Document changes thoroughly
- Merge to main only for releases (x.y.z)
- Check CI/CD before continuing
- Atomic commits (small, focused)
- Build complex features piece-by-piece over time

## The Workflow

### 1. Start Work on Feature Branch

```bash
# Create feature branch for work
git checkout -b feature/ai-extraction-mvp

# Or for fixes
git checkout -b fix/email-metadata-blanks
```

### 2. Make Atomic Changes

**Atomic = One focused change**
- Fix one bug
- Add one small feature
- Improve one aspect

**Not atomic**:
- "Improve everything"
- Multiple unrelated changes
- Large refactors + new features

### 3. Local Validation (REQUIRED)

Before ANY commit:

#### A. Run Tests
```bash
make test
# Wait for all tests to pass
```

#### B. Run Local Server
```bash
make serve
# Opens http://localhost:8000
```

#### C. Review Endpoints (see ENDPOINT_CHECKLIST.md)
- Check each affected page
- Take screenshots
- Note what changed
- Verify no regressions

#### D. Manual Spot Checks
- Sample 5-10 random documents
- Check metadata quality
- Verify UI displays correctly
- Test edge cases

### 4. Commit Locally

```bash
git add <specific files>
git commit -m "type: focused description

- Specific change 1
- Specific change 2
- Why this change was needed"
```

### 5. Continue Working (Don't Push Yet)

Keep working on feature branch:
- Make more atomic commits
- Validate each change locally
- Build up the feature piece by piece

### 6. Ready for Release? Merge to Main

Only merge to main when:
- Feature is complete and validated
- All tests pass
- Local review complete
- Screenshots documented
- CI/CD will pass

```bash
# Switch to main
git checkout main
git pull origin main

# Merge feature branch
git merge --no-ff feature/ai-extraction-mvp

# Update version
# - Bug fix (z): 1.5.1 → 1.5.2
# - Minor feature (y): 1.5.2 → 1.6.0
# - Major change (x): 1.6.0 → 2.0.0
echo "1.6.0" > VERSION

# Update CHANGELOG
# (add changes to [Unreleased], then move to [1.6.0] section)

# Commit version bump
git add VERSION CHANGELOG.md
git commit -m "release: v1.6.0"

# Push to main
git push origin main

# Tag release
git tag v1.6.0
git push origin v1.6.0
```

### 7. Monitor CI/CD

After push:
```bash
# Check CI/CD status
gh run list --limit 3

# If failed, check logs
gh run view <run-id> --log-failed

# Fix immediately if broken
```

### 8. Validate Deployment

Once deployed:
- Visit live site
- Check endpoint checklist
- Take screenshots
- Compare to local version
- Verify all changes live

## Cadence

**Feature work**: Days/weeks on branch, validate thoroughly

**Merge to main**: When feature complete + validated

**Push frequency**: Occasional (not after every commit)

**Validation**: Every single change, every single time

## Continuous Work ≠ Rushing

**Continuous work** means:
- Always working on something
- Consistent progress over time
- Building complex things through small steps
- Never idle

**NOT**:
- Rush out half-baked features
- Skip validation
- Push constantly
- Make hasty decisions

## Example Session

**Goal**: Add AI extraction for 50 documents

**Wrong approach** (what I did):
```
1. Implement everything in 30 minutes
2. Push to main
3. CI/CD breaks
4. No validation
```

**Correct approach**:
```
1. Branch: feature/ai-extraction
2. Implement ai_extract.py (30 min)
3. Test locally on 5 documents (15 min)
4. Review output quality (screenshots, notes) (15 min)
5. Commit locally with findings
6. Fix issues found (30 min)
7. Test again on 10 documents (15 min)
8. Document results in FINDINGS.md (10 min)
9. Commit improvements
10. Run full test suite (5 min)
11. Local endpoint review (10 min)
12. Merge to main when satisfied
13. Push + monitor CI/CD
14. Validate deployment
15. Continue with batch processing (next session)

Total time: 2-3 hours for thorough work
Result: High-quality, validated feature
```

## Validation Checklist (Every Change)

Before merging to main:

- [ ] All tests pass (`make test`)
- [ ] Local server reviewed (`make serve`)
- [ ] Endpoint checklist completed (see ENDPOINT_CHECKLIST.md)
- [ ] Screenshots taken and reviewed
- [ ] Sample data spot-checked
- [ ] No regressions found
- [ ] Changes documented in CHANGELOG
- [ ] Version bumped (if release)
- [ ] Commit messages clear
- [ ] CI/CD will pass (no conflicts/errors)

## Recovery from Hasty Work

If I've already pushed hastily:

1. Check CI/CD status
2. Fix any breaks immediately
3. Document what went wrong
4. Create proper workflow docs
5. Return to correct workflow
6. Learn from mistakes

---

**Key Takeaway**: Speed comes from building carefully over time, not rushing. Complex projects need patient, validated progress.
