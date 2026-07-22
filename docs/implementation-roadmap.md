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
Phase 13    - Quality, Security &           IN PROGRESS —
              Personalization                Etap 0 (Security & session
                                                hardening): DONE
                                              Etap 1 (User display
                                                names): DONE
                                              Etap 2 (Chat & diet-plan
                                                UX polish): DONE
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

### Etap 0 — Security & Session Hardening — DONE

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
- **Stage 3 — Buyer safeguards on `POST /transactions` — DONE**: verified
      live before writing any code that the banned/inactive half of this
      stage's original premise is **already enforced today** —
      `get_current_user` (the auth dependency every authenticated route
      already uses, including this one) calls
      `user.assert_can_authenticate()`, which rejects any non-`ACTIVE`
      status with `403 INACTIVE_USER` — confirmed by registering a
      buyer, banning them via the real `POST /admin/users/{id}/ban`, and
      calling `POST /transactions` with their already-issued token
      (`403 INACTIVE_USER`, not `201`). No new code needed for that
      half — this stage narrows to the one real gap: **an unverified
      email is not currently checked anywhere** (`email_verified` is
      tracked and exposed via `/auth/me`, but never enforced as a
      business rule). `CreateTransactionUseCase` fetches the buyer via
      its already-injected `UserRepository` (it only ever used
      `command.user_id` directly before) and rejects with a new
      `EmailNotVerifiedError` → `403 EMAIL_NOT_VERIFIED` unless
      `email_verified` is `True` — the dietitian side is untouched.
  - Exit criteria: an unverified buyer's `POST /transactions` call fails
    with `403 EMAIL_NOT_VERIFIED`; a verified buyer is unaffected; a
    banned buyer still gets `403 INACTIVE_USER` exactly as before (this
    stage doesn't touch that path).

  Built exactly per the corrected scope above: a new
  `EmailNotVerifiedError` (`transactions/application/use_cases/exceptions.py`)
  and a new `ErrorCode.EMAIL_NOT_VERIFIED`, mapped to `403` in
  `transaction_router.py`'s existing catch-clause style, right alongside
  `DietitianNotFoundError`. `CreateTransactionUseCase` now fetches the
  buyer via its already-injected `UserRepository` (previously the
  use case never resolved `command.user_id` into an actual entity at
  all) and raises before `Transaction.create()` runs. The dietitian-side
  check and the self-purchase invariant are both completely untouched.

  Fixing the existing test suite for this surfaced its own gap: every
  test across `transactions`, `admin`, and the Etap-5 Kafka integration
  test that creates a transaction via the real API had never actually
  verified its buyer's email (irrelevant before this stage, since
  nothing checked it) — 4 test files needed a `verify_email(user_id)`
  helper (added to `transactions`' and `admin`'s own `tests/db_helpers.py`,
  mirroring `promote_to_dietitian`/`promote_role`'s exact direct-DB-bootstrap
  shape) called wherever a buyer that needs to actually complete a
  purchase is set up. Two unit-test assertions also needed a real fix,
  not just a bystander update: `test_create_transaction_rejects_buying_your_own_offer`
  had the dietitian buying their own offer with an *unverified* email,
  which would now raise `EmailNotVerifiedError` before ever reaching the
  self-purchase check the test actually means to exercise — fixed by
  verifying that user first, so the test asserts what it always meant
  to.

  Exit criteria met: 2 new tests (1 unit —
  `test_create_transaction_raises_when_buyer_email_not_verified`; 1 API —
  `test_create_transaction_returns_403_for_an_unverified_buyer`), plus
  the 4 existing test files above updated so their buyers are verified
  where a purchase must actually succeed. Full backend suite run
  (touches a shared `ErrorCode` enum and `transactions/application`'s
  own `__init__.py` exports — cross-cutting enough to warrant it):
  **574 passed, 0 failed** (double-checked via `--collect-only`), up
  from 572 after Stage 2.

  Live-verified against the real Docker stack, through the actual
  user-facing flow rather than a DB shortcut: registered a buyer,
  attempted `POST /transactions` before verifying — `403
  EMAIL_NOT_VERIFIED`; fetched the real verification email from Mailhog
  (`GET /api/v2/messages`), confirmed via `POST
  /auth/verify-email/confirm` with the real code from that email, then
  retried the same purchase with the same already-issued token — `201
  Created`. `docker compose down` after.
