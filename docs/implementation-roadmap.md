# Mycelo - Implementation Roadmap

## Purpose

This document defines the implementation order of the Mycelo project.

The goal is to build the system incrementally while keeping architecture clean.

Each phase should result in a working part of the system.

**History**: Phases 0-11 (backend + the full frontend, Etap 0-6) and
Phase 12 (Dietitian Marketplace, Admin Panel & Roles, Etap 0-5, Etap 6
skipped) are done — see
`docs/implementation/implementation-roadmap-done190726.md` and
`docs/implementation/implementation-roadmap-done220726.md` for their
complete stage-by-stage logs. This document picks up at Phase 13.

---

## Status (as of 2026-07-22)

```
Phase 0-12  - Foundation through Dietitian  DONE — see the two archived
              Marketplace                    roadmaps
Phase 13    - Quality, Security &           NOT STARTED
              Personalization                Etap 0 (Security & session
                                                hardening): not started
                                              Etap 1 (User display
                                                names): not started
                                              Etap 2 (Chat & diet-plan
                                                UX polish): not started
                                              Etap 3 (Multi-plan
                                                calendar): not started
                                              Etap 4 (Admin panel
                                                pagination): not started
```

---

# Phase 13 - Quality, Security & Personalization

## Context

A batch of bugs and gaps the user collected while using the app
day-to-day since Phase 12 closed — spanning a real security warning
(JWT secret length), missing safeguards, rough UX edges, and a couple of
genuinely new features (per-user display names, a multi-plan calendar).
Grouped into 5 etaps by theme rather than strictly by when each item was
reported, so related backend+frontend work lands together.

Investigated against the actual current code before this breakdown was
written (not assumed from the bug report alone):

- The JWT secret really is under the 32-byte minimum PyJWT recommends
  for HS256, in both `docker-compose.yml` (`change-me-in-prod`, 17
  bytes) and `.env.example` (`change-me`, 9 bytes).
- The frontend's `QueryClient` is never `.clear()`ed on
  login/logout/register — confirmed stale cross-account cache is a real
  bug, not a one-off.
- `ChatCanvas`'s send-message mutation has no optimistic update — the
  user's own bubble only appears once the full AI round trip completes,
  confirmed as reported.
- The diet-plan-generation mutation has no `onSuccess`/`onError`
  handling at all (unlike the archive/delete mutations in the same
  file, which do) — confirmed silent-failure gap.
- Reviews are **not actually fully anonymous already** — `reviewer_id`
  (a raw UUID) is already returned by `POST /dietitian/{id}/reviews`'s
  response schema. The real gap is that nothing resolves that UUID to
  anything human-readable — which this phase's display-name feature
  fixes as a side effect once wired through.
- `CreateTransactionUseCase` validates the dietitian side (must be a
  real `DIET_USER`) but never checks the buyer's own account `status` —
  confirmed a banned/inactive user can still buy today.
- The calendar tab (`KalendarzTab.tsx`) already has working prev/next
  week navigation scoped to one selected plan's real date span, and meal
  rescheduling already auto-saves via an immediate `PATCH` on every
  drag (no separate "Save" button, already fully persisted) — so the
  user's "eksportować po zmianach" ask was already functionally
  satisfied for a *single* plan. The actual gaps are: no export action
  inside the Kalendarz tab itself (it only lives in the Plany tab), and
  no way to view/select *more than one* plan on the calendar at once —
  which is what the user actually meant by "cały rok po tygodniu
  przewijać" once clarified (stitch several non-overlapping generated
  plans together, not raise the single-plan 14-day cap).
- A separate inconsistency surfaced during this same investigation, not
  yet raised by the user: dragging a meal to a *different day* column
  in the calendar only changes its *time*, not its day — the `PATCH`
  payload has no day field, so a cross-day drop silently keeps the meal
  on its original day. Raised with the user and resolved below (full
  day+time move, not left as-is).
- Admin-panel pagination — confirmed no `limit`/`offset`/`page` params
  exist on any of `GET /admin/users`, `GET /admin/dietitian-applications`,
  or `GET /admin/transactions` today; all three return everything
  unpaginated.

