# Diet AI - Implementation Roadmap

## Purpose

This document defines the implementation order of the Diet AI project.

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
                                              frontend-admin): Stage 2/6
                                            Etaps 3-6: not started
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
- **Stage 3 — Użytkownicy tab**: list, activate/ban/delete actions;
  role-change control visible only when the logged-in admin is
  `SUPER_ADMIN`.
- **Stage 4 — Dietetycy tab**: list pending/approved/rejected
  applications, approve/reject actions.
- **Stage 5 — Raporty tab placeholder**: an explicit "coming later"
  empty state (matching this project's existing convention of shipping
  honest placeholders — e.g. the main app's "Co nowego" rail before this
  phase) — no report generation logic yet, out of scope per the user's
  own framing ("do implementacji później").
- **Stage 6 — Tests + docs sync**.

---

### Etap 3 — Transactions module

Goal: real Postgres-backed transaction records, admin-toggleable paid
status, no real payment gateway (per the user's explicit demo-scope
call, same spirit as this project's existing Mock AI provider / Mailhog
/ local SFTP stand-ins for real external services).

- **Stage 1 — New `backend/modules/transactions/` module, Postgres
  schema**: `transactions` table — id, `user_id` (buyer), `dietitian_id`
  (nullable-safe FK to the dietitian's user), `offer_type` (plan-review
  vs individual-plan), `amount`, `status` (`PENDING`/`PAID`/`UNPAID`/
  `CANCELLED` — exact states firmed up during implementation),
  `created_at`, `paid_at`. Postgres, not Mongo — this is the one new
  module that's genuinely transactional/relational, matching Identity's
  existing choice of Postgres for the same reason.
- **Stage 2 — Create-transaction use case**: fired when a user selects
  a dietitian's offer (Etap 4 wires the actual UI trigger) — creates a
  `PENDING` transaction, no payment gateway call.
- **Stage 3 — Admin mark paid/unpaid**: `POST /admin/transactions/{id}/mark-paid`
  / `.../mark-unpaid` (admin-only) — marking paid publishes the Kafka
  `TransactionPaid` event Etap 5 consumes.
- **Stage 4 — Transakcje tabs wired**: both the admin panel's Transakcje
  tab (all transactions) and the dietitian's own Transakcje tab from
  Etap 1 Stage 4 (only transactions routed to them) now show real data.
- **Stage 5 — Tests + docs sync**.

---

### Etap 4 — Marketplace & reviews

Goal: users can actually discover and hire a dietitian.

- **Stage 1 — Review domain**: `Review` entity (reviewer user id,
  dietitian id, rating 1-10, comment, created_at) in the `dietitian`
  module — one review per (user, dietitian) pair, editable by its
  author. `POST /dietitian/{id}/reviews`, aggregated average rating
  exposed on the dietitian's public profile/listing.
- **Stage 2 — Right rail becomes the marketplace listing**: replaces
  today's static "Co nowego" placeholder (which Etap 5 of Phase 10
  explicitly described as "reserved for future roadmap items" — this is
  that future). Shows dietitian cards (photo thumbnail, name, experience
  abbreviated e.g. "5 lat", average rating) — dietitians the user has an
  active/paid engagement with pinned at the top, the rest of the roster
  below.
- **Stage 3 — Public dietitian profile view**: click a card → full
  profile (experience, diplomas, description, photos, reviews, the two
  offers). "Zgłoś się" per offer.
- **Stage 4 — Offer selection → payment stub**: selecting an offer
  creates a `PENDING` transaction (Etap 3 Stage 2) and shows a stand-in
  payment screen — a single "Zapłać" action that's honest about being a
  placeholder (no card form, no gateway redirect) — admin flips it to
  paid from the panel (Etap 3 Stage 3).
- **Stage 5 — Tests + docs sync**.

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
  `TransactionPaid` (published by Etap 3 Stage 3) → a consumer creates
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
