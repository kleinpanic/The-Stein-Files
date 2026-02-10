# Development Flow - Autonomous Mode

## Pre-Work Checks

```bash
# 1. Ensure clean state
git status

# 2. Pull latest (if needed)
git pull origin main

# 3. Check current metrics
python3 -c "import json; c=json.load(open('data/meta/catalog.json')); 
cats=sum(1 for d in c if d.get('document_category'));
emails=[d for d in c if d.get('document_category')=='email'];
email_from=sum(1 for e in emails if e.get('from'));
people=len(set(p for d in c for p in d.get('person_names',[])));
ocr=sum(1 for d in c if d.get('ocr_applied'));
print(f'Categorized: {cats}/{len(c)} ({100*cats/len(c):.1f}%)');
print(f'Email From: {email_from}/{len(emails)}');
print(f'People: {people}');
print(f'OCR: {ocr}/{len(c)}')"
```

---

## Development Cycle

### 1. Branch (if major feature)
```bash
# For fixes: work directly on main
# For features: create branch
git checkout -b work/<feature-name>
```

### 2. Implement Changes
- Edit scripts/code
- Run incremental tests as you go
- Commit early and often

### 3. Run Tests Locally
```bash
# Full test suite
make test

# Quick validation only
.venv/bin/python -m scripts.validate

# Specific test file
.venv/bin/pytest tests/test_<name>.py -v
```

### 4. Extract & Build
```bash
# Re-extract if catalog changed
make extract

# Build site
make build
```

### 5. Local Validation
```bash
# Start local server
make dev

# In another terminal or via browser automation:
# - Check homepage loads
# - Search works
# - Filters work
# - PDF viewer works
# - Stats page loads
```

### 6. Git Diff Review
```bash
# Review all changes
git diff

# Review specific files
git diff scripts/extract.py

# Ensure no functionality lost
# Ensure no secrets exposed
# Ensure no debug code left
```

### 7. Commit
```bash
# Stage changes
git add -A

# Commit with clear message
git commit -m "type: description

- Detail 1
- Detail 2"

# Types: feat, fix, docs, test, refactor, style, chore
```

### 8. Merge to Main (if on branch)
```bash
# Ensure main is up to date
git checkout main
git pull origin main

# Merge branch
git merge work/<feature-name>

# Delete branch
git branch -d work/<feature-name>
```

### 9. Push
```bash
git push origin main
```

### 10. Validate Deployment
```bash
# Check GitHub Actions
gh run list --repo kleinpanic/The-Stein-Files --limit 1

# Wait for completion (usually 10-15 min)
# Then validate live site:
# https://kleinpanic.github.io/The-Stein-Files/
```

---

## Versioning Rules

| Change Type | Version Bump | Update CHANGELOG |
|-------------|--------------|------------------|
| Breaking changes | MAJOR (X.0.0) | Yes |
| New features | MINOR (x.Y.0) | Yes |
| Bug fixes | PATCH (x.y.Z) | Optional |
| Documentation | PATCH | No |

```bash
# Bump version
echo "1.5.3" > VERSION

# Tag release (on minor/major)
git tag -a v1.6.0 -m "Release v1.6.0"
git push origin v1.6.0
```

---

## Emergency Rollback

```bash
# Find last good commit
git log --oneline -10

# Reset to good commit (local only)
git reset --hard <sha>

# Force push (only if necessary)
git push origin main --force
```

---

## Heartbeat Integration

Each heartbeat (30 min):
1. Read TASK_DOCS.md - get next task
2. Read PROGRESS.md - check where we left off
3. Execute task (this flow)
4. Update PROGRESS.md with results
5. Update TASK_DOCS.md if task complete
6. Commit progress if changes made

---

## Quality Gates

Before considering work done:
- [ ] `make test` passes
- [ ] No regressions in key metrics
- [ ] Local site functions correctly
- [ ] Git history is clean
- [ ] Documentation updated if needed
- [ ] Version bumped appropriately

