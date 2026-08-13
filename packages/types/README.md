# @travel/types

TypeScript types generated from the `apps/api` OpenAPI schema.

The Pydantic models in FastAPI are the **single source of truth** for the API
contract. `src/api.ts` is generated — do not edit it by hand, your changes will be
overwritten.

## Generating

The API has to be running, because the schema is read from its live
`/openapi.json`:

```bash
# terminal 1
cd apps/api && uvicorn src.api:app --reload

# terminal 2
pnpm --filter @travel/types generate
```

Re-run this whenever a Pydantic model changes in `apps/api/src/models.py`.
