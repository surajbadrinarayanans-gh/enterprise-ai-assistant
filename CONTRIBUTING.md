# Contributing

## Commit messages: Conventional Commits

> **Why this exists:** a consistent format makes history readable at a glance, lets tools generate changelogs
> and version numbers automatically, and shows reviewers what kind of change to expect before they open it.
> Spec: https://www.conventionalcommits.org

### Format
```
<type>(<optional scope>): <short summary in imperative mood>

<optional body: WHY the change was made, wrapped at ~72 chars>

<optional footer: BREAKING CHANGE: ..., Refs: #12>
```

### Types
| Type | Use it when you… | Example |
|---|---|---|
| `feat` | add a new feature or behaviour users can notice | `feat: add /healthz endpoint` |
| `fix` | fix a bug | `fix: return 404 when document id is unknown` |
| `docs` | change documentation only | `docs: add HLD v1.0` |
| `style` | change formatting only, no logic (spaces, quotes, newlines) | `style: format main.py with ruff` |
| `refactor` | restructure code without changing behaviour | `refactor: move health route into api/health.py` |
| `perf` | make it faster or use less memory | `perf: batch embedding calls` |
| `test` | add or change tests only | `test: add test for /healthz` |
| `build` | change build system or dependencies | `build: add pytest as dev dependency` |
| `ci` | change CI pipeline config | `ci: run tests on every pull request` |
| `chore` | do maintenance that fits nowhere else | `chore: add .gitignore` |
| `revert` | undo an earlier commit | `revert: feat: add /healthz endpoint` |

### Scope (optional)
The part of the system touched, in brackets: `feat(api): ...`, `fix(ingestion): ...`, `ci(github): ...`, `docs(adr): ...`.

### Breaking changes
Add `!` after the type, or a `BREAKING CHANGE:` footer, when existing clients would break:
`feat(api)!: rename /v1/ask response field "sources" to "citations"`

### Rules of thumb
1. **Imperative mood**, as if giving an order: "add", not "added" or "adds". Test: *"If applied, this commit will ___."*
2. Summary **under ~72 characters**, lowercase after the colon, no full stop at the end.
3. **One logical change per commit.** If the summary needs "and", it is probably two commits.
4. The summary says **what**; the body says **why**. The diff already shows how.
5. Never commit secrets, `.env` files or `.venv/`.

### How the type affects versions (semantic versioning, MAJOR.MINOR.PATCH)
| Commit | Version bump | Example |
|---|---|---|
| `fix` | PATCH | 1.4.2 → 1.4.3 |
| `feat` | MINOR | 1.4.2 → 1.5.0 |
| `!` / `BREAKING CHANGE` | MAJOR | 1.4.2 → 2.0.0 |
| `docs`, `chore`, `test`, `ci`, `style`, `refactor` | none | — |
