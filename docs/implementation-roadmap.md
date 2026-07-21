# Mycelo - Implementation Roadmap

## Purpose

This document defines the implementation order of the Mycelo project.

The goal is to build the system incrementally while keeping architecture clean.

Each phase should result in a working part of the system.

**History**: Phases 0-11 (backend + the full frontend, Etap 0-6) are
done — see `docs/implementation/implementation-roadmap-done190726.md`
for their complete stage-by-stage log. This document picks up at
Phase 12.

---

## Status (as of 2026-07-20)

```
Phase 0-11  - Foundation through Testing   DONE — see the archived roadmap
Phase 12    - Dietitian Marketplace,       IN PROGRESS —
              Admin Panel & Roles           Etap 0 (Roles & RBAC): DONE
                                            Etap 1 (Dietitian applications
                                              & profile): DONE
                                            Etap 2 (Admin module +
                                              frontend-admin): DONE
                                            Etap 3 (Transactions
                                              module): DONE
                                            Etap 4 (Marketplace &
                                              reviews): DONE
                                            Etaps 5-6: not started
```

---

# Phase 12 - Dietitian Marketplace, Admin Panel & Roles

## Goal

Turn the app from "AI-only diet assistant" into a marketplace: users can
hire a real human dietitian (browse, pay a stand-in "paid" flag, chat,
get reviewed), dietitians apply and manage a public profile, and admins
run the whole thing from a separate panel.

## Grounding — what exists today vs. what's new

Checked before writing this plan, so it's grounded rather than guessed:

- **No role system exists.** `User` (`backend/modules/identity/domain/entities/user.py`)
  has no role/permission field at all — `status` (ACTIVE/INACTIVE/BLOCKED)
  is the only access-control axis today. Adding roles is a new column +
  migration + value object, no existing scaffolding.
- **Module convention** (confirmed via the `nutrition` module): each
  module gets `api/{router.py, routers/, schemas/, dependencies/}`,
  `application/{use_cases/, dto/, ports/}`,
  `domain/{entities/, value_objects/, repositories/, services/,
  exceptions/}`, `infrastructure/{repository/, mappers/, documents/}`,
  `tests/`. Wired into the app via `backend/app/api_router.py`
  (`include_router`) and `backend/app/main.py`'s lifespan for anything
  needing startup/shutdown (a Kafka producer/consumer will live there).
  New modules in this phase follow this exact shape.
- **No messaging/queue infrastructure at all** — no Kafka, no Redis, no
  Celery, nothing. `docker-compose.yml` today: `db`, `mongo`, `ollama`,
  `mailhog`, `sftp`, `backend`, `frontend`. Kafka is genuinely new
  infrastructure, not a swap-in for something existing.
- **No real-time channel** — frontend is 100% REST + TanStack Query,
  no WebSocket/SSE anywhere. Per the answered design questions below,
  this phase stays that way (polling), so this isn't a gap to close.
- **No file-upload handling anywhere** — no `UploadFile` usage, no
  S3/MinIO client. The existing SFTP client (Phase 9) is outbound-only
  (CSV export archival), not a pattern for accepting user photo
  uploads — a new upload path is built from scratch.
- **`MessageRole` is `USER`/`ASSISTANT`/`SYSTEM`** — no concept of a
  human sender. Rather than overload the AI `Conversation`/`Message`
  aggregate (which carries AI-specific concerns: categories, prompt
  building, LLM provider selection) with human-chat concerns (plan
  attachments, a paid-engagement lifecycle), dietitian↔user messaging
  gets its **own** aggregate in a new module — see Etap 5. The existing
  AI conversation module is untouched by this phase.

## Design decisions already made (confirmed with the user before writing this plan)

1. **Real-time delivery: polling, not WebSockets.** New messages and
   notifications (transaction paid, new dietitian message) are
   delivered the same way everything else in this app is — TanStack
   Query refetch/polling against REST endpoints. Kafka's role is
   backend-internal event distribution (e.g. `TransactionPaid` event →
   a consumer creates a `Notification` row) — it never needs to reach
   the browser directly.
2. **`frontend-admin` is a fully separate Vite/React/TS app** — its own
   `package.json`, its own dev server port, its own `docker-compose.yml`
   service — not a protected route group inside the existing `frontend/`.
   Shares no runtime code with `frontend/` (a shared `packages/ui` or
   similar is explicitly out of scope unless real duplication pain shows
   up later — not assumed up front).
3. **Dietitian profile photos: local disk / a Docker volume**, served
   via a plain static-file route on the backend — no MinIO/S3. Consistent
   with the project's existing self-hosted-everything approach (SFTP for
   CSV export, Mailhog for email) rather than adding another object-store
   container alongside the already-planned Kafka broker.

## Etap breakdown (prospective — implemented and retro-noted stage by stage, same as every prior phase)

---

### Etap 0 — Roles & RBAC foundation

Goal: introduce the role system every later etap depends on, without
touching any other module's behavior yet.