## Design decisions settled before this phase's breakdown

- **`User.display_name` for everyone, *plus* optional
  `first_name`/`last_name` on `DietitianProfile` a dietitian can choose
  to fill in.** Every account (user or dietitian) can set a generic
  `display_name`. A dietitian additionally has the *option* — not a
  requirement — to also set a real first + last name; if they do, that
  real name is what's shown publicly for them (marketplace, chat,
  reviews) instead of their `display_name`. Filling the fields in *is*
  the choice — no separate toggle/preference flag needed. Display-name
  resolution order, in every read model that surfaces a person's
  identity: dietitian's `first_name + last_name` (if both set) →
  `display_name` (if set) → email (final fallback, unchanged from
  today).
- **Validation rule for `display_name` and dietitian
  `first_name`/`last_name`**: Polish letters, digits, and single spaces
  between characters only — no other special characters. One shared
  value-object validator reused across all three fields. Enforced both
  at the domain level (defense in depth against malformed data
  regardless of entry point) and confirmed as a parameterized-query-only
  persistence path (SQLAlchemy already parameterizes by default; this is
  a matter of confirming no raw string interpolation is introduced when
  these fields are added, not a new mechanism).
- **Redis is scoped to exactly one job this phase: rate-limiting the
  auth endpoints** (`POST /auth/login`, `/auth/register`,
  `/auth/password-reset/request`) — not a general cache layer. Matches
  this codebase's own "mock-by-default, swap in the real thing behind a
  provider flag" pattern (`ai_provider`/`email_provider`/`sftp_provider`/
  `kafka_provider`): a `RateLimiter` port with an in-memory
  `NoOpRateLimiter`/mock default for tests and a `RedisRateLimiter` real
  implementation, gated behind a new `rate_limit_provider` setting.
  Broader caching (marketplace listing, notification polling) was
  considered and deliberately not chosen — premature at this project's
  actual scale, and not a problem anyone has actually hit yet.
- **Admin-panel pagination**, per the user's own clarification, means
  **all three `frontend-admin` tabs** (Users, Dietitian Applications,
  Transactions) — not the main app's user-facing lists (marketplace,
  diet plans, purchases), which stay as-is for this phase.
- **The multi-plan calendar's overlap rule is enforced client-side**,
  not as a new backend constraint on plan generation — a user can
  already generate two date-overlapping plans today (nothing stops
  them), and nothing about that changes. The calendar's own multi-select
  picker simply refuses to let the user *view* two overlapping plans
  together, computed from each plan's own `created_at` +
  `duration_days`, entirely in the frontend.
- **A dragged meal can move to a different day, not just a different
  time** — the user chose full freedom over the current
  time-only-reschedule constraint. `RescheduleMealUseCase`'s payload
  gains a day field; the calendar's own drag-and-drop finally does what
  it already visually implies.
- **A new backend endpoint exports several selected plans combined into
  one CSV** — not limited to re-exporting whichever single plan backs
  the currently-visible week. The multi-plan calendar's own export
  action calls this new combined endpoint with the set of currently
  selected (non-overlapping) plan ids.

---

### Etap 0 — Security & Session Hardening

Goal: close the concrete security/safety gaps found — a weak JWT
secret, no auth rate limiting, no buyer-status check on purchases, and
stale cross-account session data in the browser.