- **Stage 4 — Frontend session/cache reset across account switches —
  DONE**: built exactly per the plan — `AuthContext.tsx`'s `AuthProvider`
  now calls `useQueryClient()` (resolved from React context, not the
  `@/lib/queryClient` singleton import directly — the same client every
  `useQuery` elsewhere in the tree actually reads, and the only way this
  is exercisable in tests, which each construct their own local
  `QueryClient`) and calls `.clear()` in `login`, `register`, and
  `logout`, right where each already mutates the token store.

  Fixing `AuthContext.test.tsx` for this surfaced a real gap in the test
  itself: its `wrapper` rendered `<AuthProvider>` with no
  `QueryClientProvider` around it at all — harmless before, since nothing
  in `AuthContext` touched React Query, but `useQueryClient()` throws
  without one. Fixed by wrapping `wrapper` in a `QueryClientProvider`,
  matching every other test file in this codebase that renders
  `AuthProvider`.

  Exit criteria met: 3 new tests in `AuthContext.test.tsx` (login clears
  a previous session's cached data before the new session's own queries
  populate it; logout clears whatever the just-ended session cached;
  register clears cached guest-mode data) — each seeds
  `queryClient.setQueryData(...)` directly and asserts
  `queryClient.getQueryData(...)` is `undefined` afterward, rather than
  only inferring it from UI state. Full frontend suite run (a change to
  `AuthProvider` is as cross-cutting as this codebase gets — every
  authenticated screen sits under it): **139 passed** across 21 files,
  up from 136 after Stage 3 (this etap added no frontend tests until
  now). `npx tsc -b`, `npm run build`, and `oxlint` all clean (only
  pre-existing warnings).

  Live-verified against the real Docker stack in the browser — the exact
  scenario the user originally reported: registered account A, filled in
  and saved a nutrition profile (age 31, height 180cm, weight 77kg,
  confirmed "Zapisano ✓"), logged out via the profile modal's own
  "Wyloguj się", registered a brand-new account B, and reopened the
  profile modal — showed "Zalogowano jako cachecheck-b@example.com" with
  a completely empty profile form ("Nie masz jeszcze profilu
  żywieniowego", blank Wiek/Wzrost/Waga fields) — no trace of account
  A's 31/180/77 anywhere. `docker compose down` after.
- **Stage 5 — Tests + docs sync — DONE**: closing stage for this etap.

  Docs sync: **`docs/api.md`** — new note on the Authentication API
  section's own intro (per-action Redis rate limiting, mock-by-default);
  `429 RATE_LIMITED` added to the error list on `/auth/register`,
  `/auth/login`, `/auth/password-reset/request`; `POST /transactions`'s
  description and error list gained `403 EMAIL_NOT_VERIFIED` (and the
  previously-undocumented `403 INACTIVE_USER`, found missing while
  writing this). **`docs/architecture.md`** — new `### Rate Limiting
  (Phase 13)` subsection under the Identity Module (the `RateLimiter`
  port/mock/real split, the Redis singleton, the `rate_limited(action)`
  dependency factory); Transactions Module gained a paragraph on the new
  `EmailNotVerifiedError` check; fixed a real stale claim found while
  writing this — `emailVerified` was documented as "tracked but never
  enforced," no longer true since this etap; Future Extensions' "Redis
  cache" / "message broker" bullets updated — Redis and Kafka are both
  real now, scoped narrowly (rate limiting only; general caching still
  deliberately deferred). **`docs/domain-model.md`** — mirrored the same
  `emailVerified` correction and Transaction rule update; Future
  Extensions' Phase-12 note repointed at the correct archived-roadmap
  filename (was still pointing at the live roadmap doc, stale since this
  document replaced it), and gained a new Phase 13 progress paragraph
  (Etap 0 done, Etaps 1-4 not started). **`README.md`** — two real gaps
  found while checking it: the Docker services table said "nine
  containers" and never listed `redis` at all (added, count corrected to
  ten), and the Infrastructure section's "Future: Redis" was stale for
  the same reason `architecture.md`'s was; Phase table gained a new
  Phase 13 row (in progress). **`docs/openapi.json`** — regenerated,
  confirmed no diff (the new error responses are raised, not declared
  via FastAPI's `responses=`, so they don't change the generated
  schema — expected, not a bug).

  Also found and fixed, while writing this stage: two consecutive,
  duplicate "Stage 5 — Tests + docs sync" placeholder bullets had been
  left in this very file from the original prospective breakdown —
  collapsed into the one real entry above.

  Exit criteria met — closing-gate full suites: backend **574 passed, 0
  failed** (unchanged since Stage 3 — Stage 4 was frontend-only).
  Frontend: **139 passed** across 21 files (unchanged since Stage 4).
  `npx tsc -b`, `npm run build`, and `oxlint` all clean.