- **Stage 1 — `Role` value object + migration — DONE**: `Role` enum
  (`USER`, `DIET_USER`, `ADMIN`, `SUPER_ADMIN`), new `role` column on
  `users` (`backend/alembic/version/20260719_06_user_roles.py`, default
  `'USER'` for every existing row via `server_default`). `User` entity
  gained `role: Role = Role.USER` + a `change_role(new_role)` method +
  a new `UserRoleChanged` domain event.
  **Deviation from the sketch above**: `change_role()` does *not*
  itself validate "only `SUPER_ADMIN` can promote to `ADMIN`" — that's
  an authorization rule (who's allowed to call this), not a domain
  invariant (a fact about the entity's own state), so it's deferred to
  the API layer's `require_role` dependency (Stage 2) guarding whatever
  endpoint calls `change_role` (Stage 3), matching how `assert_can_authenticate()`
  is about the user's *own* state, never about a caller's permission.
  The entity stays a plain setter + event; the dietitian-approval
  `USER`→`DIET_USER` promotion (Etap 1) is just another caller of the
  same method, gated by its own endpoint's role requirement — no
  transition-legality table needed inside the entity.
  **Real bug found and fixed while wiring persistence**:
  `SqlAlchemyUserRepository.save()`'s update branch
  (`infrastructure/persistence/repository/sqlalchemy_user_repository.py`)
  set `existing.{email,password_hash,status,email_verified,updated_at}`
  field-by-field on an already-loaded row, but the new `role` field was
  missing from that list — a role change would have applied to the
  in-memory `User` object, returned success, and then silently
  vanished on the next fetch. Caught before any endpoint existed to
  call it, purely by re-reading the repository during this stage rather
  than assuming `to_model()`'s mapping (used only for brand-new rows)
  covered updates too.

  Exit criteria met: new unit tests (`Role`'s 4 members; `User.create()`
  defaults to `Role.USER`; `change_role()` updates the field and emits
  `UserRoleChanged`), `test_domain_exports.py` extended. Full backend
  suite **356/356 passed** (up from 353), including the migration
  itself — `conftest.py` runs a real `alembic upgrade head` against the
  ephemeral test Postgres before every run, so this wasn't just an ORM
  check; `alembic history` confirmed a clean single-head chain with no
  branching.

- **Stage 2 — RBAC dependency — DONE**: `require_role(*roles)` added to
  `current_user.py` alongside `get_current_user` — a dependency
  *factory* (`Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN))`)
  that builds on `get_current_user` for the token/session work and only
  adds the role check on top, raising `AppException(FORBIDDEN, 403)`
  when the caller's role isn't in the allowed set. `GET /auth/me`'s
  response (`MeResponse`) and the handler both gained `role`.
  Tested by calling the returned inner function directly with
  constructed `User`s (bypassing the HTTP layer entirely) rather than
  inventing a throwaway protected route just to exercise it — Stage 3's
  real `PATCH /admin/users/{id}/role` endpoint will be the first genuine
  HTTP-level test of this dependency, so building a fake one now would
  just be temporary scaffolding.

  Exit criteria met: 4 new tests for `require_role` (allows a matching
  role, allows any role in a multi-role allow-list, rejects an
  out-of-set role with 403/`FORBIDDEN`, rejects `DIET_USER` against a
  `SUPER_ADMIN`-only gate) plus the two existing `/me` API tests
  extended to assert `role`. Full backend suite **360/360**.
  Live-verified against the real Docker backend (not just pytest): a
  brand-new `register → login → me` round-trip returned
  `"role": "USER"`, and — importantly — logging in with an account
  created *before* this migration (`smoketest-etap6@example.com`, from
  Phase 10's frontend smoke walkthrough) also returned `"role": "USER"`,
  confirming the migration's `server_default` backfill actually took
  effect on real pre-existing rows, not just fresh ones.
- **Stage 3 — Role-change endpoint — DONE**: `PATCH /admin/users/{user_id}/role`
  (`SUPER_ADMIN`-only via `Depends(require_role(Role.SUPER_ADMIN))`) —
  lives in the identity module (not Etap 2's admin module yet), exactly
  as planned, since it's really an Identity-module concern (mutating a
  `User`); the admin module in Etap 2 will just call it. New
  `ChangeUserRoleUseCase`/`ChangeUserRoleCommand` (loads the target user
  via `UserRepository`, calls `user.change_role(...)`, saves — a
  `UserNotFoundError` maps to 404 `NOT_FOUND`, matching the direct-ID-
  lookup convention used elsewhere in the app, unlike the 400 mapping
  `UserNotFoundError` gets in the email-verification flow where it's
  really a token-validity edge case).

  Exit criteria met: 5 new tests in `test_change_user_role_api.py`
  (SUPER_ADMIN can change a role — including a persistence check via a
  follow-up real `/auth/me` call, not just trusting the response body;
  every other role gets 403; an unknown user id gets 404; a
  non-enum role value gets 422; no auth at all gets 401). Non-caller
  setup uses `app.dependency_overrides[get_current_user]` to become
  whichever role a given test needs — the same override mechanism
  `test_auth_me_api.py` already established — rather than inventing new
  direct-Postgres test scaffolding just to mint a `SUPER_ADMIN` caller.
  Full backend suite **365/365**.

  Live-verified against the real Docker backend end to end: registered
  two real users, promoted one to `SUPER_ADMIN` via a direct
  `UPDATE users SET role = ...` (there is no self-escalation path by
  design, and no bootstrap-admin seed mechanism exists yet — noted
  below as an open item for Etap 2, not solved here), logged in as that
  real `SUPER_ADMIN`, called the real endpoint against the second
  user's real id, confirmed `DIET_USER` in the response, then — a
  second, independent real login as the *target* user — confirmed
  `/auth/me` also returned `DIET_USER` (real persistence, not just
  the response echoing the request). Also confirmed a real 403 when
  that same now-`DIET_USER` account tried calling the endpoint itself.
  Clean backend logs throughout, `docker compose down` after.

  **Open item flagged, not solved now**: there's currently no way to
  create the *first* `SUPER_ADMIN` in a real deployment short of a
  direct SQL `UPDATE` (fine for this dev demo, not fine for anything
  real) — Etap 2 (or a dedicated small stage before it) should add a
  proper bootstrap mechanism (e.g. a one-off management script, or a
  `SUPER_ADMIN_SEED_EMAIL` env var the app promotes on startup).

- **Stage 4 — Docs sync — DONE**: unit/integration tests were already
  added incrementally in Stages 1-3 (not deferred here, unlike a first
  read of this plan might suggest) — this stage was pure docs, no code
  changes, so no test run was needed for it at all (per the updated
  testing-scope guidance). `docs/api.md`'s `/me` response gained `role`
  plus a full new `PATCH /admin/users/{user_id}/role` section (request/
  response/errors, including the "no self-escalation path" note);
  `docs/domain-model.md`'s `User` gained the `role` field, a rule
  explaining `change_role()`'s authorization split, and `UserRoleChanged`
  in the domain events list; `docs/openapi.json` regenerated via
  `scripts/export_openapi.py` and confirmed to contain the new endpoint.

This closes out **Etap 0 (Roles & RBAC foundation) in full.**

---

### Etap 1 — Dietitian applications & profile (backend + main-app frontend)

Goal: a `USER` can apply to become a dietitian; once approved
(Etap 2 handles the admin-side approval action), they get a public
profile they manage from inside the existing `frontend/` app.

- **Stage 1 — New `backend/modules/dietitian/` module — DONE**:
  **Deviation from the sketch above, per explicit user direction mid-stage**:
  Mongo was the original plan (matching `conversation`/`nutrition`'s
  document-shaped choice), but the user asked for the dietitian profile
  to be "a separate table with a proper connection to the user" —
  Postgres, relational, FK to `users.id`. Both `DietitianApplication`
  and `DietitianProfile` moved to Postgres for consistency within the
  module (one persistence technology, not split), which also sets up
  cleanly for Etap 3/4's `transactions`/reviews tables (already planned
  as Postgres) to join against a dietitian's profile without a cross-
  database join. New module built mirroring `identity`'s exact
  SQLAlchemy convention (not `nutrition`'s Mongo one): domain entities →
  `infrastructure/persistence/models` (SQLAlchemy) → mappers →
  repositories, plus `backend/alembic/version/20260719_07_dietitian_tables.py`.
  - `DietitianApplication`: `status` (`PENDING`/`APPROVED`/`REJECTED`),
    `experience`/`diplomas` (Postgres `TEXT[]`, a first for this
    codebase — every prior Postgres column has been scalar)/`description`,
    `reviewed_by`/`reviewed_at` (nullable FK to `users.id`,
    `ON DELETE SET NULL` — losing the reviewing admin account shouldn't
    cascade-delete the application it reviewed). `approve()`/`reject()`
    guard against re-reviewing an already-decided application
    (`ApplicationAlreadyReviewedError`) — a genuine domain invariant
    about the application's *own* state, unlike Etap 0's role-transition
    authorization question, which was about the *caller's* permission
    and therefore stayed out of the entity.
  - `DietitianProfile`: kept deliberately minimal for this stage —
    `experience`/`diplomas`/`description` only. Photos (Stage 3) and the
    two fixed offer prices (Stage 4) get their own columns via their own
    migrations when those stages actually need them, mirroring how
    Etap 0 added `role` as its own migration rather than guessing the
    full shape upfront.
  - Both tables: `user_id` is a `UNIQUE` FK to `users.id` (`ON DELETE
    CASCADE`) — one row per user, ever. No re-application-after-rejection
    flow exists yet (flagged as a scope decision, not an oversight — the
    user's spec didn't call for one; revisit if needed by dropping the
    unique constraint and querying "latest" instead of a 1:1 row).
  - **Applied the Etap-0 lesson directly**: both repositories' `save()`
    update-branch lists *every* mutable field explicitly, with an
    inline comment pointing at the exact bug Etap 0 Stage 1 found (a
    missing field there was `role`; the equivalent mistake here would
    have been forgetting `status` on the application, silently breaking
    approve/reject persistence).

  Exit criteria met (scoped per the new testing-scope guidance — this
  stage is fully isolated with no other module depending on it yet, so
  only the new module's own tests ran, not the full suite): 11 new
  entity unit tests. `pytest.ini` gained the new test path.
  Live-verified against both the ephemeral test Postgres (implicitly,
  via the autouse migration fixture succeeding) and the real Docker dev
  Postgres — confirmed via `docker compose logs` that
  `20260719_07_dietitian_tables` applied cleanly, and via `psql \d` that
  both tables have the exact FKs/unique constraints/array column
  designed above. Clean backend logs, `docker compose down` after.
- **Stage 2 — Apply flow — DONE**: `POST /dietitian/applications`
  (any authenticated `USER`, one pending application per user — the
  DB's `UNIQUE` constraint on `user_id` from Stage 1 backs this, and the
  use case also checks `get_by_user_id` first to return a clean 409
  rather than surfacing a raw integrity-error) and
  `GET /dietitian/applications/me` (404 when none submitted yet — lets
  the frontend distinguish "no application" from "application exists"
  without a separate boolean flag). New use cases
  (`SubmitDietitianApplicationUseCase`, `GetMyDietitianApplicationUseCase`)
  and their DTOs/exceptions threaded through `application/__init__.py`
  exactly like Etap 0's `ChangeUserRoleUseCase` was. New
  `api/schemas/application_schemas.py`, `api/dependencies/dietitian_dependencies.py`,
  `api/routers/application_router.py` (prefix `/dietitian`), and a new
  module-level `api/router.py` aggregator — this module had no API
  surface mounted at all before this stage, so `backend/app/api_router.py`
  also gained its `dietitian_router` import/include.
  **Shared dependency promoted before the new code needed it**:
  `get_db_session` moved from `identity/api/dependencies/auth_dependencies.py`
  to `backend/shared/database/postgres.py` (re-exported from its old
  location so identity's existing imports keep working unchanged) —
  the same "promote once a second module needs an identity-only utility"
  pattern Phase 8 established for `SecureToken`/JSON-Schema helpers.
  Frontend: `frontend/src/api/dietitian.ts` (types +
  `getMyDietitianApplication`/`submitDietitianApplication`) and a new
  `DietitianApplicationSection.tsx`, mounted at the bottom-right of the
  Profil tab (`ProfilTab.tsx`) exactly where the mockup spec called for
  it. It queries `GET .../me` on mount: 404 → the "Zgłoszenie dietetyka"
  button, which opens a `Dialog` form (experience/diplomas/description,
  diplomas as one-per-line free text) reusing the existing design system
  (`FieldError`, the new `Textarea` shadcn primitive, `Badge` for the
  post-submit status); any other status → a `Badge` showing the Polish
  status label instead of the button, so a pending/approved/rejected
  application can never be resubmitted from the UI.

  Exit criteria met (scoped, not the full suite — this stage only
  touches the new `dietitian` module and one already-isolated
  `get_db_session` refactor): the `get_db_session` move was verified by
  running all of `identity`'s tests (128 passed, since that dependency
  threads through identity's whole API surface) rather than just the
  new file; the apply-flow itself added 2 new API test files' worth of
  coverage — `test_submit_dietitian_application_use_case.py` (3 tests),
  `test_get_my_dietitian_application_use_case.py` (2 tests), and
  `test_dietitian_application_api.py` (6 tests, including the 409-on-
  duplicate and 401-when-unauthenticated cases) — 22 tests total in the
  module. Frontend: a new `DietitianApplicationSection.test.tsx` (2
  tests: button→submit→badge, and badge-shown-directly for an existing
  application) plus `ProfilTab.test.tsx`'s 4 existing tests updated to
  mock the new `/dietitian/applications/me` call (404) so they stay
  deterministic. `npx tsc --noEmit` and `npm run build` both clean.

  Live-verified against the real Docker backend: registered a fresh
  user, confirmed `GET .../me` → 404 before applying, `POST` → 201 with
  `status: "PENDING"`, `GET .../me` → 200 with the same row, and a
  second `POST` → 409 — all via `curl`, then cross-checked the row
  directly with `psql \d dietitian_applications` / `SELECT ...`. Then
  live-verified the frontend in a real browser (Vite dev server +
  Docker backend): opened the Profil tab, confirmed the button renders
  bottom-right, filled and submitted the form, confirmed the dialog
  closed and the button was replaced by a "Zgłoszenie w trakcie
  rozpatrywania" badge, then closed and reopened the Profil modal to
  confirm the badge is refetched from the server (not just local state)
  rather than resetting to the button. Dev server and
  `docker compose down` both stopped after.
- **Stage 3 — Photo upload — DONE**: `POST /dietitian/profile/photos`
  (multipart upload, gated by `require_role(Role.DIET_USER)` — reusing
  Etap 0's dependency directly, cross-module, exactly as designed).
  `DietitianProfile` gained a `photos: tuple[str, ...]` field (new
  migration `20260719_08_dietitian_photos.py`, chained after Stage 1's)
  and an `add_photo()` domain method enforcing a hard cap of 3 — a
  `MAX_PROFILE_PHOTOS` constant shared between the entity's own
  defensive check and the use case's earlier check (see below).
  **Applied the Etap-0 lesson a second time**: `SqlAlchemyDietitianProfileRepository.save()`'s
  update branch gained `existing.photos = list(profile.photos)`, with
  the same inline comment as Stage 1's application repository, this
  time naming `photos` as the field that would have silently vanished.
  New `FileStorage` port (`application/ports/file_storage.py`) +
  `LocalDiskFileStorage` adapter (`infrastructure/storage/`) per the
  confirmed local-disk decision — the adapter never trusts the client's
  filename beyond its extension (generates its own UUID-based stored
  name), which also rules out path traversal by construction, not by
  sanitization. `UploadDietitianProfilePhotoUseCase` checks the 3-photo
  cap *before* calling `FileStorage.save()`, not after — so a rejected
  4th upload never writes an orphaned file to disk (verified by a
  dedicated use-case test asserting the fake storage recorded nothing).
  API layer validates content-type (`image/jpeg`/`png`/`webp` only) and
  a 5 MB size cap before ever reaching the use case. New settings
  (`dietitian_photos_storage_dir`, `dietitian_photos_base_url`) and a
  `StaticFiles` mount added in `main.py::create_app()` to actually serve
  the stored files back. Added the `python-multipart` dependency
  (required by FastAPI's `UploadFile`/`File(...)`, not previously
  needed anywhere in this codebase) to `requirements.txt`.

  **Genuine sequencing gap, called out rather than worked around**:
  this stage assumes a `DietitianProfile` already exists, but the only
  thing that will ever create one is Etap 2's admin-approval flow,
  which doesn't exist yet — there is still no way for a user to become
  `DIET_USER` with a profile through the API alone. Tests and live
  verification both seed that state directly against Postgres (a new
  `_test_db_session()` helper using its own dedicated engine, and a
  direct `psql UPDATE`/`INSERT` for live verification) — the same
  "bypass via direct SQL until the real flow exists" pattern already
  used for the first SUPER_ADMIN in Etap 0. This is a stand-in, not a
  design decision: once Etap 2 exists, the real approve-application
  action becomes the only path that creates a profile.

  Exit criteria met (scoped — this stage only touches the new
  photo-upload path within the already-isolated `dietitian` module):
  domain tests for `add_photo()` (2), a `LocalDiskFileStorage` unit test
  (2, including one asserting a path-traversal-shaped filename is
  ignored), use-case tests against an in-memory profile repo + fake
  storage (3), and an API test file (6: success, 401, 403-without-role,
  404-without-a-profile, 400-unsupported-type, 400-on-a-4th-photo) — 35
  tests total in the module (up from 22 after Stage 2).

  Live-verified against the real Docker backend: confirmed the new
  migration applied via `docker compose logs`; registered a user,
  promoted it to `DIET_USER` and seeded a profile via direct `psql`,
  then via `curl` uploaded 3 photos (each 201, `photos` array growing),
  confirmed a 4th → 400 and a `application/pdf` upload → 400, and
  confirmed the stored file is byte-for-byte fetchable through the
  static route (`GET http://localhost:8000/static/dietitian-photos/<name>`
  returned the exact uploaded content). Cross-checked
  `dietitian_profiles.photos` directly via `psql \d` / `SELECT`.
  `docker compose down` after. The locally-created `./data/dietitian_photos/`
  scratch directory (a side effect of importing `main.py` during local
  verification) was deleted and added to `.gitignore`.
- **Stage 4 — Dietitian's own profile management (main app) — DONE**:
  the Profil modal now conditionally gains **"Profil dietetyka"** and
  **"Transakcje"** tabs, gated purely on `user.role === 'DIET_USER'`
  (`ProfileModal.tsx`) — a regular `USER` never sees either tab. Reviews
  (Etap 4) and real transaction data (Etap 3) are deliberately *not*
  built here — the "Transakcje" tab is a shell (`TransakcjeTab.tsx`, an
  `EmptyState` placeholder) per the plan's own note that Etap 3 wires
  its actual content; a reviews section wasn't added at all, since the
  plan attributed it to Etap 4 specifically, not this stage.
  Backend gained the rest of the profile-management surface beyond
  Stage 3's upload-only endpoint: `GET /dietitian/profile/me`,
  `PUT /dietitian/profile` (partial update, reusing Stage 1's
  `update_details()` domain method verbatim), and
  `DELETE /dietitian/profile/photos/{index}` (new `remove_photo()`
  domain method, symmetric with `add_photo()` — an out-of-range index
  raises `InvalidDietitianProfileError`, mapped to 400). All three
  reuse `require_role(Role.DIET_USER)` directly, unchanged since Etap 0.
  Frontend: `DietitianProfileTab.tsx` (edit form mirroring
  `NutritionProfileForm`'s save-mutation pattern, plus a photo gallery —
  thumbnails with a hover-remove button, an "add" button disabled at the
  3-photo cap) and a new `frontend/src/lib/apiFetch.ts` capability:
  `authedFetch` now detects a `FormData` body and skips both
  JSON-stringifying it and forcing a `Content-Type` header, letting the
  browser set its own multipart boundary — the first real upload from
  the frontend since the CSV *export* work only ever needed downloads.
  A new `resolveStaticUrl()` helper resolves a root-absolute photo path
  (e.g. `/static/dietitian-photos/x.jpg`) against the API's own origin,
  since those files are served outside the `/api/v1` prefix and a bare
  `<img src>` would otherwise resolve against the frontend's own origin.
  **Frontend type gap fixed in passing**: `MeResponse` never gained a
  `role` field back in Etap 0 Stage 4 even though the backend has
  returned it since then — this stage's tab-gating needed it, so it was
  added now (`UserRole` union type + `role: UserRole` on `MeResponse`).

  **Genuine repo-hygiene bug found and fixed while checking `git
  status` before this retrospective**: `.gitignore`'s bare `lib/` /
  `lib64/` entries (meant for Python's packaging output) also matched
  `frontend/src/lib/` at any depth, since an unanchored gitignore
  pattern matches every directory with that name regardless of
  location. Consequence: **all 12 files under `frontend/src/lib/`
  (`apiFetch.ts`, the entire `auth/` module — `AuthContext.tsx`,
  `useAuth.ts`, `tokenStore.ts` — plus `toast.ts`, `queryClient.ts`,
  `utils.ts`, `profileOptions.ts`, `categoryOptions.ts`, and 2 test
  files) had never been committed in any prior session**, despite all
  of Phase 10 being marked DONE — a fresh clone of this repo would not
  have built the frontend at all. Fixed by anchoring both patterns to
  the repo root (`/lib/`, `/lib64/`) and staging the 12 previously-
  untracked files alongside the `.gitignore` fix (confirmed via the
  user) — left for the user to commit, per the standing rule.

  Exit criteria met (scoped — this stage only extends the already-
  isolated `dietitian` module and adds new frontend components; the
  `apiFetch.ts` change is small and additive, not a behavior change to
  the existing JSON path): domain tests for `remove_photo()` (2),
  three new use-case test files (`get_my_dietitian_profile`,
  `update_dietitian_profile`, `remove_dietitian_profile_photo` — 8
  tests total), and a new `test_dietitian_profile_api.py` (7 tests:
  get/update/remove success and error paths) — 53 tests total in the
  module (up from 35 after Stage 3). The two API test files' shared
  DB-seeding helpers (`_test_db_session`, `promote_to_dietitian(_with_profile)`)
  were extracted into a new `tests/db_helpers.py` rather than
  duplicated a second time. Frontend: `DietitianProfileTab.test.tsx`
  (4), `TransakcjeTab.test.tsx` (1), and `ProfileModal.test.tsx` gained
  2 new tests asserting the tabs are hidden for `USER` and shown for
  `DIET_USER` — full suite run since `apiFetch.ts`/`auth.ts` are
  genuinely shared, cross-cutting files (105 passed, up from 105 total
  including the new ones). `npx tsc --noEmit` and `npm run build` both
  clean.

  Live-verified against the real Docker backend via `curl` (registered
  a user, promoted to `DIET_USER` with a seeded profile via direct SQL —
  same Etap-2-doesn't-exist-yet stand-in as Stage 3 — then confirmed
  `GET`/`PUT`/upload/`DELETE` all round-trip correctly, and that
  `GET /auth/me` now returns `role: "DIET_USER"`). **Browser-based UI
  verification could not be completed this stage**: the Claude-in-
  Chrome extension entered a persistent `Cannot access a chrome-
  extension:// URL of different extension` error across two separate
  tabs and did not recover — flagged rather than worked around, per the
  guidance to stop after repeated tool failures rather than loop.
  Substituted the `curl`-based backend verification above plus the full
  automated test suites (53 backend, 105 frontend) as the closest
  available substitute; an actual in-browser pass of the new tabs is
  still outstanding and should happen opportunistically once the
  extension recovers. `docker compose down` after.
- **Stage 5 — Tests + docs sync — DONE**: closing stage for Etap 1 as a
  whole, so — per the standing testing-scope rule — the *full* suite
  ran rather than just the dietitian module.
  - `docs/api.md`: new **Dietitian API** module section covering all 6
    endpoints built across Stages 2-4 (`POST`/`GET .../applications*`,
    `GET`/`PUT .../profile`, `POST`/`DELETE .../profile/photos*`), plus
    an Overview bullet mentioning dietitian applications/profiles.
  - `docs/domain-model.md`: new **Dietitian Context** (bounded contexts)
    and **Dietitian Domain** section (`DietitianApplication`,
    `DietitianProfile` — both aggregate roots, their rules, and an
    explicit note that neither currently emits domain events, unlike
    `User.change_role()`), both added to Aggregates/Persistence Mapping,
    and a short addendum on the Relationships diagram. Inserting a new
    domain section required renumbering sections 7-13 to 8-14 — done
    and verified sequential.
  - `docs/openapi.json` regenerated via `scripts/export_openapi.py` —
    confirmed the new dietitian paths are present.
  - This document's own status block flipped Phase 12 from PLANNED to
    IN PROGRESS, with Etap 0/Etap 1 marked DONE.

  **Full-suite closing gate run (backend + frontend)**: frontend clean
  (105/105). Backend: 416 passed, **2 pre-existing failures unrelated to
  this etap** — `test_diet_plan_api.py::test_list_diet_plans_from_today_includes_todays_plan`
  and `::test_list_diet_plans_to_in_the_past_excludes_todays_plan`
  (Phase 10 nutrition tests, untouched this whole session). Root cause:
  both compute `date.today()` in the *local* timezone (CEST, UTC+2) and
  compare it against `DietPlan.created_at`, which is stored in UTC —
  for roughly 2 hours after local midnight but before UTC midnight,
  local "today" and the plan's actual UTC-dated `created_at` disagree
  by one day, flipping both tests' expected result. Confirmed by
  comparing `date.today()` vs `datetime.now(UTC).date()` at the time of
  the run (`2026-07-20` vs `2026-07-19`) — a genuine latent bug, but a
  clock-window flake unrelated to any dietitian-module change, so it
  wasn't fixed here; left as a flagged, separately-scoped issue for
  whoever next touches `nutrition`'s date-range filtering.

Etap 1 (Dietitian applications & profile) is now **DONE** — all 5
stages complete: the module (Postgres, Stage 1), the apply flow
(Stage 2), photo upload (Stage 3), the dietitian's own profile
management UI (Stage 4), and this docs/tests sync (Stage 5).

---

### Etap 2 — Admin backend module + `frontend-admin` app

Goal: the actual admin panel — a separate app, separate backend module,
gated to `ADMIN`/`SUPER_ADMIN`.

- **Stage 1 — New `backend/modules/admin/` module — DONE**: no new
  persistence of its own, exactly as planned — its use cases call the
  existing `identity`/`dietitian`/`nutrition`/`conversation` modules'
  repository ports directly, reusing their already-exported API-layer
  provider functions (`get_conversation_repository`,
  `get_nutrition_profile_repository`, `get_diet_plan_repository`,
  `get_diet_plan_export_repository`, `get_dietitian_application_repository`,
  `get_dietitian_profile_repository`) the same way every module already
  reuses identity's `get_current_user`/`require_role` — so admin logic
  stays a thin orchestration layer, not a second source of truth, and no
  new repository implementation had to be written for it.
  Endpoints, all gated by `require_role(ADMIN, SUPER_ADMIN)`:
  `GET /admin/users`, `POST /admin/users/{id}/activate`,
  `POST /admin/users/{id}/ban`, `DELETE /admin/users/{id}`,
  `GET /admin/dietitian-applications` (optional `?status=` filter),
  `POST /admin/dietitian-applications/{id}/approve` (promotes the user
  to `DIET_USER` and creates their `DietitianProfile` — see below),
  `POST /admin/dietitian-applications/{id}/reject`.

  **New repository capabilities added to support this stage** (each
  module's own domain/infrastructure layers, not admin's): `UserRepository`
  gained `list_all()`/`delete()`; `DietitianApplicationRepository`
  gained `list_all(status=None)`; `NutritionProfileRepository`,
  `DietPlanRepository`, `DietPlanExportRepository` each gained
  `delete_by_user_id()` (Mongo bulk deletes — nothing in this codebase
  had ever deleted these before). `ConversationRepository` needed no
  change — `list_by_user()` + `delete(id)` already existed and compose
  into exactly what `DeleteUserUseCase` needs.

  **`DELETE /admin/users/{id}`'s cross-database cleanup, flagged before
  this stage and now built exactly as flagged**: `DeleteUserUseCase`
  deletes the user's Mongo-held conversations (via `list_by_user` +
  `delete`), nutrition profile, diet plans, and diet plan exports —
  all *before* the Postgres `user_repository.delete()` call, which
  cascades to `refresh_tokens`/`password_reset_tokens`/
  `email_verification_tokens`/`dietitian_applications`/
  `dietitian_profiles` (all already `ON DELETE CASCADE`; `email_logs`
  correctly has no FK and is deliberately left behind). Also added a
  guard the original plan didn't call out but the entity model made
  obviously necessary once actually building the endpoint: an admin
  cannot delete their own account (`CannotDeleteSelfError`, 400) —
  the same spirit as "no self-escalation path" for role changes.

  **The dietitian-approval flow closes the exact gap Etap 1 left
  open**: since Etap 1, there was no way for a `DietitianProfile` to
  ever be created through the API — `ApproveDietitianApplicationUseCase`
  is that path. It calls `application.approve(reviewed_by)` (raising
  `ApplicationAlreadyReviewedError` on a second attempt), promotes the
  user via `user.change_role(Role.DIET_USER)` directly (not through
  identity's `ChangeUserRoleUseCase` — that object exists for the
  `SUPER_ADMIN`-only role-change endpoint specifically; this is a
  deliberately different path, gated by its own endpoint's
  `require_role(ADMIN, SUPER_ADMIN)`), then creates the
  `DietitianProfile` from the application's own experience/diplomas/
  description. Defensively checks for an existing profile first (not
  expected in practice — one application per user, ever, approvable
  only once — but manual DB fixes during earlier live-verification
  passes are exactly the kind of state that could violate that
  assumption, so it's guarded rather than trusted).

  Exit criteria met — scoped to the new `admin` module plus the small
  repository additions in `identity`/`dietitian`/`nutrition` (genuinely
  cross-cutting, so the *full* suite ran, not just the new module): 43
  new tests total — 16 admin use-case unit tests (list/activate/ban/
  delete users; list/approve/reject dietitian applications, including
  the self-delete guard and the already-reviewed/already-exists edge
  cases) using in-memory fakes reused directly from each source
  module's own `tests/fakes.py`, plus 11 API-level tests across two new
  files (`test_users_api.py`, `test_dietitian_applications_api.py`) —
  27 tests in the new `backend/modules/admin/tests/` package
  (`pytest.ini` gained the new test path), and existing-fake updates
  (`InMemoryUserRepository` ×2, `InMemoryDietitianApplicationRepository`,
  three nutrition fakes) so the new abstract repository methods didn't
  break any ABC-inheriting fake. Full backend suite: 443 passed — the
  same 2 pre-existing timezone-boundary failures from Etap 1 Stage 5
  (unrelated, already flagged there) and nothing else.

  Live-verified against the real Docker backend via `curl` (no new
  migration needed — confirmed by `docker compose logs`, since this
  module adds no persistence of its own): bootstrapped an `ADMIN` via
  direct SQL (same pattern as Etap 0's first `SUPER_ADMIN`), confirmed
  `GET /admin/users` lists both accounts, submitted a dietitian
  application and approved it — confirmed via `GET /auth/me` that the
  applicant's role flipped to `DIET_USER` and via
  `GET /dietitian/profile/me` that a real profile now exists with the
  application's own data. Separately verified ban→activate,
  self-delete correctly rejected with 400, and — the part that mattered
  most — the cross-database cleanup: gave a second user a real Mongo
  nutrition profile, conversation, and diet plan, confirmed all three
  existed via `mongosh` (`UUID('...')` query syntax, not a plain string
  — `user_id` is stored as a native BSON UUID, an early verification
  attempt silently matched zero documents until this was corrected),
  called `DELETE /admin/users/{id}`, then confirmed all three Mongo
  documents and the Postgres `users` row were gone. `docker compose down`
  after.
- **Stage 2 — `frontend-admin/` scaffold — DONE**: new sibling folder
  to `frontend/` — its own Vite+React+TS+Tailwind v4 project (per the
  confirmed decision), same shadcn `base-nova` style and the identical
  design tokens/palette as the main app (brand consistency — this is
  the same product's admin tool, not a separate one), but no
  `react-router` (a single-page tab switcher needs no routes) and no
  registration/password-reset/email-verification flows (admin accounts
  are provisioned by role change, never self-registered). Own
  `docker-compose.yml` service (`frontend-admin`, port 5174, mirroring
  `frontend`'s exact pattern) and its own `Dockerfile`.

  **Login gate**: reuses the existing `POST /auth/login` +
  `GET /auth/me` endpoints — no separate admin auth system. `AuthContext.login()`
  fetches `/auth/me` right after storing tokens and immediately clears
  them and throws `InsufficientRoleError` if the role isn't
  `ADMIN`/`SUPER_ADMIN` — a `DIET_USER` or plain `USER` can authenticate
  against the backend but is never treated as "logged in" by this app's
  own state, not even for an instant. The same check runs during the
  silent bootstrap-refresh path on page load, not just on the login
  form's explicit submit.

  **Layout**: a plain top bar (title, logged-in email, a "← Powrót do
  aplikacji" link to `VITE_MAIN_APP_URL`, a logout button) — no rail
  choreography like the main app — plus a `Tabs` bar: Raporty /
  Użytkownicy / Dietetycy / Transakcje. All four are honest placeholders
  for now ("pojawi się w kolejnym etapie" / "po wdrożeniu modułu
  płatności"), each already its own file
  (`features/shell/tabs/*.tsx`) so Stage 3/4 replace one at a time
  without touching the others.

  **Two real bugs found and fixed while live-verifying, both would
  have silently broken the admin panel in the browser despite
  passing every automated test**:
  1. `docker-compose.yml`'s `backend` service hardcodes
     `CORS_ORIGINS: http://localhost:5173` as an environment variable,
     which overrides `Settings.cors_origins`'s default entirely —
     editing the Python default (also done, `"http://localhost:5173,http://localhost:5174"`,
     for anyone running the backend outside Docker) had no effect on
     the actual running container. Confirmed via a real CORS preflight
     (`OPTIONS` with `Origin: http://localhost:5174`) returning
     `400 Disallowed CORS origin` even after rebuilding — fixed by
     updating the compose file's env var too, re-verified as `200` with
     `access-control-allow-origin: http://localhost:5174`. Neither
     `pytest` nor a component test would ever catch this class of bug —
     it's purely a Docker Compose environment-variable precedence
     issue, only visible by actually issuing a cross-origin request
     against the containerized backend.
  2. (Caught before it shipped, while writing the tests, not after) —
     `App.test.tsx`'s first draft imported the module-level
     `queryClient` singleton from `@/lib/queryClient` for every test
     instead of a fresh `new QueryClient()` per render, which would
     have let cached `/auth/me` responses leak between unrelated test
     cases — fixed before running.

  Exit criteria met: `npx tsc --noEmit` and `npm run build` both clean;
  10 new tests (`AuthContext.test.tsx`: 6, covering ADMIN/SUPER_ADMIN
  acceptance, USER/DIET_USER rejection with token cleanup, and logout;
  `App.test.tsx`: 4, covering the login page, the full shell with all 4
  tabs after a real ADMIN login, the non-admin rejection message, and
  logout back to the login page) — both passing and exercising the
  exact role-gate logic that matters most in this stage. Backend's full
  suite re-run after the CORS settings change: 443 passed, same 2
  pre-existing timezone-boundary failures from Etap 1 Stage 5 and
  nothing else.

  Live-verified: `docker compose up -d --build backend frontend-admin`
  — confirmed via `docker compose logs` no new migration ran (this
  stage touches no backend persistence) and both services started
  clean; bootstrapped an `ADMIN` via direct SQL (same pattern as
  Etap 0's first `SUPER_ADMIN`); confirmed the login page renders with
  the shared design tokens in a real browser (one clean screenshot —
  the Claude-in-Chrome extension hit the same intermittent
  `chrome-extension://` connection error as Etap 1 Stage 4's browser
  check and didn't reliably recover across multiple fresh tabs this
  time either); fell back to `curl` for the functional checks: real
  `ADMIN` login → `/auth/me` returns `role: "ADMIN"`, a plain `USER`
  login → `/auth/me` returns `role: "USER"` (confirming the data the
  frontend's role-gate acts on), and the CORS preflight fix above.
  `docker compose down` after.
- **Stage 3 — Użytkownicy tab — DONE**: real list (`GET /admin/users`)
  in a plain table — email, a status `Badge`, role, created-at, and a
  per-row actions column (Aktywuj/Zablokuj toggling on `status`, Usuń
  opening a confirm `Dialog` before calling `DELETE`, per the
  "confirm before a destructive/irreversible action" convention). The
  role column is plain text for everyone except a `SUPER_ADMIN` caller,
  who gets an inline `Select` — and even then, not on their own row
  (see below). New `Select`/`Dialog`/`Badge` shadcn primitives copied
  into `frontend-admin` (same generated output as `frontend`'s own).

  **Two self-action guards added, one already planned and one found
  necessary while wiring the UI**: the existing `CannotDeleteSelfError`
  (Etap 2 Stage 1) now has a real UI trigger — the Usuń/Zablokuj
  buttons are disabled on the caller's own row. The *new* one: nothing
  had ever stopped a `SUPER_ADMIN` from changing their own role via
  `PATCH /admin/users/{user_id}/role` — harmless with several
  `SUPER_ADMIN`s around, but if there's only one, a single misclick
  demotes or locks out the only account that could undo it. Added the
  same shape of guard identity's admin router already had for deletion:
  `user_id == caller.id` → 400, checked in
  `backend/modules/identity/api/routers/admin_router.py` directly
  (`ChangeUserRoleUseCase` itself doesn't know about the caller, same
  as before — this stays an authorization concern at the API layer).
  On the frontend, the role `Select` simply isn't rendered at all for
  the `SUPER_ADMIN`'s own row, rather than rendering it disabled.

  Exit criteria met: backend — 1 new test
  (`test_super_admin_cannot_change_their_own_role`) in the existing
  `test_change_user_role_api.py` (6/6 passing), full identity suite
  re-run since the router changed (129 passed) and full backend suite
  since `docker-compose.yml`/CORS-adjacent files weren't touched this
  time but the shared router was (444 passed, same 2 pre-existing
  timezone-boundary failures, unrelated). Frontend — 6 new
  `UzytkownicyTab.test.tsx` tests (list rendering, role selector
  hidden for a plain `ADMIN`, shown for `SUPER_ADMIN` but not on their
  own row, ban, self-row actions disabled, delete-with-confirmation)
  plus `App.test.tsx`'s existing 4 tests updated to mock
  `GET /admin/users` (the placeholder text they'd asserted on no
  longer exists once this tab does something real) — 16/16 passing,
  `npx tsc --noEmit` and `npm run build` both clean.

  Live-verified: `docker compose up -d --build backend frontend-admin`,
  confirmed clean startup via logs (no new migration — this stage adds
  no schema). Browser click-through was blocked again by the same
  Claude-in-Chrome `chrome-extension://` connection error (failed on
  the very next action after a clean screenshot, across a fresh tab,
  same pattern as Stage 2) — substituted a thorough `curl` pass instead:
  bootstrapped a `SUPER_ADMIN` and 3 target users, listed them via
  `GET /admin/users`, ran ban→activate→role-change on one target (each
  200, each change reflected in the response body), confirmed both
  self-guards return 400 for the `SUPER_ADMIN`'s own id (role-change
  and delete), then deleted the target user (204). Also re-confirmed
  the CORS preflight for `/admin/users` from `http://localhost:5174`
  returns `200` with the right `access-control-allow-origin`.
  `docker compose down` after.
- **Stage 4 — Dietetycy tab — DONE**: real list
  (`GET /admin/dietitian-applications`) with a status filter `Select`
  (Oczekujące / Zaakceptowane / Odrzucone / Wszystkie, defaulting to
  Oczekujące — what an admin needs day-to-day), each application shown
  as a card (experience/diplomas/description + a status `Badge`), with
  Zaakceptuj/Odrzuć actions only on `PENDING` ones.

  **The endpoint only returns `user_id`, not an email** — solved
  client-side rather than adding a backend field: reuses the
  `['admin-users']` query (same key `UzytkownicyTab` already fetches,
  so TanStack Query dedupes/shares the one request) to build a
  `user_id → email` lookup map, falling back to the raw UUID if a
  match isn't found (covered by a test, though it shouldn't happen in
  practice — every application has a real owning user).

  **A real, fully broken layout bug found and fixed in the browser,
  invisible to every automated test**: `AdminShell`'s tab bar rendered
  as a vertical column of four stacked links in the page's far-left
  margin instead of a horizontal bar under the header — completely
  unusable, but every unit test still passed, because jsdom doesn't
  compute Flexbox layout at all, so `getByRole('tab', ...)` finds the
  elements regardless of how (or whether) they're visually arranged.
  Root cause: the shared `tabs.tsx` primitive's root class is
  `"group/tabs flex gap-2 data-horizontal:flex-col"` — `data-horizontal:`
  is a Tailwind arbitrary-attribute selector keyed on a boolean
  `data-horizontal` attribute that this version of Base UI never
  actually sets (it only sets `data-orientation="horizontal"`), so the
  class silently never applies and `Tabs` falls back to a plain `flex`
  (row) instead of the intended column (list-above-panel) layout. The
  main app's own `ProfileModal` never hit this because it happens to
  pass `className="flex h-full flex-col gap-0"` explicitly on its own
  `<Tabs>` — a workaround, not a fix, that this stage's `AdminShell`
  simply hadn't copied. Fixed the same way: `<Tabs defaultValue="uzytkownicy"
  className="flex flex-col gap-0">`, with a comment explaining why,
  so the next `<Tabs>` usage in this codebase doesn't rediscover the
  same bug. The underlying `tabs.tsx` primitive itself was left
  unpatched — fixing the arbitrary-selector bug at its source is a
  larger, riskier change (affects every `Tabs` usage in both apps) than
  this stage's scope justified; noted here for whoever next touches
  that primitive.

  Exit criteria met: 6 new `DietetycyTab.test.tsx` tests (email
  resolution + details, empty state, no-actions-for-non-pending,
  approve, reject, UUID fallback when the user list has no match) — all
  passing, 22/22 for the whole `frontend-admin` suite, `npx tsc --noEmit`
  and `npm run build` both clean.

  Live-verified in a real browser this time (the Claude-in-Chrome
  extension held up for the whole session, unlike the last two
  stages): `docker compose up -d --build backend frontend-admin` —
  ran into a genuine "No space left on device" failure starting
  Postgres, caused by ~29GB of accumulated Docker images/build cache
  from this session's many rebuilds eating nearly all free disk space;
  resolved with `docker image prune -f` + `docker builder prune -f`
  (dangling images and build cache only, no volumes touched) before
  retrying successfully. Bootstrapped a `SUPER_ADMIN` and two dietitian
  applications via `curl`/direct SQL, then logged into
  `frontend-admin` for real: confirmed the (post-fix) horizontal tab
  bar, clicked into Dietetycy, approved one application, watched it
  disappear from the "Oczekujące" filter and the success toast fire,
  switched the filter to "Zaakceptowane" and confirmed it now appeared
  there with no action buttons, and confirmed directly via `psql` that
  the approved applicant's Postgres row now has `role = 'DIET_USER'`.
  `docker compose down` after.
- **Stage 5 — Raporty tab placeholder — DONE**: elevated Raporty (and,
  since it's in the same boat — a placeholder with no real fix date —
  Transakcje too) from Stage 2's bare paragraph to a proper `EmptyState`
  component: icon + centered message, matching the main app's own
  `EmptyState` shape exactly (new `frontend-admin/src/components/EmptyState.tsx`,
  same props/layout, since the two apps don't share a component
  library). No report-generation logic — explicitly out of scope per
  the user's own framing ("do implementacji później"). New
  `RaportyTab.test.tsx` (the tab's first dedicated test — it had none
  before, having only ever been asserted on indirectly through
  `App.test.tsx`).

  Exit criteria met: 23/23 `frontend-admin` tests passing (1 new),
  `npx tsc --noEmit` and `npm run build` both clean. Live-verified in a
  real browser (Claude-in-Chrome held up again): bootstrapped a fresh
  `SUPER_ADMIN`, logged in, clicked Raporty, confirmed the bar-chart
  icon + message render centered and the Stage 4 tab-bar layout fix
  still holds. `docker compose down` after — no backend touched this
  stage, so no backend test run was needed.
- **Stage 6 — Tests + docs sync — DONE**: closing stage for Etap 2 as a
  whole, so — per the standing testing-scope rule — the full suite ran
  across all three codebases (backend, `frontend`, `frontend-admin`),
  not just what this etap touched.

  **Docs sync** (all three doc gaps below were genuinely missing, not
  just stale — the new `admin` module and RBAC had never been written
  up in `docs/architecture.md` at all, across three prior etaps):
  - `docs/api.md`: new **Admin API** module section — all 7 endpoints
    (`GET /admin/users`, activate/ban/delete, `GET /admin/dietitian-applications`
    with its `?status=` filter, approve/reject), plus an Overview bullet.
  - `docs/architecture.md`: added the **Role-based access control**
    subsection to the Identity Module (a gap from Etap 0 — RBAC had
    never been documented here even though `docs/domain-model.md` and
    `docs/api.md` both got it at the time), a new **Admin Module**
    section explaining its no-own-persistence design and explicitly
    why that isn't an exception to the Data Ownership Rules (goes
    through the same repository ports each owning module's own use
    cases already use), updated the Docker services list
    (`frontend-admin`, plus a note on the `CORS_ORIGINS` env-var
    override gotcha from Etap 2 Stage 2), and a short addendum on the
    High Level Architecture diagram.
  - `docs/domain-model.md`: new **Admin Context** bounded-context entry
    — explicitly "no domain entities of its own," so its absence from
    Aggregates/Persistence Mapping reads as intentional, not forgotten.
  - `README.md`: added a Phase 12 row to the status table (Stage 2 had
    already covered the Docker services table and file tree).
  - `docs/openapi.json` regenerated — confirmed all 7 new paths present.

  **A second pre-existing bug fixed, not just flagged this time**: the
  same timezone-boundary flake called out (but left alone) in both
  Etap 1 Stage 5 and Etap 2 Stage 1's retrospectives —
  `test_diet_plan_api.py` comparing `date.today()` (local timezone) against
  `DietPlan.created_at` (stored UTC), flaky for ~2 hours a day in any
  UTC+ timezone. Fixed for real this time (closing-stage full-suite
  runs are exactly when a flake like this keeps resurfacing): a new
  `_today()` test helper using `datetime.now(UTC).date()`, all 6
  call sites in the file switched to it. This is a test-only change —
  no production code was touched, and full backend suite is now **446
  passed, 0 failed**, clean for the first time all session instead of
  "444 passed, 2 pre-existing failures."

  Exit criteria met: full suite across all three codebases —
  **backend: 446/446**, **frontend: 105/105**, **frontend-admin: 23/23**
  — all clean, zero known failures anywhere. Both frontend builds
  (`npm run build`) clean.

Etap 2 (Admin backend module + `frontend-admin` app) is now **DONE** —
all 6 stages complete: the module itself (Stage 1), the app scaffold
with its role-gated login (Stage 2), the Użytkownicy tab (Stage 3), the
Dietetycy tab (Stage 4), the Raporty placeholder (Stage 5), and this
docs/tests close-out (Stage 6).

---

### Etap 3 — Transactions module

Goal: real Postgres-backed transaction records, admin-toggleable paid
status, no real payment gateway (per the user's explicit demo-scope
call, same spirit as this project's existing Mock AI provider / Mailhog
/ local SFTP stand-ins for real external services).

Design decisions settled before Stage 1 (revised 2026-07-20, once actually
about to build this etap, from the looser sketch above):

- **Status is a 2-state toggle, not a one-way state machine**:
  `TransactionStatus`: `UNPAID` (initial) / `PAID`. The admin action is
  literally "mark paid" / "mark unpaid" — a reversible toggle, unlike
  `DietitianApplication`'s one-way `PENDING → APPROVED|REJECTED`. No
  `PENDING`/`CANCELLED` states — nothing in the spec calls for them, and
  adding a richer state machine than the two real actions need would be
  speculative. `mark_paid()` sets `status=PAID` + `paid_at=now()`;
  `mark_unpaid()` sets `status=UNPAID` + `paid_at=None` — both idempotent,
  neither raises on a redundant call (unlike approve/reject, this isn't
  guarding an invariant, just flipping a flag).
- **`amount` is server-computed, not client-supplied**: a small fixed
  price table keyed by `offer_type` (`PLAN_REVIEW` / `INDIVIDUAL_PLAN`)
  lives in the domain layer — the create-transaction request only ever
  sends `dietitian_id` + `offer_type`; letting a client set its own price
  would be a real integrity hole for a module whose entire job is
  tracking money. Stored as `Numeric(10, 2)` / `Decimal`, not `float`.
- **FK behavior**: `user_id` (buyer) is `ON DELETE CASCADE` (same as
  `dietitian_applications`/`dietitian_profiles` — owned data disappears
  with its owner, and this needs zero changes to Etap 2's
  `DeleteUserUseCase`). `dietitian_id` is `ON DELETE SET NULL` (mirrors
  `dietitian_applications.reviewed_by` — deleting the dietitian shouldn't
  erase the *buyer's* transaction history).
- **Kafka doesn't exist yet — a port stands in for it, not a stub
  string of TODOs**: Stage 3 needs to react to a transaction turning
  `PAID`, but Etap 5 is what actually adds Kafka. Same shape as
  `EmailSender`/`SftpClient`/`FileStorage` elsewhere in this codebase: a
  `TransactionEventPublisher` port, `NoOpTransactionEventPublisher` as
  the only implementation for now. Etap 5 Stage 1 adds a
  `KafkaTransactionEventPublisher` and wires it in — the mark-paid use
  case itself doesn't change.

- **Stage 1 — New `backend/modules/transactions/` module, Postgres
  schema — DONE**: `Transaction` entity + `transactions` table — `id`,
  `user_id` (buyer), `dietitian_id`, `offer_type`, `amount`, `status`,
  `created_at`, `paid_at`. Postgres, not Mongo — this is the one new
  module that's genuinely transactional/relational, matching Identity's
  existing choice of Postgres for the same reason. Domain + repository
  port + SQLAlchemy model/mapper/migration only — no API surface yet
  (mirrors Etap 1 Stage 1's own scoping: schema first, endpoints next).
  Built exactly per the design decisions settled above: `amount` is
  `Numeric(10, 2)`/`Decimal`, resolved server-side from the
  `OFFER_PRICES` table keyed by `OfferType`, never accepted from a
  caller; `TransactionStatus` is the 2-state `UNPAID`/`PAID` toggle,
  `mark_paid()`/`mark_unpaid()` both idempotent; `Transaction.create()`
  itself rejects `user_id == dietitian_id` (a pure data invariant, no
  repository lookup needed, so it lives in the entity — checking that
  the dietitian side is an actual `DIET_USER` does need a lookup and is
  deferred to Stage 2's use case). `dietitian_id` is modeled as
  `UUID | None` in the domain entity, not just nullable at the DB
  level — it can legitimately become `None` for an existing row once
  the dietitian account is deleted (`ON DELETE SET NULL`), so the
  domain type has to allow that even though `create()` never produces
  it. New migration `20260720_09_transactions.py`, chained after
  Etap 1's `20260719_08_dietitian_photos`.

  Exit criteria met (scoped — new, fully isolated module): 6 new entity
  unit tests (`create()` defaults, price lookup, self-purchase
  rejection, `mark_paid`/`mark_unpaid`, idempotent re-marking).
  `pytest.ini` and `alembic/env.py` both gained the new module.

  Live-verified against the real Docker backend: confirmed the
  migration applied via `docker compose logs`, confirmed the exact
  schema/FKs/indexes via `psql \d transactions`, then proved both FK
  behaviors concretely rather than just trusting the DDL — inserted a
  real transaction row, deleted the *dietitian's* user row directly and
  confirmed the transaction survived with `dietitian_id` now `NULL`,
  then deleted the *buyer's* user row and confirmed the transaction row
  was gone (cascade). `docker compose down` after.
- **Stage 2 — Create-transaction use case + endpoint — DONE**:
  `POST /transactions` (`{dietitian_id, offer_type}`, buyer = caller,
  any authenticated user — not role-gated, since anyone might want to
  hire a dietitian) — creates an `UNPAID` transaction with the
  server-computed amount. `CreateTransactionUseCase` checks order
  matters: it loads `dietitian_id` via `UserRepository` and confirms
  `role == DIET_USER` *first* (404 `DietitianNotFoundError` if missing
  or not a dietitian) — only then calls `Transaction.create()`, whose
  own self-purchase guard (Stage 1) fires second. Consequence, caught
  live rather than assumed: a non-dietitian trying to "buy from
  themselves" gets **404, not 400** — the dietitian-existence check
  fails before the self-purchase check is ever reached, since they
  aren't a real dietitian target either way. Confirmed correct by
  testing both shapes separately: a plain user targeting their own id →
  404; an actual `DIET_USER` targeting their own id → 400 from the
  entity's guard.

  Fired from Etap 4's offer-selection UI once that exists; until then,
  exercised directly — same "verify via curl ahead of the real UI
  trigger" pattern Etap 2's dietitian-approval flow used before Etap 4's
  marketplace existed. Cross-module reuse follows the established
  shape: `CreateTransactionUseCase` takes `identity`'s `UserRepository`
  as a constructor dependency (via a locally-defined
  `get_user_repository_for_transactions` provider — not a shared
  export, mirroring how `admin`'s own equivalent provider is also
  module-local, not something other modules import).

  Exit criteria met (scoped — new, still-isolated module; no shared
  repository interfaces changed this time, so no full-suite run):
  4 new use-case unit tests (success; unknown dietitian id; target
  exists but isn't a `DIET_USER`; self-purchase) using
  `InMemoryTransactionRepository` (new `tests/fakes.py`) +
  `identity`'s own `InMemoryUserRepository`, plus 6 new
  `test_create_transaction_api.py` tests (201, 401, both 404 shapes,
  400 self-purchase, 422 invalid `offer_type`) — 16 tests total in the
  module (up from 6 after Stage 1).

  Live-verified against the real Docker backend via `curl`: created a
  real `PLAN_REVIEW` (49.00) and `INDIVIDUAL_PLAN` (149.00) transaction
  between a real buyer and a real `DIET_USER`, confirmed both amounts
  came back server-computed and exactly right; confirmed unauthenticated
  → 401; confirmed a genuine `DIET_USER` targeting their own id → 400
  (the scenario above, tested for real, not just in the suite);
  cross-checked both persisted rows directly via
  `psql SELECT offer_type, amount, status FROM transactions`.
  `docker compose down` after.
- **Stage 3 — Admin mark paid/unpaid — DONE**: `POST /admin/transactions/{id}/mark-paid`
  / `.../mark-unpaid`, both admin-only, both living in the existing
  `admin` module (`MarkTransactionPaidUseCase`/`MarkTransactionUnpaidUseCase`)
  — same reuse-the-owning-module's-repository-port pattern as every
  other admin action, this time reusing `transactions`' own exported
  `get_transaction_repository` dependency exactly the way `admin`
  already reuses `dietitian`'s. New `TransactionEventPublisher` port
  (`application/ports/`) + `NoOpTransactionEventPublisher`
  (`infrastructure/events/`) — same "swappable port, mock/no-op default"
  shape as `EmailSender`/`SftpClient`/`FileStorage`, right down to
  keeping a `published: list[Transaction]` for tests to assert against,
  mirroring `MockEmailSender.sent`. `mark_paid()` calls
  `publish_transaction_paid()` after saving; `mark_unpaid()` doesn't
  publish anything — only a transaction *becoming* paid is a
  meaningful event (Etap 5's dietitian-contact-reveal trigger), not the
  reverse. A new `TransactionNotFoundError` was added to `transactions`'
  own `application/use_cases/exceptions.py` (not `admin`'s) — same
  precedent as `DietitianApplicationNotFoundError` living in `dietitian`
  even though `admin`'s approve/reject use cases are the ones raising it.

  Exit criteria met (scoped — only `admin` and `transactions`, the two
  already-isolated modules touched; no full suite): 4 new use-case unit
  tests (mark-paid updates status + publishes exactly one event;
  mark-paid on an unknown id raises without publishing; mark-unpaid
  clears `paid_at`; mark-unpaid on an unknown id raises) using
  `InMemoryTransactionRepository` reused directly from `transactions/tests/fakes.py`
  (cross-module fake reuse, same precedent as `admin`'s
  `delete_user_use_case` test importing nutrition/conversation fakes),
  plus 4 new API tests (403 for a non-admin, the full paid→unpaid
  round-trip via a transaction created through the real Stage 2
  endpoint, and both 404 shapes) — 51 tests total across the two
  modules (16 + 35, up from 16 + 27).

  Live-verified against the real Docker backend via `curl`: registered
  an admin/buyer/dietitian trio, created a real transaction, marked it
  paid (`paid_at` populated in the response), marked it unpaid again
  (`paid_at` cleared), confirmed a non-admin caller gets 403, and
  cross-checked the final `UNPAID`/`NULL` state directly via
  `psql SELECT status, paid_at FROM transactions`. `docker compose down`
  after.
- **Stage 4 — Transakcje tabs wired — DONE**: two new `GET` endpoints,
  each living in the module that actually owns the data (not `admin`
  for the dietitian-facing one): `GET /transactions/me`
  (`transactions` module, `DIET_USER`-gated, `list_by_dietitian_id(caller)`)
  and `GET /admin/transactions` (`admin` module, `ADMIN`/`SUPER_ADMIN`-gated,
  `list_all()`) — same "self-service view lives in the owning module,
  cross-cutting oversight view lives in `admin`" split already used for
  `GET /dietitian/applications/me` vs `GET /admin/dietitian-applications`.

  **A deliberate scope decision, not an oversight**: the dietitian's own
  Transakcje tab shows offer type, amount, status, and date — **not**
  the buyer's identity. Etap 5 Stage 1's own design explicitly frames
  "making the paying user's contact visible to the dietitian" as *the*
  event `TransactionPaid` triggers — meaning buyer contact is meant to
  stay hidden from the dietitian until that reveal exists. Building the
  contact-hiding logic now (before Etap 5 exists) would mean redoing it
  once the real reveal flow lands, so this stage just never surfaces
  `user_id` in the dietitian-facing UI at all (the API response still
  includes it — enforcing that server-side wasn't judged necessary yet,
  since no endpoint available to a `DIET_USER` can resolve a bare UUID
  into anything identifying anyway). The **admin** panel's Transakcje
  tab, by contrast, legitimately needs to see everyone involved — it
  resolves both `user_id` and `dietitian_id` against the already-cached
  `['admin-users']` query, the identical client-side email-resolution
  trick `DietetycyTab` already used in Etap 2 Stage 4.

  Frontend: `frontend/src/api/transactions.ts` (new, main app) +
  `TransakcjeTab.tsx` rewritten from Etap 1 Stage 4's placeholder to a
  real list; `frontend-admin/src/api/admin.ts` gained
  `getTransactions`/`markTransactionPaid`/`markTransactionUnpaid`, and
  its own `TransakcjeTab.tsx` rewritten from Etap 2 Stage 5's
  `EmptyState` placeholder to a real table with inline mark-paid/unpaid
  toggle buttons per row.

  Exit criteria met: backend — 2 new use-case tests
  (`GetMyTransactionsAsDietitianUseCase`: filters correctly, empty when
  none) + 3 new API tests (403/401/own-only) in `transactions`
  (21 tests, up from 16), and 2 new `ListTransactionsUseCase` tests +
  2 new API tests in `admin` (39 tests, up from 35) — no full suite
  (still fully within the two already-isolated modules). Frontend:
  main app gained 4 new `TransakcjeTab.test.tsx` tests (empty state,
  offer/amount/status rendering — including a word-boundary regex fix
  once `/49.00/` ambiguously matched `149.00` too — and an explicit
  assertion that the buyer's UUID never appears in the DOM) plus 2
  existing `ProfileModal.test.tsx` assertions updated for the new
  content — 107/107 passing. `frontend-admin` gained 5 new
  `TransakcjeTab.test.tsx` tests (empty state, resolved emails,
  mark-paid, mark-unpaid, UUID fallback) — 28/28 passing. Both
  `npx tsc --noEmit` and both `npm run build` clean.

  Live-verified against the real Docker backend: created a real
  transaction between a buyer and a `DIET_USER`, confirmed
  `GET /transactions/me` (as the dietitian) returns exactly that one
  transaction, confirmed `GET /admin/transactions` (as `SUPER_ADMIN`)
  lists it among all transactions, and confirmed both frontend dev
  servers respond `200`. **Browser click-through could not be
  completed this stage** — the Claude-in-Chrome extension reported
  fully disconnected (not just the intermittent flake from the last
  three stages), so the UI-level verification rests on the `curl`
  checks above plus the two frontends' full test suites, which
  directly exercise the email-resolution and mark-paid/unpaid logic
  under test. `docker compose down` after.
- **Stage 5 — Tests + docs sync — DONE**: closing stage for Etap 3 —
  documentation sync across all four docs plus the closing full-suite
  gate, no new application code.

  **`docs/api.md`**: added the two new admin transaction-oversight
  endpoints (`GET /admin/transactions`,
  `POST /admin/transactions/{id}/mark-paid`,
  `POST /admin/transactions/{id}/mark-unpaid`) to the existing Admin API
  section, and a brand-new `# Transactions API` module section
  (`POST /transactions`, `GET /transactions/me`) between Admin API and
  Conversation Categories.

  **`docs/domain-model.md`**: new `## Transactions Context` bounded
  context and a new `# 8. Transactions Domain` section (the entity, the
  2-state toggle rule, the self-purchase guard, "no domain events
  emitted" — matching the port/no-op pattern rather than raising real
  events yet). Every subsequent top-level section renumbered (AI Domain
  8→9 through Future Extensions 14→15 — verified sequential via
  `grep -n "^# [0-9]"` afterward). Aggregates list, Persistence Mapping
  (new `transactions` table entry), and Relationships (new note: User is
  the only entity playing two different roles — buyer and dietitian — in
  the same relationship, each with a different delete behavior) all
  updated to match.

  **`docs/architecture.md`**: Admin Module section updated for the new
  `/admin/transactions` route group and its reuse of `transactions`'s own
  `TransactionRepository`; new `## Transactions Module (Phase 12)`
  section (responsibilities, the no-payment-gateway demo-scope decision,
  the `TransactionEventPublisher` port with its code snippet, the FK
  asymmetry explanation noting both directions were verified by real
  deletion, not just read off the DDL); Data Ownership Rules gained a
  short addendum that `transactions`' own `CreateTransactionUseCase` also
  reuses `identity`'s `UserRepository` directly, the same
  not-actually-an-exception pattern `admin` already established.

  **`README.md`**: checked, needed no change — it tracks Phase 12 only at
  the whole-phase level ("🚧 in progress"), not per-etap.

  **`docs/openapi.json`**: regenerated via
  `PYTHONPATH=. python scripts/export_openapi.py`; confirmed all three
  new transaction paths present (`/api/v1/transactions`,
  `/api/v1/transactions/me`, `/api/v1/admin/transactions`).

  Exit criteria met — closing-gate full suites, not just the touched
  modules: backend **479 passed, 0 failed** (the timezone flake flagged
  in Etap 1 Stage 5 and re-flagged in Etap 2 Stage 5's retrospectives was
  actually fixed for good back in Etap 2 Stage 6 — this is the first
  closing stage all Phase 12 with a fully clean backend run). Main
  frontend: **107 passed** (18 files). `frontend-admin`: **28 passed** (6
  files). Both `npm run build`s clean (only the pre-existing, harmless
  "chunks larger than 500 kB" warning on the main app).

  No new bugs found this stage — this was a pure docs-and-verification
  close-out.
- **Etap 3 (Transactions module): DONE** — all 5 stages complete (domain
  entity + schema + migration, create-transaction endpoint, admin
  mark-paid/unpaid, both apps' Transakcje tabs wired to real data, this
  docs/tests sync).

---

### Etap 4 — Marketplace & reviews

Goal: users can actually discover and hire a dietitian.

Design decisions settled before Stage 1 (revised 2026-07-20, once actually
about to build this etap, same spirit as Etap 3's own pre-Stage-1 revision):

- **`Review` lives in the `dietitian` module, not a new module** — it's
  data about a dietitian's public standing, same bounded context as
  `DietitianProfile`. `id, reviewer_id, dietitian_id (both plain `UUID`s
  pointing at `users.id`, same cross-referencing style as
  `DietitianApplication.reviewed_by`/`Transaction.dietitian_id`), rating:
  int (1-10 per the sketch above), comment: str, created_at, updated_at`.
  One review per `(reviewer_id, dietitian_id)` pair, **editable by its
  author** — `SubmitReviewUseCase` upserts: loads any existing review for
  that pair first, calls `review.update_content()` if found, else
  `Review.create()`. A DB-level unique index on
  `(reviewer_id, dietitian_id)` backs the same invariant the app layer
  enforces, exactly the way `ix_dietitian_applications_user_id` already
  backs "one application per user" — not a new pattern.
- **Self-review guard lives in `Review.create()`**, same reasoning as
  `Transaction.create()`'s self-purchase guard: `reviewer_id ==
  dietitian_id` is a pure data invariant needing no repository lookup, so
  it belongs in the entity, not the use case.
- **No "must have a paid transaction to review" gate.** Nothing in this
  etap's own goal or the earlier sketch calls for tying reviews to
  completed engagements, and building that gate now would be inventing a
  requirement rather than implementing one — any authenticated user may
  review any real dietitian. Flagged here explicitly as a deliberate
  scope decision, not an oversight.
- **Public listing/profile reads are unauthenticated** — genuinely public
  browsing (no login) for `GET /dietitian` (marketplace listing) and
  `GET /dietitian/{dietitian_id}` (single public profile), matching how
  any real marketplace lets you window-shop before signing up. Submitting
  a review (`POST /dietitian/{dietitian_id}/reviews`) still requires
  `get_current_user` — same "any authenticated user" dependency
  `POST /transactions` already uses.
- **Average rating is computed on read, not stored redundantly** on
  `DietitianProfile` — a small `rating_summary_by_dietitian_id()`
  repository method (SQL `AVG`/`COUNT`) called once per listed/viewed
  dietitian. Demo-scope dietitian counts make the resulting N+1 pattern
  (one query per card) an acceptable simplicity trade-off, same call
  already made for admin's client-side email resolution.
- **Public reviews omit the reviewer's identity** — the profile endpoint
  returns `rating`, `comment`, `created_at` per review, never
  `reviewer_id`/email. This mirrors Etap 3's own buyer-contact-hiding
  decision in spirit (don't surface a user's identity to an audience the
  spec never asked them to be exposed to) — here protecting *any*
  visitor (not just the dietitian) from seeing who wrote a review, since
  this endpoint needs no auth at all to view.
- **Marketplace listing/profile filter to real, active dietitians only**:
  a profile whose owning user is no longer `DIET_USER` (a `SUPER_ADMIN`
  reversed the role) or is not `ACTIVE` (banned/deactivated) is excluded
  — same `role`/`status` check `CreateTransactionUseCase` already applies
  when validating a purchase target, reused here for the same reason (a
  banned dietitian shouldn't be discoverable or hireable).
- `DietitianProfileRepository` gains `list_all()` (mirrors
  `UserRepository`/`TransactionRepository`'s own `list_all()`) — the
  marketplace listing use case's data source, filtered down as above.

- **Stage 1 — Review domain — DONE**: `Review` entity (`reviewer_id`,
  `dietitian_id`, `rating` 1-10, `comment`, `created_at`, `updated_at`) +
  `reviews` table in the `dietitian` module, built exactly per the design
  decisions settled above — self-review guard in `Review.create()`,
  DB-level unique index on `(reviewer_id, dietitian_id)` backing the
  app-level upsert, both FKs `ON DELETE CASCADE` (reviews about a deleted
  dietitian, or by a deleted reviewer, have no reason to survive — unlike
  `transactions`' asymmetric FKs). `SubmitReviewUseCase` loads any
  existing review for the pair first and calls `update_content()` if
  found, else `Review.create()` — one `POST /dietitian/{id}/reviews` call
  handles both create and edit. Validates the target is a real, active
  `DIET_USER` via `UserRepository` (reused directly, same
  not-actually-an-exception pattern `transactions`' own
  `CreateTransactionUseCase` already established) before touching the
  review itself.

  Also shipped in this stage, since the plan calls for the average
  rating to be "exposed on the dietitian's public profile/listing" and
  that listing/profile don't exist as a *frontend* yet, the **backend**
  side of both: `GET /dietitian` (marketplace listing) and
  `GET /dietitian/{dietitian_id}` (single public profile) — both
  genuinely unauthenticated, matching real-marketplace browse-before-login
  UX. `ListDietitiansUseCase`/`GetPublicDietitianProfileUseCase` join
  `DietitianProfileRepository.list_all()` (new method, added this stage)
  against `UserRepository` (for email + role/status filtering) and
  `ReviewRepository.rating_summary_by_dietitian_id()` (a small SQL
  `AVG`/`COUNT` query) per dietitian — an accepted N+1 pattern at this
  data scale, same trade-off already made for admin's client-side email
  resolution. Public reviews surface `rating`/`comment`/`created_at`
  only, never the reviewer's identity — a deliberate, explicitly-recorded
  scope decision, not an oversight. This stage is otherwise backend-only
  — Stages 2/3 wire the frontend to what it exposes, same "schema/logic
  first, UI next" split as every prior etap.

  Exit criteria met: 29 new tests (7 `Review` entity — self-review guard,
  rating boundaries, empty-comment rejection, `update_content()`; 6
  `SubmitReviewUseCase` — create, upsert-on-repeat, unknown/non-dietitian
  target, self-review, invalid rating; 4 `ListDietitiansUseCase` — active
  dietitian with rating summary, excludes banned, excludes role-reversed,
  empty; 3 `GetPublicDietitianProfileUseCase` — reviews without reviewer
  identity, not-found, banned-excluded; 6 review API tests — 201, 401,
  404 unknown dietitian, 400 self-review, 422 out-of-range rating,
  upsert-via-API; 3 marketplace API tests — public listing, public
  profile with a real review, 404 without a profile), dietitian module
  now at 82 tests (up from 53). Because this stage added a new abstract
  method to the shared `DietitianProfileRepository` port (`list_all()`,
  also consumed by `admin`'s existing fakes), the **full** backend suite
  was run rather than just the touched module's: 508 passed, 0 failed
  (up from 479 at Etap 3's close — the 29 new tests here plus nothing
  else changed).

  Live-verified against the real Docker backend: confirmed the
  `20260720_10_reviews` migration applies cleanly on top of
  `20260720_09_transactions`; registered a buyer and a dietitian,
  promoted the dietitian and seeded a profile via direct SQL (same
  pattern as every prior stage's bootstrap), confirmed `GET /dietitian`
  lists it — and, since this environment's Postgres volume carries
  dietitian profiles seeded by earlier live-verification sessions all the
  way back to Phase 12's start, the listing response came back with all
  of them still present and correctly email-resolved, a good incidental
  check that `list_all()` doesn't silently drop older rows. Confirmed
  `GET /dietitian/{id}` 404s before any profile exists check applies,
  submitted a real review as the buyer (`average_rating`/`review_count`
  updated correctly on the next profile fetch), and confirmed the
  dietitian attempting to review themselves gets a real `400`.
  `docker compose down` after.
- **Stage 2 — Right rail becomes the marketplace listing — DONE**:
  replaces today's static "Co nowego" placeholder (which Etap 5 of
  Phase 10 explicitly described as "reserved for future roadmap items" —
  this is that future). Shows dietitian cards (photo thumbnail, name,
  experience, average rating) — dietitians the user has an active/paid
  engagement with pinned at the top ("Twoi dietetycy"), the rest of the
  roster below ("Wszyscy dietetycy" — heading only shown once there's a
  pinned group to distinguish it from).

  **Design decisions settled right before building this stage** (a small
  backend gap found while scoping the frontend work, same spirit as every
  prior "revised once actually about to build this" note):
  - **"Pinned at the top" needs the buyer's own purchase history, which
    no endpoint exposes yet** — `GET /transactions/me` is dietitian-only
    (`require_role(DIET_USER)`, returns transactions where the caller is
    the *seller*). A plain buyer has no way to ask "which dietitians have
    I already engaged?". Adds one small, symmetric endpoint to the
    `transactions` module: `GET /transactions/me/purchases` (any
    authenticated user, `get_current_user` — mirrors `POST /transactions`
    itself), backed by a new `GetMyPurchasesUseCase` that's a one-line
    twin of `GetMyTransactionsAsDietitianUseCase` (`list_by_user_id`
    instead of `list_by_dietitian_id` — the repository already exposed
    both, only the dietitian side had a route). "Active/paid" is read
    loosely as "any transaction exists with this dietitian, regardless of
    `UNPAID`/`PAID`" — pinning a card the moment you've expressed
    interest (created an `UNPAID` transaction) rather than only after an
    admin flips it, which better matches "dietitians I'm already talking
    to" than a strict paid-only reading would.
  - **Cards are not clickable yet** — Stage 3 is explicitly "click a card
    → full profile"; wiring navigation before that view exists would be a
    dead link. This stage only renders the listing.
  - **"Experience abbreviated e.g. '5 lat'" is a CSS truncation, not a
    text-parsing extraction** — `experience` is free-text (some existing
    seeded profiles read like a full sentence, not a bare "5 lat"), so
    there's no reliable way to mechanically extract a short form from
    arbitrary prose. Cards `truncate`/`line-clamp` the real field instead
    of inventing a parser for something the backend never structured as a
    number.

  Built: `RightRail.tsx` rewritten from Etap 0's static placeholder to a
  real listing — `useQuery(['dietitian-listing'], listDietitians)` (no
  `isAuthenticated` gate — genuinely public, matching the backend) plus
  `useQuery(['my-purchases'], getMyPurchases, { enabled: isAuthenticated
  })` to compute the pinned set. Each `DietitianCard` shows an `Avatar`
  (real photo via `resolveStaticUrl` when present, initials fallback
  otherwise — same pattern `LeftRail`'s profile avatar already uses), the
  email as the display name (still the only identifier `User` has, same
  call made throughout `admin`/`frontend-admin`), the truncated
  experience text, and either a star rating badge or "Brak ocen" when
  `average_rating` is `null`. Loading (skeleton cards), error, and empty
  states mirror `LeftRail`'s own conversation-history states for visual
  consistency. `frontend/src/api/dietitian.ts` gained `listDietitians()`
  (called with `skipAuth: true` — this endpoint never needs a token and
  should never trigger a refresh attempt); `frontend/src/api/
  transactions.ts` gained `getMyPurchases()`.

  Also shipped, since it was this stage's own prerequisite: the backend
  `GET /transactions/me/purchases` endpoint + `GetMyPurchasesUseCase`
  (`transactions` module).

  Exit criteria met: backend — 5 new tests (2 `GetMyPurchasesUseCase`
  unit tests, 3 API tests: 401 without auth, 200 with an empty list for
  a buyer with no purchases, returns only the calling buyer's own
  transactions) — `transactions` module now at 26 tests (up from 21);
  frontend — 4 new `RightRail.test.tsx` tests (empty state
  without requiring login, card rendering with rating/"Brak ocen",
  error state, pinning a dietitian the logged-in user has a transaction
  with) plus 6 existing `AppShell.test.tsx` fetch-mock bodies updated to
  return `[]` for the two new endpoints instead of falling through to
  `{}` (which would have thrown inside `RightRail`'s `.filter()` calls)
  and its 4 "Co nowego" assertions renamed to "Dietetycy" — main frontend
  now at 111 tests, all passing. Both `npx tsc --noEmit` and
  `npm run build` clean.

  Live-verified against the real Docker backend and a real browser (this
  stage's Claude-in-Chrome session stayed connected throughout, unlike
  several recent stages): registered a buyer and a dietitian, promoted
  the dietitian via direct SQL, created a real `UNPAID` transaction and a
  real review via `curl`, then opened the actual app. Confirmed the
  marketplace listing renders with real photos/ratings/truncated
  experience text for every previously-seeded dietitian across this
  session's whole history (a good incidental full-regression check on
  `list_all()` + email resolution), confirmed it's visible while logged
  out (genuinely public browsing), and — logged in as the seeded buyer —
  confirmed the exact dietitian with the open transaction appeared under
  a "Twoi dietetycy" section while the rest stayed under "Wszyscy
  dietetycy". `docker compose down` after.
- **Stage 3 — Public dietitian profile view — DONE**: click a card → full
  profile (experience, diplomas, description, photos, reviews, the two
  offers). "Zgłoś się" per offer.

  **Design decision**: a `Dialog` modal (`DietitianProfileModal.tsx`),
  not a new route — same choice already made for `ProfileModal`/
  `AuthPopup`, and the existing router only knows `/` and
  `/:conversationId` (Etap 0's own scoping); adding a `/dietitian/:id`
  route for one view would be new routing infrastructure the plan never
  asked for. Selection state (`selectedDietitianId`) lives in `RightRail`
  itself, which already owns the cards.

  **"Zgłoś się" renders but is inert this stage** — both offer buttons
  are `disabled` with a `title="Wkrótce dostępne"` tooltip rather than
  silently doing nothing on click; Stage 4 is explicitly "selecting an
  offer creates an `UNPAID` transaction", so wiring that here would jump
  the stage. A disabled, honestly-labeled button beats either a dead
  click handler or hiding the offers entirely — the marketplace's whole
  point is showing what's for sale, even before checkout exists.

  Built: `DietitianCard` (in `RightRail.tsx`) is now a real `<button>`
  calling `onSelect(dietitian.user_id)`; `DietitianProfileModal.tsx` (new)
  fetches `GET /dietitian/{id}` via `useQuery(['dietitian-profile',
  dietitianId], ..., { enabled: dietitianId !== null })` and renders
  avatar/rating header, experience, diplomas (hidden when empty — most
  seeded profiles from earlier stages have none), description, a photo
  gallery (hidden when empty), the two offers (`OFFER_LABEL`/
  `OFFER_PRICE` — pulled out of `TransakcjeTab.tsx` into a shared export
  in `api/transactions.ts` rather than duplicated, since two call sites
  now need the same label/price mapping), and the reviews list (rating,
  comment, date — no reviewer identity, matching the backend's own
  public-review shape from Stage 1).

  Exit criteria met: no backend changes this stage. Frontend — 4 new
  `DietitianProfileModal.test.tsx` tests (closed/no-fetch when nothing
  selected, full render with diplomas/photos/offers/reviews, "Brak
  ocen"/"Brak opinii." for an empty profile, error state) + 1 new
  `RightRail.test.tsx` test (clicking a card opens the modal with that
  exact dietitian's data) — main frontend now at 116 tests, all passing.
  Both `npx tsc --noEmit` and `npm run build` clean.

  Live-verified in a real browser against the real Docker backend
  (Claude-in-Chrome stayed connected): browsed the marketplace as a
  guest, clicked a real seeded dietitian's card, confirmed the modal
  showed their real experience/description/9.0 rating/the one real
  review left in an earlier stage, confirmed both offer prices (49.00 zł
  / 149.00 zł) render correctly, and confirmed clicking "Zgłoś się"
  visibly does nothing (disabled, no request fired) — all while never
  logging in, confirming the whole flow (listing → profile) is genuinely
  public. `docker compose down` after.
- **Stage 4 — Offer selection → payment stub — DONE**: selecting an
  offer creates an `UNPAID` transaction (Etap 3 Stage 2) and shows a
  stand-in payment screen — a single "Zapłać" action that's honest about
  being a placeholder (no card form, no gateway redirect) — admin flips
  it to paid from the panel (Etap 3 Stage 3).

  **No new backend work this stage** — `POST /transactions` (Etap 3
  Stage 2) and `GET /transactions/me/purchases` (Etap 4 Stage 2) already
  cover everything this stage needed; purely frontend wiring.

  **Design decisions**:
  - **Per-offer state, computed from the buyer's own purchase history**
    — each offer independently renders one of four states by matching
    `getMyPurchases()` against `(dietitianId, offerType)`: no existing
    transaction → real "Zgłoś się" button; an `UNPAID` one → "Przejdź do
    płatności" (reopens the same payment stub without a new `POST`); a
    `PAID` one → "Opłacone ✓", no button at all (nothing invites a
    duplicate purchase through the UI, even though the backend itself
    doesn't block it). This also means revisiting a dietitian's profile
    after leaving mid-checkout picks up exactly where you left off.
  - **"Zgłoś się" disabled with a tooltip in two cases**: logged out
    ("Zaloguj się, aby się zgłosić") and viewing your own public profile
    as its own dietitian ("Nie możesz zgłosić się do własnej oferty") —
    the backend already rejects the guest case with 401 and the
    self-purchase case with 400 (`Transaction.create()`'s own guard from
    Etap 3), but pre-empting both in the UI is a cheap, already-known
    check (`isAuthenticated`/`user.user_id === dietitianId`) that avoids
    a round-trip to learn something already knowable client-side.
  - **"Zapłać" is honestly inert, not a fake success** — clicking it
    shows a toast ("Dziękujemy! Administrator potwierdzi płatność
    ręcznie.") and returns to the profile view, but calls no endpoint and
    never touches the transaction's status — there is no user-facing
    "mark paid" action anywhere in this system by design (Etap 3's own
    scope decision: only `ADMIN`/`SUPER_ADMIN` can flip that flag). A
    button that silently did nothing would be a dead click; one that
    pretended to charge a card would misrepresent a project that
    deliberately has no payment gateway. Confirmed live that the
    transaction's `PAID` state only ever changes via the real admin
    endpoint, never via this button.
  - **`OFFER_LABEL`/`OFFER_PRICE` centralized** in `api/transactions.ts`
    (moved out of `TransakcjeTab.tsx`, which already had its own copy) —
    two call sites needing the same offer→label/price mapping is exactly
    the point where de-duplicating stops being premature.
  - **New `notifyInfo` toast helper** alongside the existing
    `notifyError`, in the same `lib/toast.ts` — this stage's first
    non-error toast, same one-function-per-tone shape.

  Exit criteria met: no backend tests needed (no backend changes).
  Frontend — `DietitianProfileModal.test.tsx` rewritten to wrap renders
  in `AuthProvider` (the component now calls `useAuth()`) with 4 new
  tests (disabled + tooltip for a guest, disabled + tooltip for your own
  profile, full apply→payment-stub→pay flow with `notifyInfo` asserted,
  and the three-way existing-transaction states in one profile) — 8
  tests total in that file, up from 4. Main frontend now at 120 tests,
  all passing. Both `npx tsc --noEmit` and `npm run build` clean.

  Live-verified against the real Docker backend and a real browser
  (Claude-in-Chrome stayed connected): registered a fresh buyer, clicked
  "Zgłoś się" on a real dietitian's "Ocena wygenerowanego planu" offer,
  confirmed the payment stub appeared with the real `49.00 zł` amount
  and the transaction existed in Postgres (`SELECT ... FROM
  transactions`) as `UNPAID`; confirmed the right rail's "Twoi
  dietetycy" pinning updated live in the background (the `['my-purchases']`
  cache invalidation reaching `RightRail` too, not just this modal);
  clicked "Zapłać" and confirmed the toast fired and no transaction
  field changed; reopened via "Przejdź do płatności" and confirmed it's
  the same transaction, no duplicate created; bootstrapped a real
  `SUPER_ADMIN` and called the actual `POST
  /admin/transactions/{id}/mark-paid` endpoint via `curl`; reloaded and
  confirmed the offer now shows "Opłacone ✓" while the *other* offer
  (`Indywidualny plan`) independently still showed "Zgłoś się" — proving
  the per-offer state is tracked correctly, not per-dietitian.
  `docker compose down` after.
- **Stage 5 — Tests + docs sync — DONE**: closing stage for Etap 4 —
  documentation sync across all three docs plus the closing full-suite
  gate, no new application code.

  **`docs/api.md`**: added three new `# Dietitian API` sections (`GET
  /dietitian` — the public marketplace listing, `GET
  /dietitian/{dietitian_id}` — the public profile with reviews, `POST
  /dietitian/{dietitian_id}/reviews`) and one new `# Transactions API`
  section (`GET /transactions/me/purchases`); fixed two stale sentences
  found while writing this — the module's own auth intro said "All
  endpoints below require Authorization: Bearer" (no longer true, the
  two marketplace reads are genuinely public) and `GET /transactions/me`
  said "there is no buyer-facing purchases list yet" (Stage 2 built
  exactly that) — both corrected rather than left to rot; updated the
  Overview bullet list.

  **`docs/domain-model.md`**: new `## Review` entity section in `# 7.
  Dietitian Domain` (the upsert rule, self-review guard, rating/comment
  validation, the CASCADE/CASCADE FK pair, the no-engagement-gate and
  no-reviewer-identity scope decisions); `## Dietitian Context`
  responsibilities extended; Aggregates/Persistence Mapping/Relationships
  updated (+`Review`, the second entity — after `Transaction` — where
  `User` plays two roles in one relationship, though here both sides are
  `CASCADE` rather than asymmetric); found and fixed a second stale
  sentence — `DietitianProfile`'s own doc still said profile creation on
  approval was "not yet automated," true when written in Etap 1 but
  false since Etap 2 actually built `ApproveDietitianApplicationUseCase`;
  Future Extensions' Phase-12-progress note updated (Etap 3 now reads
  simply "done" instead of the stale "done through Stage 4," Etap 4 now
  the one "done through Stage 4," Etaps 5-6 not started).

  **`docs/architecture.md`**: added a genuinely new, previously-missing
  `## Dietitian Module (Phase 12)` section — this module had **no**
  dedicated architecture write-up at all until now, a gap dating back to
  Etap 1 that this closing stage's full read-through surfaced (Admin and
  Transactions modules each got one when they were built; Dietitian
  itself never had — only scattered mentions from those two). Documents
  applications, profile management, the `FileStorage` port, and this
  etap's own public-marketplace/review additions in one place. Also:
  Transactions Module responsibilities gained the `GET
  /transactions/me/purchases` bullet; Data Ownership Rules gained a
  paragraph on `dietitian`'s three Etap-4 use cases reusing `identity`'s
  `UserRepository` directly (same not-an-exception pattern already
  established); the Docker section's `db` service description — stale
  since Etap 3 ("PostgreSQL (Identity, Dietitian)", missing
  Transactions) — corrected.

  **`README.md`**: checked, needed no change — whole-phase granularity
  only, same finding as every prior etap's closing stage.

  **`docs/openapi.json`**: regenerated via
  `PYTHONPATH=. python scripts/export_openapi.py`; confirmed via `grep`
  that `/api/v1/dietitian`, `/api/v1/dietitian/{dietitian_id}`,
  `/api/v1/dietitian/{dietitian_id}/reviews`, and
  `/api/v1/transactions/me/purchases` are all present.

  Exit criteria met — closing-gate full suites: backend **513 passed, 0
  failed** (34 new tests across this etap: 29 from Stage 1's Review
  domain + marketplace reads, 5 from Stage 2's `GetMyPurchasesUseCase` +
  API — up from 479 at Etap 3's close; Stages 3/4 added no backend
  code). Main frontend: **120 passed** (13 new across this etap — 4 from
  Stage 2's `RightRail` marketplace tests, 5 from Stage 3's
  `DietitianProfileModal`/click-through tests, 4 net from Stage 4's
  offer-flow rewrite — up from 107 at Etap 3's close). `frontend-admin`:
  **28 passed**, unchanged — this etap never touched the admin app.
  `npx tsc --noEmit` and all three `npm run build`s clean (main app's
  only warning is the same pre-existing, harmless "chunks larger than
  500 kB" one).

  No new bugs found this stage beyond the two doc staleness issues above
  — this was a pure docs-and-verification close-out, consistent with
  every prior etap's own Stage 5/6.
- **Etap 4 (Marketplace & reviews): DONE** — all 5 stages complete
  (review domain + public marketplace read endpoints, right-rail
  listing wired to real data with purchase-based pinning, public
  dietitian profile view with reviews, offer selection → real
  transaction + honest payment stub, this docs/tests sync).

---

### Branding — Mycelo (decided before Etap 5, applies to everything after)

The product is renamed **Mycelo** (was "Diet AI") — a full rebrand, not
just a new logo: `Settings.app_name`, both frontends' `<title>`, the AI's
own system-prompt self-introduction, transactional email subject/body
text, README.md, and every doc's title header were all updated in one
pass (see the git history around this note for the exact diff — not
re-derived here since it's plain mechanical text replacement, not a
design decision worth re-explaining).

**What *is* a lasting decision, and does need to be remembered**: the
brand mark is a mushroom, chosen from six proposed line-art/geometric/
mascot variants — "Wariant C" (a line-art silhouette: stroke-only dome
cap + rounded stem, no fill) is the one picked. Two colors carry the
whole brand:

- idle / everyday: a warm earthy brown (`--mycelo-idle` token, added to
  `frontend/src/index.css` — `#A9754C` light / `#C98A5F` dark),
- **notification / something-new state: the cap turns red** — reuses
  the existing `--destructive` token rather than a new color, since a
  notification-red and an error-red are the same semantic "pay
  attention" signal. This imitates a fly agaric (*muchomor*/*Amanita
  muscaria*) turning up red-capped once there's something to see —
  the whole reason a mushroom was chosen as the mark in the first place.

Implemented now, ready for later:

- `frontend/public/favicon.svg` and `frontend-admin/public/favicon.svg`
  — both replaced with the idle-state mark (Vite's unrelated default
  logo was still in place before this, never customized since Etap 0),
- `frontend/src/components/MyceloIcon.tsx` — a reusable component with
  an `alert` boolean prop that flips stroke color and adds a small spore
  dot; **Etap 5 Stage 4's notification badge should use this component**
  rather than inventing a separate bell/badge icon, so the "cap turns
  red" rule stays a single implementation, not one look on the favicon
  and a different one on the actual notification UI.

No infrastructure identifiers were touched — `docker-compose.yml`/
`docker-compose.test.yml` container names, the Postgres/Mongo database
name (`diet_ai`/`diet_ai_test`), and the dev SFTP/SMTP credentials all
still say `diet_ai`/`dietai`. Renaming those has zero brand benefit (no
user ever sees a container name) and real risk (existing local dev
volumes/data live under the `diet_ai` database name) — a deliberate
scope boundary, not an oversight, confirmed with the user before
starting this rebrand.

---

### Etap 5 — Kafka notifications + human-dietitian chat

Goal: the highest-infrastructure-risk etap — introduces Kafka from
scratch, plus a second chat surface distinct from the AI one.

- **Stage 1 — Kafka infrastructure**: single-broker Kafka in KRaft mode
  (no separate Zookeeper — the modern minimal setup, appropriate for a
  demo rather than a multi-broker production cluster) added to
  `docker-compose.yml`, plus a thin producer/consumer wrapper started
  from `backend/app/main.py`'s lifespan (same place the existing
  email-retry background loop lives). First real event:
  `TransactionPaid` — Etap 3 Stage 3 already defines the
  `TransactionEventPublisher` port and calls it on every mark-paid; this
  stage swaps in a real `KafkaTransactionEventPublisher`, no change to
  that use case itself — a consumer creates
  a `Notification` row (new small table/collection — landing spot
  TBD during implementation, likely Postgres alongside `transactions`
  since notifications are per-user transactional state) and — this is
  the dietitian-facing contact reveal — makes the paying user's contact
  visible to the dietitian.
- **Stage 2 — New `backend/modules/messaging/` module** (kept separate
  from the AI `conversation` module, per the Grounding section above):
  `DietitianThread` (paired user + dietitian, tied to a paid
  transaction), `DietitianMessage` (sender USER or DIETITIAN, content,
  optional attached `diet_plan_id`, `created_at`). REST endpoints for
  listing a thread's messages and posting a new one — plain
  request/response, no WebSocket, per the confirmed polling decision.
- **Stage 3 — Human-chat UI**: once a transaction is paid, a contact
  card appears above the marketplace roster (Etap 4 Stage 2's rail).
  Opening it swaps `ChatCanvas` into a **human-chat variant** — same
  layout, but the background tint shifts toward green (a new set of
  design tokens, not a hardcoded color, so it composes with the existing
  light/dark token setup) so it's visually unmistakable that this isn't
  the AI. The composer gains a "send my generated plan" action (attaches
  a `diet_plan_id`, rendered in the thread as a compact `DietPlanCard`,
  reusing the existing component from Phase 10).
- **Stage 4 — Notification badges**: a small badge above the right rail
  for an unread dietitian message, and (Etap 3's event) a badge/toast
  for a newly-paid transaction becoming visible to the dietitian side.
  Polling-driven per the confirmed decision — a `useQuery` with a short
  `refetchInterval` against a `GET /notifications` endpoint, not a push
  channel.
- **Stage 5 — Tests + docs sync**: this etap's tests need a
  docker-compose.test.yml Kafka service too (the existing ephemeral
  Postgres/Mongo test-stack pattern in `conftest.py` extends to Kafka).

---

### Etap 6 — Cross-cutting polish + docs/status sync

Goal: close out Phase 12 the same way Phase 10 closed out — once every
piece above is live, a consistency pass + final doc sync, not a new
feature.

- **Stage 1 — Design-system consistency pass** on everything built in
  this phase (reusing `Badge`/`FieldError`/`EmptyState`/`Skeleton` from
  Phase 10 Etap 5 rather than reinventing per-screen patterns — a mirror
  of that etap's own audit, scoped to the new screens this phase adds).
- **Stage 2 — Manual smoke walkthrough**: a new
  `docs/dietitian-marketplace-smoke-walkthrough.md` (same spirit as
  Phase 10's own walkthrough doc) covering: apply as a dietitian → admin
  approves → dietitian completes their profile → a second user browses
  the marketplace → leaves a review → selects an offer → admin marks
  the transaction paid → dietitian sees the contact reveal → both sides
  chat and exchange a generated plan.
- **Stage 3 — Docs & status sync**: `README.md`, this roadmap's own
  status table, and `docs/architecture.md` all updated to reflect
  Phase 12 as done — same closing move as Phase 10 Etap 6 Stage 3.

---

## Open items intentionally deferred (not silently dropped)

- **Raporty tab actual report generation** — explicitly named by the
  user as "do implementacji później" (Etap 2 Stage 5 ships only the
  placeholder).
- **A real payment gateway** — explicitly out of scope for this demo
  per the user; the admin mark-paid/unpaid toggle is the whole payment
  story for now.
- **Object storage for photos / a real message broker beyond Kafka's
  minimal setup / WebSockets** — all considered and deliberately not
  chosen, per the confirmed design decisions above; revisit only if a
  concrete need shows up later, not speculatively.
