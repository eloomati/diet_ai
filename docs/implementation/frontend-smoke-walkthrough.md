# Frontend smoke walkthrough

Same spirit as `docs/https/*.http` — a numbered, repeatable manual
script with an expected outcome per step — but UI-driven, since there's
no REST-client equivalent for browser interactions. Run this against the
real Docker stack (`docker compose up -d db mongo mailhog ollama backend`
+ `cd frontend && npm run dev`) with a **brand-new account**, not a
long-lived test user — this is meant to catch a real registration-to-
export journey breaking, not just individual features in isolation.

Covers: register → login → complete profile → chat → generate plan →
reschedule → export.

---

### 1) Register

- Open the app while logged out — the login popup should appear
  automatically.
- Switch to the "Zarejestruj się" tab.
- Fill E-mail (a fresh address) and Hasło (8+ chars), let the CAPTCHA
  widget auto-resolve (dev placeholder token when no site key is
  configured), click "Utwórz konto".
- **Expected**: the popup closes, the app shows the chat hero as a
  logged-in user (avatar initials in the left rail).

### 2) Explicit logout → login

Registration auto-logs in — this step exercises the *login form*
itself, which register alone doesn't.

- Open Profil (avatar) → "Wyloguj się".
- **Expected**: the login popup reappears (session-aware gating).
- Switch to "Zaloguj się" tab, enter the same credentials, submit.
- **Expected**: popup closes, back to the logged-in chat view.

### 3) Complete the nutrition profile

- Open Profil → Profil tab.
- Fill age/height/weight, pick activity level / goal / diet type,
  submit.
- **Expected**: "Zapisano ✓" appears; reloading the page and reopening
  the tab shows the same values pre-filled (real `PUT /profile`
  round-trip, not just local state).

### 4) Chat

- From the hero, type a message and send it (or click one of the
  chip prompts first to prefill).
- **Expected**: the message appears, "Mycelo pisze odpowiedź…" shows
  while pending, then a real assistant reply renders.

### 5) Generate a diet plan

- Click "Generuj plan" in the composer.
- **Expected**: "Generowanie planu…" while pending, then a
  `DietPlanCard` renders inline with real days/meals/macros.

### 6) Reschedule a meal

- Open Profil → Kalendarz tab, confirm the newly generated plan is
  selected (or pick it from the dropdown).
- Drag a meal chip to a different time within the same day (in
  "Szczegółowy" view).
- **Expected**: a real `PATCH /diet-plans/{id}/meals` fires, the chip
  moves to the new time, and a confirmation message appears.

### 7) Export

- Open Profil → Plany tab, find the same plan, click "Pobierz".
- **Expected**: a real `POST .../export` then `GET .../download` fire,
  and a `.csv` file lands in the browser's downloads with the plan's
  current data (including the reschedule from step 6).

---

## Run log

| Date | Result | Notes |
| --- | --- | --- |
| 2026-07-19 | ✅ all 7 steps passed | Fresh account (`smoketest-etap6@example.com`), real Docker stack. See Etap 6 Stage 2 retrospective in `implementation-roadmap.md` for details. |
