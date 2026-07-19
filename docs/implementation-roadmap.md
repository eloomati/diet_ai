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

## Status (as of 2026-07-19)

```
Phase 0-11  - Foundation through Testing   DONE — see the archived roadmap
Phase 12    - Dietitian Marketplace,       PLANNED — not started. This
              Admin Panel & Roles           document's prospective plan,
                                            awaiting stage-by-stage
                                            implementation.
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

- **Stage 1 — New `backend/modules/dietitian/` module**: `DietitianApplication`
  entity (`status`: `PENDING`/`APPROVED`/`REJECTED`, applicant user id,
  submitted form fields, `reviewed_by`/`reviewed_at`), `DietitianProfile`
  entity (experience text, diplomas, description, up to 3 photo
  references, two fixed `Offer`s — "oceń wygenerowany plan" /
  "stwórz plan indywidualny" — each with a price). Mongo persistence
  (matching `conversation`/`nutrition`'s existing choice, not Postgres —
  this is document-shaped content, not transactional).
- **Stage 2 — Apply flow**: `POST /dietitian/applications` (any `USER`,
  one pending application at a time). Frontend: "Zgłoszenie dietetyka"
  button in the bottom-right corner of the Profil tab, opening a form
  (experience, description, etc.) — matches the mockup precedent of
  building real screens against the existing design system
  (`FieldError`/`Skeleton`/`EmptyState`/`Badge` from Etap 5's pass).
- **Stage 3 — Photo upload**: new generic upload endpoint
  (`POST /dietitian/profile/photos`, max 3, local-disk storage per the
  confirmed decision, served via a static route) — built as a small
  reusable port (`FileStorage` interface + local-disk adapter) so a
  later swap to object storage doesn't touch call sites.
- **Stage 4 — Dietitian's own profile management (main app)**: once
  `role == DIET_USER` (set in Etap 2 via admin approval), the Profil
  modal gains a **"Profil dietetyka"** tab (alongside today's
  Profil/Plany/Kalendarz) — edit experience/diplomas/description/photos,
  view submitted reviews (Etap 4). A **"Transakcje"** tab also appears
  here (Etap 3 wires its actual content) showing transactions routed to
  this dietitian.
- **Stage 5 — Tests + docs sync**.

---

### Etap 2 — Admin backend module + `frontend-admin` app

Goal: the actual admin panel — a separate app, separate backend module,
gated to `ADMIN`/`SUPER_ADMIN`.

- **Stage 1 — New `backend/modules/admin/` module**: no new persistence
  of its own — its use cases call the existing `identity`/`dietitian`/
  (later) `transactions` modules' repository ports directly (an
  established cross-module pattern already used elsewhere in this
  codebase), so admin logic stays a thin orchestration layer rather than
  a second source of truth. Endpoints: `GET /admin/users` (list, no
  sensitive fields), `POST /admin/users/{id}/activate`,
  `POST /admin/users/{id}/ban`, `DELETE /admin/users/{id}`,
  `GET /admin/dietitian-applications`,
  `POST /admin/dietitian-applications/{id}/approve` (promotes the user
  to `DIET_USER` via Etap 0 Stage 1's `change_role()`),
  `POST /admin/dietitian-applications/{id}/reject`. All gated by
  Etap 0's `require_role(ADMIN, SUPER_ADMIN)` (role-change itself stays
  `SUPER_ADMIN`-only per Etap 0 Stage 3).
- **Stage 2 — `frontend-admin/` scaffold**: new sibling folder to
  `frontend/` — its own Vite+React+TS+Tailwind v4 project (per the
  confirmed decision), reusing the same `docker-compose.yml` pattern as
  `frontend`'s own service (new `frontend-admin` service, its own port).
  Login reuses the existing `/auth/login` endpoint (no separate admin
  auth system) — the login form just also checks the returned role and
  refuses entry below `ADMIN`. Layout: a plain, legible shell (no rail
  choreography like the main app) — a top bar with a "Powrót do
  aplikacji" link back to the main frontend, and a tab bar: Raporty /
  Użytkownicy / Dietetycy / Transakcje (Transakcje's real content
  arrives in Etap 3).
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