- **Stage 1 — JWT secret hardening — DONE**: replaced the under-32-byte
  placeholders in `docker-compose.yml` (17 bytes), `.env.example` (9
  bytes), and `Settings.jwt_secret_key`'s own Python default (21 bytes)
  with three distinct, properly `secrets.token_urlsafe(32)`-generated
  values (each 53-64 bytes as a UTF-8 string) — still clearly
  "change-me" dev placeholders, just long enough to stop triggering the
  warning; added a new `Settings` `@model_validator(mode="after")`
  (`_reject_weak_jwt_secret_outside_dev`) that raises a clear
  `ValueError` if `jwt_secret_key` is under 32 bytes, skipped only when
  `app_env == "dev"` or `testing` — so a short key is merely tolerated
  locally but fails fast anywhere else, rather than only ever producing
  a library warning easy to miss in a log stream.

  Built exactly per the Stage 1 plan — no new design decisions needed,
  the fix was mechanical once the three weak-default locations were
  confirmed.

  Exit criteria met: added `backend/tests/test_settings.py` (4 new
  tests — rejects a short key outside dev/testing, accepts one in dev,
  accepts one when `testing=True`, accepts a long-enough key outside
  dev) — ran alongside `backend/tests/test_app_startup.py` since both
  touch `Settings`/app creation, 7 passed, 0 failed. `PYTHONPATH=. python
  -c "from backend.app.main import create_app; create_app()"` confirms
  the app still boots cleanly with the new defaults.

  Live-verified against the real Docker stack: brought up
  `backend`+its dependencies, registered and logged in a user (forcing a
  real JWT encode/decode round trip), then `docker compose logs backend
  | grep -i InsecureKeyLength` — no match, confirming the warning is
  actually gone end-to-end, not just absent from a unit test. `docker
  compose down` after.
