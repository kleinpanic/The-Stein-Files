# Recommended Git Settings

These settings are optional but recommended for consistent local development.

```
git config pull.rebase false
git config init.defaultBranch main
git config core.autocrlf input
git config fetch.prune true
git config rerere.enabled true
```

Do not set `user.name` or `user.email` in repository config.
