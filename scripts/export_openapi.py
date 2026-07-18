"""Regenerate docs/openapi.json from the FastAPI app's live OpenAPI schema.

Run whenever an endpoint/schema changes, so the committed file doesn't
silently drift from what the app actually serves — from the repo root:

    PYTHONPATH=. python scripts/export_openapi.py

Importing backend.app.main only constructs the FastAPI app (registers
routes/schemas) — it does not run the lifespan, so no real Postgres/Mongo/
AI-provider connection is needed just to export the schema.
"""

import json
from pathlib import Path

from backend.app.main import app

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"


def main() -> None:
    schema = app.openapi()
    OUTPUT_PATH.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
