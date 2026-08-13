# Alur Kerja

## Branch

```
main                rilis. cuma nerima merge dari development. selalu deployable.
└── development     branch integrasi. default branch. semua kerjaan nyatu di sini dulu.
     ├── feat/*     fitur baru
     ├── fix/*      perbaikan bug
     ├── refactor/* restrukturisasi tanpa ngubah perilaku
     ├── chore/*    tooling, config, dependency
     └── docs/*     dokumentasi doang
```

Aturan intinya: **selalu cabang dari `development`, balik lagi ke `development`.**
`main` cuma disentuh pas rilis.

```bash
git checkout development
git pull
git checkout -b feat/nama-pekerjaan
# ... kerjain ...
git push -u origin feat/nama-pekerjaan
gh pr create --base development
```

### Penamaan branch

`<tipe>/<scope-kebab-case>` — scope-nya jelasin *pekerjaannya*, bukan file yang disentuh.

| Bagus | Kurang bagus |
|---|---|
| `refactor/agent-core-litellm` | `refactor/agent-py` |
| `feat/rag-chromadb` | `feat/update` |
| `feat/byok-rate-limit` | `feat/fase-3` |

## Commit

`<tipe>(<scope>): <deskripsi>` — ngikutin konvensi yang udah dipakai di repo ini.

```
feat(agent): tambah loop tool-calling dengan batas iterasi
fix(llm): teruskan riwayat percakapan ke Gemini
refactor(providers): gabung 4 implementasi lookup lokasi jadi satu
chore(deps): pin litellm
docs(readme): tambah petunjuk setup lokal
```

Body-nya isi **kenapa**, bukan **apa** — diff-nya udah nunjukin apa yang berubah.

## Rilis

```bash
git checkout main
git merge --no-ff development
git tag -a v0.x.0 -m "..."
git push origin main --tags
```

## Setup lokal

```bash
pnpm install

# API — pakai uv (jauh lebih cepat dari pip)
cd apps/api
uv venv --python 3.13
uv pip install -r requirements.txt
cp .env.example .env          # isi API key-nya
uvicorn src.api:app --reload  # http://127.0.0.1:8000/docs
```

Python 3.13 dipakai, bukan 3.14 — beberapa versi yang di-pin di `requirements.txt` wheel-nya
belum ada buat 3.14.

## Yang jangan sampai ke-commit

Repo ini **public**. Sebelum push, pastiin:

- Nggak ada API key, token, atau credential — termasuk di komentar, test fixture, dan pesan error
- `.env` nggak pernah ke-stage (`.gitignore` udah nutup, tapi tetap cek `git status`)
- Nggak ada artefak runtime: `venv/`, `.venv/`, `node_modules/`, `dist/`, `.next/`, `*.log`,
  `data/trip_contexts.json`

```bash
git status --porcelain | grep -Ei "venv|node_modules|dist|\.env$|\.log$"   # harus kosong
```