Design decisions settled right before building Stage 2 (none of this was
in the codebase to mirror exactly — rate limiting is the first
cross-cutting infra this project has added since Kafka, and the first
thing anywhere in this codebase to read the request's client IP):

- **Port location**: `backend/modules/identity/application/ports/rate_limiter.py`
  — same directory as `EmailSender`'s port, since both endpoints it
  guards live in `identity`. Signature: `async def hit(self, key: str,
  max_attempts: int, window_seconds: int) -> bool` (`True` = allowed),
  not a raise-on-exceeded exception — keeps the port a plain check, with
  the 429 decision made once, in the FastAPI dependency that calls it,
  not duplicated per call site.
- **Redis connection is a shared singleton, not per-request** — unlike
  `EmailSender` (deliberately per-request, no persistent connection
  worth reusing), Redis needs a long-lived connection the same way
  Postgres/Mongo/the Kafka producer already do. `backend/shared/redis/client.py`
  gets the same `init_redis_client`/`close_redis_client`/`get_redis_client`
  shape as `shared/messaging/kafka.py`, wired into `main.py`'s lifespan
  only when `rate_limit_provider == "redis"` (same conditional-startup
  pattern Kafka already uses).
- **Fixed-window counter via `INCR` + `EXPIRE`-on-first-hit** — the
  standard simple Redis rate-limit pattern (`INCR key`; if the result is
  `1`, `EXPIRE key window_seconds`; block once the count exceeds
  `max_attempts`). Not a sliding-window/token-bucket algorithm — a small
  window-boundary imprecision is an acceptable tradeoff against the
  extra complexity for a demo-scoped anti-brute-force guard, not a
  billing-grade limiter.
- **Rate-limit key is `f"{action}:{client_ip}"`** — one counter bucket
  per endpoint per IP (a login flood doesn't also throttle registration
  from the same IP, and vice versa). `RedisRateLimiter` takes the Redis
  client via constructor injection against a narrow Protocol (`incr`,
  `expire`) — same testability pattern as
  `KafkaTransactionEventPublisher`'s `_KafkaProducerLike` Protocol —
  rather than reaching into the global singleton directly.
- **`NoOpRateLimiter` always returns `True`** (never blocks) — the
  default (`rate_limit_provider: mock`), so `pytest` never needs a real
  Redis, matching `ai_provider`/`email_provider`/`sftp_provider`/
  `kafka_provider`'s exact mock/real split.
- **New `ErrorCode.RATE_LIMITED`**, raised as `AppException(code=...,
  status_code=429)` directly inside the FastAPI dependency that calls
  `RateLimiter.hit()` — same "router/dependency raises `AppException`
  with an explicit status code" convention already used everywhere else
  in this codebase, not a new mapping table.
- **`redis-test` in `docker-compose.test.yml` is on-demand, not
  autouse** — exactly the `kafka_test_broker` precedent from Etap 5: a
  new non-autouse `redis_test_broker` session fixture, requested only by
  the one new rate-limiting integration test, so the always-on
  Postgres+Mongo fixture stays untaxed.

- **Stage 2 — Redis-backed auth rate limiting — DONE**: built exactly
  per the design decisions above. `backend/modules/identity/application/ports/rate_limiter.py`
  (`RateLimiter.hit(key, max_attempts, window_seconds) -> bool`) +
  `NoOpRateLimiter` (always allows, the default) +
  `RedisRateLimiter` (fixed-window `INCR`+`EXPIRE`-on-first-hit, takes
  the client via a narrow `_RedisLike` Protocol) +
  `build_rate_limiter(settings)` factory, gated on the new
  `rate_limit_provider: mock | redis` setting. A new
  `backend/shared/redis/client.py` singleton
  (`init_redis_client`/`close_redis_client`/`get_redis_client`) mirrors
  `shared/messaging/kafka.py`'s exact shape, wired into `main.py`'s
  lifespan only when `rate_limit_provider == "redis"`. A new
  `rate_limited(action)` FastAPI dependency factory
  (`backend/modules/identity/api/dependencies/rate_limit_dependency.py`,
  same "factory returning a dependency" shape as `require_role`) reads
  `request.client.host`, calls `RateLimiter.hit()` with a
  `f"{action}:{client_ip}"` key, and raises a new
  `AppException(code=ErrorCode.RATE_LIMITED, status_code=429)` when
  blocked — added as a fourth `Depends(...)` parameter on
  `register`/`login`/`request_password_reset` in `auth_router.py`,
  changing nothing else about those handlers. New `redis`/`redis-test`
  Docker services (dev: always-on, real by default like Kafka/AI/Email
  in dev; test: on-demand via a new `redis_test_broker` fixture,
  mirroring `kafka_test_broker` exactly). Filled in two related gaps
  found while touching these same files: Kafka's own settings were
  missing from `.env.example` entirely since Etap 5 — added alongside
  the new rate-limit settings.

  Exit criteria met: 5 new unit tests
  (`backend/modules/identity/tests/test_rate_limiter.py` — `NoOpRateLimiter`
  always allows; `RedisRateLimiter` against a fake in-memory Redis-like
  stub: allows up to the max, blocks past it, sets expiry only on the
  first hit, keeps independent counters per key) + 2 new integration
  tests against a real on-demand Redis broker
  (`test_rate_limit_integration.py` — repeated `/auth/login` attempts
  actually get `429`'d past the threshold; flooding `/auth/login`
  doesn't block `/auth/register` from the same IP). Full backend suite
  run (cross-cutting — this stage's endpoints are used by nearly every
  other module's own tests via `register_and_login`-style helpers):
  **572 passed, 0 failed**, up from 565 after Stage 1. `pytest` still
  needs zero real Redis by default (`redis_test_broker` only starts for
  the 2 tests that request it).

  Live-verified against the real Docker stack: 5 rapid `/auth/login`
  attempts with wrong credentials all returned `401`, the 6th returned
  `429 RATE_LIMITED`; a `/auth/register` call from the same blocked IP
  still succeeded (`201`) — confirming the separate-bucket-per-action
  design; `docker compose exec redis redis-cli KEYS "*"` showed exactly
  `login:<ip>` and `register:<ip>`, confirming the key shape matches the
  design. `docker compose down` after.
- [ ] **Stage 3 — Buyer account-status safeguard**:
      `CreateTransactionUseCase` resolves the buyer via `UserRepository`
      and rejects (`403` or similar) unless the buyer's own `status` is
      `ACTIVE` — mirrors the existing dietitian-side validation, just
      for the other party.
  - Exit criteria: a banned/inactive user's `POST /transactions` call
    fails with a clear error code; an active user is unaffected.
- [ ] **Stage 4 — Frontend session/cache reset across account
      switches**: `queryClient.clear()` called on login, logout, and
      register in `AuthContext.tsx` — so a newly-logged-in session never
      shows a previous account's cached profile/conversations/plans/etc.
  - Exit criteria: logging out of account A and into account B shows no
    stale data from A anywhere in the app (verified live, not just by
    code inspection).
- [ ] **Stage 5 — Tests + docs sync**: closing stage for this etap.

---

### Etap 1 — User Display Names

Goal: everyone can set their own display name; dietitians additionally
have the option to display their real first + last name instead.
Validated, and shown everywhere email/UUID currently leaks through.

- [ ] **Stage 1 — `display_name` domain field + dietitian
      `first_name`/`last_name`**: `display_name` added to `User`
      (nullable — falls back to email wherever currently shown, until
      set); `first_name`/`last_name` added to `DietitianProfile` (both
      nullable, optional, independent of `display_name`). One shared
      value-object validator (Polish-letters/digits/single-spaces-only)
      reused across all three fields; new migration(s) for both tables.
  - Exit criteria: domain-level tests cover the validator's accept/reject
    cases for all three fields; migrations apply cleanly.
- [ ] **Stage 2 — Propagate into read models**: a shared resolution rule
      — dietitian's `first_name + last_name` (if both set) →
      `display_name` (if set) → email (fallback) — applied everywhere a
      person's identity is currently surfaced via email/UUID: messaging
      thread `other_participant_email`-equivalent, review responses
      (resolving `reviewer_id`), marketplace dietitian listing/profile,
      chat.
  - Exit criteria: each of those API responses carries the resolved
    name (per the fallback order above) alongside/instead of the raw
    identifier, per endpoint.
- [ ] **Stage 3 — Frontend: set/edit + display everywhere**: a
      `display_name` field in the profile UI for every account; an
      additional, clearly-optional first-name/last-name field pair in
      the dietitian profile editor. Every place in the UI currently
      showing an email or UUID (chat bubbles, messaging thread cards,
      review cards, marketplace dietitian cards) switches to showing the
      resolved name.
  - Exit criteria: live-verified across chat, messaging, reviews, and
    marketplace views — including a dietitian who has set a real name
    showing that instead of their `display_name`/email.
- [ ] **Stage 4 — Registration form**: adds a confirm-password field
      (client-side match validation before submit); optionally prompts
      for a display name at registration (design decision to confirm at
      this stage: prompt now vs. leave entirely to the profile screen
      later).
  - Exit criteria: mismatched passwords block submission with a clear
    inline error; registration still succeeds end-to-end.
- [ ] **Stage 5 — Tests + docs sync**: closing stage for this etap.

---

### Etap 2 — Chat & Diet Plan UX Polish

Goal: the rough day-to-day UX edges the user hit while actually using
the app.

- [ ] **Stage 1 — Optimistic own-message rendering**: the user's own
      sent message appears in the chat immediately on submit, not only
      after the AI's full response returns.
  - Exit criteria: live-verified — typing and sending shows the user's
    own bubble instantly, with the existing "Mycelo pisze
    odpowiedź…" placeholder following it, not preceding it.
- [ ] **Stage 2 — Diet-plan-generation feedback**: `onSuccess`/`onError`
      added to the generate-plan mutation — a success toast (or
      equivalent inline confirmation) and a clear error toast on
      failure, matching the pattern already used by
      archive/delete/send-message mutations elsewhere in this codebase.
  - Exit criteria: a forced generation failure surfaces a visible error
    instead of silently doing nothing.
- [ ] **Stage 3 — Rename conversations + diet plans**: new
      rename/edit-title endpoints for both (`PATCH` on each), plus
      inline-edit UI (e.g. click-to-edit the title) in the left rail's
      conversation history and the Plany tab's plan list.
  - Exit criteria: renaming persists across a refresh for both entity
    types.
- [ ] **Stage 4 — Copy + layout fixes**: empty-state copy in the left
      rail changes from "Brak jeszcze żadnych rozmów." to "Jeszcze z
      nami nie pogadałeś :("; root layout gets `overflow-hidden` (or
      equivalent) so panel-level scroll areas don't leak into a
      page-level scrollbar.
  - Exit criteria: no page-level scrollbar visible on any main view;
    new empty-state copy confirmed live.
- [ ] **Stage 5 — Tests + docs sync**: closing stage for this etap.

---

### Etap 3 — Multi-Plan Calendar

Goal: let a user view several of their own non-overlapping generated
plans together on one continuous calendar, freely move meals between
days, and export the combined selection directly from that view.

- [ ] **Stage 1 — Full day+time meal rescheduling**: `RescheduleMealUseCase`
      and its `PATCH /diet-plans/{id}/meals` payload gain a day field
      alongside the existing time field; `DietPlan.reschedule_meal()`
      updated to actually move the meal between `DietDay`s, not just
      re-time it within its original day. The calendar's drag-and-drop
      now sends the dropped-on day, not just the dropped-on time.
  - Exit criteria: dragging a meal to a different day column actually
    moves it there (persisted), live-verified; the existing same-day
    retime behavior is unaffected.
- [ ] **Stage 2 — Multi-select plan picker**: `KalendarzTab`'s current
      single-`Select` plan picker becomes a multi-select; client-side
      overlap validation (from each plan's `created_at` +
      `duration_days`) prevents selecting two plans whose ranges
      intersect.
  - Exit criteria: attempting to select two overlapping plans is
    blocked with a clear message; non-overlapping plans can be selected
    together.
- [ ] **Stage 3 — Combined week-by-week navigation**: the calendar's
      week grid merges all currently-selected plans' days into one
      continuous range, replacing the current single-plan `totalWeeks`
      calculation.
  - Exit criteria: navigating week-by-week across two or more selected
    non-overlapping plans shows the correct plan's meals for each week,
    with no gaps/overlaps in the combined range.
- [ ] **Stage 4 — Combined export**: a new backend endpoint exporting
      several selected plans' meals combined into one CSV (given a list
      of plan ids); an export action added directly in `KalendarzTab`
      (today it only exists in Plany) calling this new endpoint with
      whichever plans are currently selected.
  - Exit criteria: exporting from the calendar view with 2+ selected
    plans produces one correct combined CSV, live-verified; exporting
    with a single plan selected still works.
- [ ] **Stage 5 — Tests + docs sync**: closing stage for this etap.

---

### Etap 4 — Admin Panel Pagination

Goal: all three `frontend-admin` tabs (Users, Dietitian Applications,
Transactions) paginate instead of rendering every row unpaginated.

- [ ] **Stage 1 — Backend pagination**: `limit`/`offset` (or
      `page`/`page_size`) query params added to `GET /admin/users`,
      `GET /admin/dietitian-applications`, `GET /admin/transactions`,
      each returning a total count alongside the page of results.
  - Exit criteria: each endpoint's existing behavior is preserved when
    no pagination params are passed (backwards compatible), and returns
    a correctly-sized page + accurate total when they are.
- [ ] **Stage 2 — Frontend-admin pagination UI**: a shared
      pagination control wired into all three tabs.
  - Exit criteria: live-verified paging through each of the three tabs
    with enough seed data to span multiple pages.
- [ ] **Stage 3 — Tests + docs sync**: closing stage for this etap.

---

## Open items intentionally deferred (not silently dropped)

- **Raporty tab actual report generation** — explicitly named by the
  user as "do implementacji później" back in Phase 12 (still a
  placeholder).
- **A real payment gateway** — explicitly out of scope for this demo
  per the user; the admin mark-paid/unpaid toggle is the whole payment
  story for now.
- **Object storage for photos / a real message broker beyond Kafka's
  minimal setup / WebSockets** — all considered and deliberately not
  chosen in Phase 12; revisit only if a concrete need shows up later,
  not speculatively.
- **Redis as a general cache layer** (marketplace listing, notification
  polling) — considered for this phase and deliberately narrowed to
  auth rate-limiting only; revisit if a real performance problem shows
  up, not speculatively.
