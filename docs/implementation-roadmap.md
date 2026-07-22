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

- [ ] **Stage 1 — JWT secret hardening**: replace the under-32-byte
      placeholders in `docker-compose.yml` and `.env.example` with a
      properly generated 32+ byte secret (documented as a placeholder
      to rotate in any real deployment, same spirit as every other
      "change-me" dev default in this codebase); add a `Settings`-level
      startup check that raises (or at minimum logs a clear warning) if
      `jwt_secret_key` is under 32 bytes when `app_env != "dev"`.
  - Exit criteria: `docker compose up` no longer produces
    `InsecureKeyLengthWarning`; a short key outside dev mode fails fast
    with a clear error instead of a buried library warning.
- [ ] **Stage 2 — Redis-backed auth rate limiting**: new `redis`
      service (`docker-compose.yml` + `docker-compose.test.yml`, same
      ephemeral-test-stack pattern as Postgres/Mongo/Kafka), a
      `RateLimiter` port + `NoOpRateLimiter` (default, tests never need
      a real Redis) + `RedisRateLimiter`, gated behind
      `rate_limit_provider: mock | redis`; wired into
      `POST /auth/login`, `/auth/register`, `/auth/password-reset/request`.
  - Exit criteria: repeated rapid requests to any of the three
    endpoints get a `429` past a defined threshold when
    `rate_limit_provider=redis`; `pytest` still runs with zero real
    Redis dependency by default.
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
