# @travel/types

Tipe TypeScript yang di-generate dari skema OpenAPI `apps/api`.

Model Pydantic di FastAPI adalah **satu-satunya sumber kebenaran** untuk kontrak API. File
`src/api.ts` dihasilkan otomatis — jangan diedit manual, perubahannya bakal ketimpa.

## Cara generate

API harus jalan dulu, karena skemanya dibaca dari endpoint `/openapi.json` yang hidup:

```bash
# terminal 1
cd apps/api && uvicorn src.api:app --reload

# terminal 2
pnpm --filter @travel/types generate
```

Jalanin ulang tiap kali ada model Pydantic yang berubah di `apps/api/src/models.py`.