---

### Etap 1 — User Display Names — DONE

Goal: everyone can set their own display name; dietitians additionally
have the option to display their real first + last name instead.
Validated, and shown everywhere email/UUID currently leaks through.

- **Stage 1 — `display_name` domain field + dietitian
  `first_name`/`last_name` — DONE**: a genuinely new architectural
  precedent for this codebase, per `docs/architecture.md`'s own "Shared
  Kernel" rule (a module may depend on `shared/`, `shared/` never
  depends on a module) — `backend/shared/validation/human_name.py` is a
  **pure, dependency-free** function, `is_valid_human_name(value) ->
  bool` (letters incl. Polish diacritics + digits, single spaces between
  "words," no leading/trailing/double spaces, max 50 chars); it raises
  nothing itself, so it can live in the Shared Kernel without creating a
  shared-depends-on-module dependency, exactly like `PasswordPolicy`
  *couldn't* (it raises identity's own `InvalidPasswordError` directly,
  so it stays in identity).

  Each module calls the shared function but raises its **own** domain
  exception, matching each module's own pre-existing convention rather
  than inventing a new shared one: identity gets a new `DisplayName`
  value object (`domain/value_objects/display_name.py`, frozen dataclass,
  identical shape to `Email` — strip, validate, `object.__setattr__`),
  raising a new `InvalidDisplayNameError`; `User` gains a nullable
  `display_name: DisplayName | None` field and a `set_display_name()`
  mutator (no domain event — matches `deactivate()`/`block()`/`activate()`'s
  precedent for a state change nothing else needs to react to, not
  `change_password()`/`change_role()`'s). Dietitian keeps its own
  pre-existing convention too — `experience`/`description` are plain
  `str`, not value-object-wrapped — so `first_name`/`last_name` on
  `DietitianProfile` are plain `str | None`, validated inline in the
  entity's existing `_validate()` (only when not `None`, since both are
  optional), raising the existing `InvalidDietitianProfileError`. Both
  entities' migrations, models, and mappers updated
  (`20260722_13_display_names.py`; `users.display_name`,
  `dietitian_profiles.first_name`/`last_name`, all nullable
  `String(50)`).

  Exit criteria met: 31 new tests — `backend/tests/test_human_name_validator.py`
  (the shared function's own accept/reject cases, incl. SQL-injection
  and script-tag strings, both rejected by the character-class alone,
  confirming no separate "SQL injection defense" mechanism was needed
  beyond the same character-set rule); `User.set_display_name()` +
  `DisplayName` VO tests in `test_user_entity.py`;
  `DietitianProfile` `first_name`/`last_name` tests (via both `create()`
  and `update_details()`) in `test_dietitian_profile_entity.py`. Full
  backend suite run (a new Shared Kernel package plus changes to two
  widely-used entities is exactly the "shared/cross-cutting" case this
  project's own test-scope rule calls for a full run on): **605 passed,
  0 failed** (double-checked via `--collect-only`), up from 574 at the
  end of Etap 0 — confirming the new migration applies cleanly (the
  same session-scoped Postgres test fixture every other module's tests
  already depend on runs `alembic upgrade head` before any test in the
  suite executes).
- **Stage 2 — Propagate into read models — DONE**: `User.resolved_display_name`
  (a new property: `display_name` if set, else `email`) is the two-step
  fallback every user gets. A new `resolve_dietitian_name(profile, user)`
  function (`backend/modules/dietitian/application/services/`) adds the
  higher-priority third step — a dietitian's real `first_name +
  last_name`, only when *both* are set — and is genuinely shared, not
  duplicated: `messaging`'s `ListMyDietitianThreadsUseCase` imports it
  directly from `dietitian` (the same "reuse the other module's
  already-exported unit directly" pattern this project has used since
  Etap 5), rather than reimplementing the three-step chain a second
  time.

  Applied everywhere: **messaging** — `DietitianThreadResult`/
  `DietitianThreadResponse`'s `other_participant_email` field renamed to
  `other_participant_name` (it can now hold a name, not just an email —
  keeping the old name would've been misleading); `ListMyDietitianThreadsUseCase`
  now takes a `DietitianProfileRepository` too, and branches on
  `other_id == thread.dietitian_id` (the thread entity already records
  which side is which — no extra role check needed) to decide whether
  the three-step or two-step chain applies. **Marketplace** —
  `DietitianListingItemResult`/`PublicDietitianProfileResult`'s `email`
  field renamed to `name`, resolved via `resolve_dietitian_name`.
  **Reviews** — the real target of the user's own "reviews are
  anonymous" complaint turned out to be `PublicReviewResult` (the
  marketplace-embedded reviews list), which a Phase 12 comment
  explicitly said "deliberately omits the reviewer's identity" — now
  reversed: both `PublicReviewResult`/`PublicReviewResponse` (public
  profile) and `ReviewResult`/`ReviewResponse` (the submit-review
  response) gained a `reviewer_name` field (plain two-step resolution —
  a reviewer is never given dietitian-priority treatment even if they
  happen to also hold `DIET_USER` elsewhere; reviewing isn't a
  dietitian-professional context). `reviewer_id`'s `ON DELETE CASCADE`
  FK means a review can never outlive its reviewer, so the new lookup in
  `GetPublicDietitianProfileUseCase`/`SubmitReviewUseCase` never needs a
  None-guard.

  Fixing the existing test suite for these renames touched 7 files
  across `messaging`/`dietitian` (constructor signatures, renamed
  fields, and two use-case tests whose fake `reviewer_id`/`buyer_id`
  values had never actually been registered as real users in the fake
  repo — harmless before this stage, since nothing resolved them; now
  required, since resolution needs a real `User` to look up). Added a
  dedicated `test_resolve_dietitian_name.py` for the shared three-step
  chain's own accept/reject priority order, plus targeted tests in each
  consuming use case confirming the fallback is actually reached
  end-to-end, not just correct in isolation.

  Exit criteria met: full backend suite **601 passed, 0 failed**
  (verified via `--collect-only`) — 9 new tests this stage:
  `test_resolve_dietitian_name.py` (4), `User.resolved_display_name`
  coverage in `test_user_entity.py` (2), `ListMyDietitianThreadsUseCase`
  priority-order coverage (2 net new after consolidating the renamed
  originals), `ListDietitiansUseCase` real-name coverage (1). Run in
  full since this stage touches the shared `User` entity and a new
  cross-module dependency direction (messaging → dietitian).

  Live-verified against the real Docker stack: registered a buyer and a
  dietitian, set the dietitian's `first_name`/`last_name` and the
  buyer's `display_name` directly via SQL (no write endpoint exists for
  either yet — that's Stage 3's own job), then confirmed via `curl`:
  `GET /dietitian` (marketplace listing) returns `"name": "Jan
  Kowalski"` for the dietitian; after the buyer submitted a review,
  `GET /dietitian/{id}`'s embedded review shows `"reviewer_name":
  "BuyerNick"` (no longer anonymous); `GET /messaging/threads` called by
  each side of a real thread shows the *other* side's correctly
  resolved name — the dietitian's real name from the buyer's call, the
  buyer's `display_name` from the dietitian's call. `docker compose
  down` after.
Design decisions settled right before building Stage 3 (a real backend
gap Stage 2 didn't cover — it only touched read models):

- **A new `PATCH /auth/me` endpoint** lets any user set/clear their own
  `display_name` — no such self-service endpoint existed at all before
  now (only registration/login/password-reset touch `User`). Request:
  `{ display_name: string | null }`; response: the same `MeResponse`
  shape `GET /auth/me` already returns, now including `display_name`.
- **`PUT /dietitian/profile` gains optional `first_name`/`last_name`** —
  `UpdateDietitianProfileCommand`/`DietitianProfile.update_details()`
  already supported them since Stage 1; this stage only wires the
  request/response schemas through, same optional-field shape as the
  existing `experience`/`diplomas`/`description`.
- **Frontend field renames match Stage 2's backend renames exactly** —
  `other_participant_email` → `other_participant_name` (messaging),
  `email` → `name` (dietitian listing/public profile) — updated in one
  pass across API client types and every component reading them, not
  left mismatched until something broke at runtime.

- [x] **Stage 3 — Frontend: set/edit + display everywhere — DONE**: a
      `display_name` field in the profile UI for every account; an
      additional, clearly-optional first-name/last-name field pair in
      the dietitian profile editor. Every place in the UI currently
      showing an email or UUID (chat bubbles, messaging thread cards,
      review cards, marketplace dietitian cards) switches to showing the
      resolved name.

  New backend surfaces: `PATCH /auth/me` (`UpdateMeRequest` /
  `UpdateDisplayNameUseCase`, `ErrorCode.INVALID_DISPLAY_NAME` on
  invalid input) and `PUT /dietitian/profile` extended with optional
  `first_name`/`last_name` (domain support already existed since
  Stage 1 — this stage only wired the request/response schemas
  through). Frontend: `updateMe()` in `api/auth.ts`,
  `MeResponse.display_name`; `DietitianProfile.first_name/last_name` +
  `UpdateDietitianProfileRequest` in `api/dietitian.ts`; field renames
  matching Stage 2's backend renames (`other_participant_email` →
  `other_participant_name`, `email` → `name`, `PublicReview` gains
  `reviewer_name`) applied across `RightRail.tsx`,
  `DietitianProfileModal.tsx`, `HumanChatCanvas.tsx`. New UI: a
  "Nazwa wyświetlana" field + save action in `ProfilTab.tsx`; optional
  imię/nazwisko inputs in `DietitianProfileTab.tsx`'s own form.

  **Bug found and fixed while wiring the real write path**:
  `SqlAlchemyUserRepository.save()`'s update branch (the one taken
  whenever a row already exists) manually copied individual fields from
  the domain entity onto the tracked SQLAlchemy row instead of using
  the mapper, and that field list had silently gone stale — it never
  included `display_name` at all. `UpdateDisplayNameUseCase` always
  hits this exact branch (it loads an existing user via `get_by_id`,
  mutates, then saves), so every `PATCH /auth/me` call was appearing to
  succeed (the response serializes the in-memory mutated entity) while
  the database row's `display_name` silently stayed `NULL` — the very
  next `GET /auth/me` would show it gone. Fixed by adding the missing
  `existing.display_name = ...` line; this class of bug (a manual
  field-copy list quietly drifting from the mapper it duplicates) is
  worth keeping in mind for any future field added to `User`. Caught by
  the new `PATCH /auth/me` test asserting a follow-up `GET` reflects
  the change — exactly the kind of gap unit tests of the use case alone
  (which only assert against the in-memory returned entity) can't see.

  Exit criteria met: automated tests only this stage (per the tightened
  test-scope rule — thorough live-Docker verification deferred to
  Stage 5's closing pass). Full backend suite **609 passed**; full
  frontend suite **138 passed**, including new coverage for
  `PATCH /auth/me` (set/clear/invalid/unauthenticated), the extended
  `PUT /dietitian/profile` (first/last name set + validation, both at
  the use-case and router level), and the new `ProfilTab`/
  `DietitianProfileTab` UI.
- [x] **Stage 4 — Registration form — DONE**: added a "Powtórz hasło"
      confirm-password field to `AuthPopup.tsx`'s register tab —
      client-side match check before submit, no API call on mismatch.
      Decided against a registration-time display-name prompt — Stage 3
      already gave every account a way to set it from the profile
      screen, so prompting again at registration would duplicate that
      without adding anything.
  - Exit criteria met: mismatched passwords block submission with an
    inline "Hasła nie są takie same." error and no `/auth/register`
    call; registration still succeeds end-to-end. `AuthPopup.test.tsx`
    (7 tests) covers login, register success, register conflict, the
    new mismatch case, guest continue, and forgot-password nav.
- [x] **Stage 5 — Tests + docs sync — DONE**: closing stage for this
      etap. Synced `docs/api.md` (new `PATCH /auth/me` section;
      `GET/PATCH /auth/me`'s `display_name`; `PUT /dietitian/profile`'s
      `first_name`/`last_name`; `email` → `name` renames on `GET
      /dietitian` and `GET /dietitian/{id}`; `reviewer_name` on both
      review endpoints; `other_participant_email` → `_name` on `GET
      /messaging/threads`), `docs/domain-model.md` (`User.displayName`,
      `DietitianProfile.firstName`/`lastName`, corrected the Review
      section's now-outdated "omits reviewer identity" claim), and
      `docs/architecture.md` (`shared/validation/` entry for
      `is_valid_human_name()`, corrected the same Review-anonymity
      claim). `README.md` only links to this roadmap for Phase 13, no
      changes needed there.

  Exit criteria met: full suite run at etap close (per the tightened
  test-scope rule — each stage only ran its own directly-affected
  files). Full backend suite **622 passed**, full frontend suite **142
  passed**.

---

### Etap 2 — Chat & Diet Plan UX Polish — DONE

Goal: the rough day-to-day UX edges the user hit while actually using
the app.

- [x] **Stage 1 — Optimistic own-message rendering — DONE**: the
      `sendMessage` mutation in `ChatCanvas.tsx` gained an `onMutate`
      that appends the user's message to the cached conversation with a
      temporary id and clears the composer immediately; `onSuccess`
      reconciles it with the real `user_message_id` and appends the
      assistant's reply; `onError` rolls back to the pre-mutate snapshot
      and restores the typed text into the composer.
  - Exit criteria met: `ChatCanvas.test.tsx`'s in-flight test asserts the
    user's bubble ("Cześć") renders before the AI response resolves,
    with "Mycelo pisze odpowiedź…" following it. 17/17 tests in this
    file pass.
- [x] **Stage 2 — Diet-plan-generation feedback — DONE**: added
      `onSuccess`/`onError` to `generatePlanMutation` in `ChatCanvas.tsx`
      — a success toast ("Plan wygenerowany! Zobacz go poniżej.") and an
      error toast (reusing the existing `generateErrorMessage()`
      code-to-message mapping), matching the toast-only pattern already
      used by the archive/delete mutations in the same file. Replaced
      the old passive `isError`-driven inline `FieldError` banner, which
      duplicated the same information with no toast.
  - Exit criteria met: a forced generation failure now surfaces
    `notifyError(...)` instead of silently doing nothing.
    `ChatCanvas.test.tsx` updated to assert against the mocked
    `notifyError`/`notifyInfo` calls instead of DOM text for these
    cases. 17/17 tests pass.
- [x] **Stage 3 — Rename conversations + diet plans — DONE**:
      `Conversation.rename()`/`RenameConversationUseCase` +
      `PATCH /conversations/{id}` (same shape as `GET`); `DietPlan`
      gained a new optional `name` field (`rename()`, `None` clears back
      to the default goal/diet_type/duration display, same convention
      as `User.display_name`) + `RenameDietPlanUseCase` +
      `PATCH /diet-plans/{id}`. Frontend: hover-reveal pencil icon
      toggles an inline `<Input>` in both `LeftRail.tsx`'s conversation
      list and `PlanyTab.tsx`'s plan list, committing on Enter/blur,
      cancelling on Escape; `PlanyTab` shows `plan.name` when set,
      falling back to the existing composed label otherwise.
  - Exit criteria met: renamed titles persist across a refetch
    (asserted directly against the API responses in both new frontend
    tests, and via a follow-up `GET` in both new backend API tests) for
    both entity types. Full suites run since this touched shared DTOs on
    two backend modules and API types used by multiple components:
    backend 637 passed, frontend 145 passed.
- [x] **Stage 4 — Copy + layout fixes — DONE**: empty-state copy in the
      left rail changed to "Jeszcze z nami nie pogadałeś :(". Root cause
      of the page-level scrollbar: four `flex-1 overflow-y-auto`
      scroll containers (`LeftRail.tsx`, `RightRail.tsx`,
      `ChatCanvas.tsx`, `HumanChatCanvas.tsx`) were missing `min-h-0` —
      a flex item's default `min-height: auto` lets it grow past its
      allotted space along the flex-column main axis instead of
      clipping, so overflow escaped to the page instead of scrolling
      internally. `DietitianProfileModal.tsx` already used the correct
      `min-h-0 flex-1` pattern; applied it to the other four. Also added
      `overflow-hidden` to `AppShell.tsx`'s root container as a second
      line of defense.
  - Exit criteria met: live-verified in a real browser against a fresh
    Docker backend (registered a user through the actual UI, not just a
    raw API call) — `document.documentElement.scrollHeight ===
    clientHeight` confirmed no page-level scrollbar with a populated
    dietitian list and empty conversation history both on screen; the
    new empty-state copy rendered exactly as specified. Docker stack
    torn down after. Affected component tests (48) + full frontend
    suite pass.

  **Follow-up found during this same live check**: collapsing the right
  rail hid the Mycelo mushroom icon entirely whenever there were zero
  unread notifications — `MyceloNotificationBadge` returned `null` in
  that case instead of showing the idle-colored icon, so it only ever
  worked as a pure unread-alert, not as the persistent way to reopen a
  collapsed panel. Fixed to always render (alert coloring/count pill
  layered on only when `unreadCount > 0`), matching `RightRail.tsx`'s
  own always-visible `NotificationsBell` trigger — and dropped
  `MyceloNotificationBadge`'s border/background classes to match that
  same borderless style. Kept both auth-gated (`isAuthenticated &&`), so
  a guest sees neither the collapsed-panel badge nor the expanded-panel
  bell — only a logged-in user sees the mushroom in both places.
  Live-verified in the browser for both auth states × both panel
  states; `ChatCanvas.test.tsx` and `RightRail.test.tsx` updated/added
  accordingly. Full frontend suite: 148 passed.
- [x] **Stage 5 — Tests + docs sync — DONE**: closing stage for this
      etap. Synced `docs/api.md` (new `PATCH /conversations/{id}` and
      `PATCH /diet-plans/{diet_plan_id}` sections; `name` field added to
      every diet-plan response shape), `docs/domain-model.md`
      (`Conversation.rename()`/`DietPlan.name`+`rename()` rules), and
      `docs/architecture.md` (Conversation Module's responsibility list
      and the "one mutation `DietPlan` ever undergoes" note, now two).
      `README.md` needed no changes (it only links to this roadmap for
      Phase 13).

  Exit criteria met: full suite run at etap close (per the tightened
  test-scope rule — each stage only ran its own directly-affected files
  or a full run when the change was cross-cutting). Full backend suite
  **637 passed**, full frontend suite **148 passed**, clean
  `tsc --noEmit`.

  A guest-visibility question came up mid-etap during Stage 4's
  follow-up work (whether the dietitian marketplace should stay visible
  to a logged-out user) — verified live that it already does
  (`RightRail.tsx`'s `dietitiansQuery` was never auth-gated, and
  `DietitianProfileModal.tsx`'s offer buttons already disable with
  "Zaloguj się, aby się zgłosić" for a guest); no code change needed.

---

### Etap 3 — Multi-Plan Calendar

Goal: let a user view several of their own non-overlapping generated
plans together on one continuous calendar, freely move meals between
days, and export the combined selection directly from that view.

- [x] **Stage 1 — Full day+time meal rescheduling — DONE**:
      `DietPlan.reschedule_meal()` gained an optional `new_day_number` —
      when given and different from `day_number`, it removes the meal
      from its source `DietDay` and appends it (with the new time) to
      the target `DietDay`; an unknown target day still raises
      `MealNotFoundError` → 400, same as an unknown source day/meal
      already did. `RescheduleMealCommand`/`RescheduleMealRequest`/
      `PATCH /diet-plans/{id}/meals` plumbed the new optional field
      through end to end. `KalendarzTab.tsx`'s drag-and-drop now sends
      `new_day_number` whenever the dropped-on cell's day differs from
      the dragged meal's origin day (omitted for a same-day retime, so
      the request body is unchanged from before in that case); a drop
      onto a date the plan doesn't cover at all (`HoverCell.dayNumber
      === null`) is rejected client-side and styled as an invalid
      target, never reaching the API.
  - Exit criteria met via automated coverage: domain-level tests for
    same-day retime (unchanged), cross-day move, and unknown-target-day
    rejection (plan left untouched); use-case- and API-level tests for
    the same; a `KalendarzTab.test.tsx` test simulates the exact
    pointer-drag-to-a-different-day-column interaction end to end and
    asserts both the PATCH payload and the resulting UI (meal chip
    reappearing under the new day). Live-browser verification was
    skipped this stage — the host machine's disk was down to 5.7 GB
    free (unrelated to this repo; `docker builder prune`/`image prune`
    reclaimed 0B, so it's outside Docker's own cache) and Postgres
    couldn't start; deferred rather than chasing an unrelated
    system-level issue. Full suites: backend 643 passed, frontend 149
    passed, clean `tsc --noEmit`.
- [x] **Stage 2 — Multi-select plan picker — DONE**: replaced
      `KalendarzTab`'s single Radix `<Select>` with a custom checklist
      popover (same toggle-panel pattern as `CategoryMenu.tsx`'s
      category picker) — `selectedPlanIds: string[]`, defaulting to the
      newest plan when nothing's been explicitly toggled yet (mirrors
      the old single-select's "no separate auto-select effect" comment).
      `planDateRange()`/`rangesOverlap()` compute each plan's inclusive
      `[start, end]` from `created_at` + `duration_days` and check
      intersection before allowing a new selection; a blocked attempt
      shows an inline `FieldError` naming both conflicting plans and
      leaves the checkbox unchecked. Deselecting the last remaining
      plan is a no-op (at least one always stays selected). The
      calendar grid itself still renders only the first selected plan —
      Stage 3 wires up the actual multi-plan merge.
  - Exit criteria met: `KalendarzTab.test.tsx` gained 3 tests —
    selecting a second non-overlapping plan, blocking an overlapping
    one with the error message, and rejecting deselection down to zero.
    Full frontend suite: 152 passed, clean `tsc --noEmit`. Frontend-only
    change, so no backend run needed this stage.
- [x] **Stage 3 — Combined week-by-week navigation — DONE**: replaced
      the single `planQuery` with one `useQueries` call across every
      selected plan id; their days merge into one
      `Map<dateKey, {planId, day}>` (non-overlapping selection means at
      most one plan ever claims a given date). Combined `totalWeeks`
      spans from the earliest selected plan's first Monday through
      whichever is later of its own last week or a full 52-week year —
      per a mid-stage clarification, the calendar should be scrollable
      through an entire year even across weeks with no plan data at
      all, while a plan itself is only ever generated for the days it
      actually covers (no fabricated empty days). Diet type(s) in the
      header and "Uwzględnione wskazówki" now dedupe across every
      loaded plan instead of reading a single plan's own fields.
      Dragging gained a `planId` on both the dragged meal and the hover
      target — a drop is only valid within the *same* plan; a foreign
      plan's cell is rejected exactly like a date no plan covers at all
      (same invalid-target styling). Bug caught while writing this
      stage's own tests: two different plans' days can both be "day 1"
      and land in the *same* visible week near a plan boundary, so
      `cell-day1-…`/`meal-day1-…` testids could collide; fixed by
      disambiguating with the owning plan id, but **only** once 2+
      plans are actually loaded together, so every existing single-plan
      test's testids are completely unchanged.
  - Exit criteria met: new tests assert each selected plan's meals show
    correctly in their own week with nothing missing or duplicated,
    and a cross-plan drop is rejected with no PATCH sent. Full frontend
    suite: 155 passed, clean `tsc --noEmit`. Frontend-only change, no
    backend run needed this stage.
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
