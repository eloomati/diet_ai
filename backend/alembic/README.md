# Alembic (Backend)

To run migrations from project root:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```
Weryfikacja:

```bash
docker compose ps
curl http://localhost:8000/health