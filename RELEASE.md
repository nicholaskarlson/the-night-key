# Release process

## Tagging (press-time)

1) Ensure `main` is green (CI passing).
2) Choose a version tag (e.g., `v0.1.0`).
3) Tag and push:

```bash
git tag -a v0.1.0 -m "v0.1.0 (book companion)"
git push --tags
```

## What a release means

A tag is what the book will reference so readers can reproduce the exact codebase used in print.
