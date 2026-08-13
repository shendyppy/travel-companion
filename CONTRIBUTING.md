# Working on this repo

## Language

Everything written for other developers is in **English**: commit messages, code
comments, docstrings, documentation, and the agent's system prompt.

The system prompt is English for a functional reason, not a stylistic one — a
prompt written in Indonesian biases every reply toward Indonesian regardless of
what the user actually wrote. The agent's *replies* are multilingual and mirror
the user's language.

## Branches

```
main                releases. only receives merges from development. always deployable.
└── development     integration branch. the default branch. work lands here first.
     ├── feat/*     new features
     ├── fix/*      bug fixes
     ├── refactor/* restructuring without behaviour change
     ├── chore/*    tooling, config, dependencies
     └── docs/*     documentation only
```

The rule: **always branch from `development`, always merge back into `development`.**
`main` is touched only at release time.

```bash
git checkout development
git pull
git checkout -b feat/what-you-are-doing
# ... work ...
git push -u origin feat/what-you-are-doing
gh pr create --base development
```

### Branch naming

`<type>/<kebab-case-scope>` — the scope describes *the work*, not the files touched.

| Good | Less good |
|---|---|
| `refactor/agent-core-litellm` | `refactor/agent-py` |
| `feat/rag-chromadb` | `feat/update` |
| `feat/byok-rate-limit` | `feat/phase-3` |

## Commits

`<type>(<scope>): <description>`

```
feat(agent): add tool-calling loop with an iteration cap
fix(llm): pass conversation history through to Gemini
refactor(providers): merge four location lookups into one
chore(deps): pin litellm
docs(readme): add local setup instructions
```

The body explains **why**, not **what** — the diff already shows what changed.

## Releasing

```bash
git checkout main
git merge --no-ff development
git tag -a v0.x.0 -m "..."
git push origin main --tags
```

## Local setup

```bash
pnpm install

cd apps/api
uv venv --python 3.13
uv pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # fill in your API keys
uvicorn src.api:app --reload  # http://127.0.0.1:8000/docs
pytest
```

Python 3.13, not 3.14 — some pinned versions in `requirements.txt` have no wheels
for 3.14 yet.

## Imports

Modules are imported one way only: `from src.<module> import ...`.

Earlier versions wrote every import twice inside a `try/except ImportError`, because
`PYTHONPATH=/app/src` made both `from config` and `from src.config` resolve. That
setting is gone. If you find yourself writing an import fallback, something else is
wrong.

## Never commit

This repository is **public**. Before pushing, check:

- No API keys, tokens, or credentials — including in comments, test fixtures, and
  error messages
- `.env` is never staged (`.gitignore` covers it, but check `git status` anyway)
- No runtime artefacts: `venv/`, `.venv/`, `node_modules/`, `dist/`, `.next/`,
  `*.log`, `data/trip_contexts.json`

```bash
git status --porcelain | grep -Ei "venv|node_modules|dist|\.env$|\.log$"   # must be empty
```
