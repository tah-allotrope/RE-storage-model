---
title: "Web GAP-04: Production Deploy, Persistence, and Access Control"
date: "2026-06-13"
status: "draft"
request: "Create a multi-phase plan for GAP-04 (deploy + persistence + auth) from reports/2026-06-13-reopt-web-interface-gap-analysis.md"
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-06-13-reopt-web-interface-gap-analysis.md"
---

# Plan: Web GAP-04: Production Deploy, Persistence, and Access Control

## Objective
Turn the locally-runnable web tool into a reachable, durable application. Today the app has never been deployed (`.firebaserc` still points at the placeholder `re-storage-tool`), keeps no state (results vanish on refresh), and is unauthenticated. This plan delivers a first production deploy, run persistence with shareable links, and basic access control — the infrastructure every other web gap depends on for real-world testing.

## Context Snapshot
- **Current state:** [firebase.json](../firebase.json) configures hosting + 4 Python functions with a `prepare_firebase_functions.py` predeploy hook; [.firebaserc](../.firebaserc) default is the placeholder `re-storage-tool`. No Firestore/Storage/Auth. Built [web/frontend/dist/](../web/frontend/dist) is committed and may be stale. Deploy checklist exists in [README.md](../README.md) §123.
- **Desired state:** A real Firebase project is provisioned and deployed; each run's inputs+KPIs are stored in Firestore and reloadable via a `/runs/<id>` share route; the app is protected by Firebase Auth or App Check with a `maxInstances` cap; the frontend build is produced by CI (or `dist/` is untracked) so deploys never ship stale UI.
- **Key repo surfaces:** `firebase.json`, `.firebaserc`, `scripts/prepare_firebase_functions.py`, `web/functions/main.py` (+ handlers), `web/frontend` (Vite build), `web/frontend/src/hooks/useModelRun.ts`, `web/frontend/src/api/client.ts`.
- **Out of scope:** Verdicts (GAP-01), export (GAP-02), tariff mode (GAP-03), multi-user collaboration, billing dashboards.

## Research Inputs
- [reports/2026-06-13-reopt-web-interface-gap-analysis.md](../reports/2026-06-13-reopt-web-interface-gap-analysis.md) — GAP-04 (HIGH) + GAP-09 (stale `dist/`, no web CI) + Risks (cold start, placeholder project, public abuse). Sequencing: deploy (4a) is the smallest HIGH and unblocks testing everything else.
- [plans/web-tool-implementation-plan.md](../plans/web-tool-implementation-plan.md) §5, §8, §9 — Firebase setup, deploy instructions, and Risks R1/R10 (cold start `minInstances:1`; no-auth abuse mitigation).

## Assumptions and Constraints
- **CON-001:** A first production deploy requires a Google Cloud project with billing enabled — a human action the agent cannot perform; the plan provides the exact commands but flags this as a gating manual step.
- **DEC-001:** Persistence uses Firestore (native mode) for run records and Firebase Storage only if Excel/CSV audit trails are wanted; MVP stores inputs + KPI JSON, not raw uploads.
- **DEC-002:** Re-using the existing rewrite-based same-origin `/api/*` routing avoids CORS in production (plan Risk R9); `flask-cors` stays for local dev.
- **ASM-001:** Audience is internal/limited for first launch, so App Check (or a single shared Auth) is sufficient; full multi-tenant auth is deferred.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | First production deploy + build hygiene | None | Live URL; real `.firebaserc`; CI/predeploy build of `dist/` |
| PHASE-02 | Firestore run persistence + share links | PHASE-01 | `runs` collection; `/runs/<id>` reload route |
| PHASE-03 | Access control + abuse limits | PHASE-01 | App Check/Auth; `maxInstances`; `minInstances:1` warm |

## Detailed Phases

### PHASE-01 - First production deploy and build hygiene
**Goal**
The app is reachable at a Firebase Hosting URL with functions serving `/api/*`, and deploys always ship a fresh frontend build.

**Tasks**
- [ ] TASK-01-01: Provision a real Firebase project (billing enabled); record its ID. Replace the placeholder in [.firebaserc](../.firebaserc) (`firebase use <real-id>`). **[manual gating step]**
- [ ] TASK-01-02: Run the documented checklist (README §123): `python scripts/prepare_firebase_functions.py`; `pytest tests/unit/test_web_handlers.py -v`; `cd web/frontend && npm run build`; `firebase deploy --only functions,hosting`.
- [ ] TASK-01-03: Fix build hygiene (GAP-09): either stop tracking `web/frontend/dist/` (add to `.gitignore`) and add a hosting predeploy hook that runs `npm run build`, or add a CI job that builds and deploys. Prevents stale-UI deploys.
- [ ] TASK-01-04: Smoke-test the deployed `/api/run-json` and `/api/run-excel` against the Emivest and Ecoplexus fixtures; confirm KPIs match references.
- [ ] TASK-01-05: Confirm function `runtime: python311`, `availableMemoryMb` (raise to 2048 per plan §5 if 1024 is tight), `timeoutSeconds: 300`.

**Files / Surfaces**
- `.firebaserc`, `firebase.json`, `.gitignore`, `scripts/prepare_firebase_functions.py`, `web/frontend/dist/` (untrack), CI config (new, if chosen).

**Dependencies**
- None (other than the manual project-provisioning gate).

**Exit Criteria**
- [ ] Public Hosting URL serves the SPA and a structured-form run returns KPIs from the deployed function.
- [ ] A clean `git` tree no longer tracks `dist/`, or CI rebuilds it on deploy.

**Phase Risks**
- **RISK-01-01:** Cold start 3–10s (Python+pandas+scipy) — set `minInstances: 1` (plan R1) or set expectations via existing progress copy.
- **RISK-01-02:** Predeploy vendoring (`prepare_firebase_functions.py`) must run in the deploy environment; verify the hook fires and the `re_storage` package is bundled.

### PHASE-02 - Firestore run persistence and share links
**Goal**
Each run is saved and reloadable via a stable URL.

**Tasks**
- [ ] TASK-02-01: Enable Firestore; add minimal security rules (read by run id, writes only from functions).
- [ ] TASK-02-02: In the run handlers, after a successful run, write `{id, created_at, inputs(payload), kpis, verdict?}` to a `runs` collection and return the `run_id` in the response.
- [ ] TASK-02-03: Add a `GET /api/runs/<id>` function returning the stored record; register in `main.py` and `firebase.json`.
- [ ] TASK-02-04: Frontend: on run success, store `run_id`; add a "Copy share link" action and a `/runs/:id` route in the SPA that fetches and renders a past run read-only.
- [ ] TASK-02-05: Decide storage of the 8,760-row CSV — store a Storage object reference (optional) or require re-upload for re-runs; MVP stores inputs+KPIs only.

**Files / Surfaces**
- `firebase.json` (Firestore rules path), `firestore.rules` (new), `web/functions/handlers/*` (write on success), `web/functions/handlers/get_run.py` (new), `web/frontend/src/api/client.ts`, `web/frontend/src/hooks/useModelRun.ts`, SPA routing.

**Dependencies**
- PHASE-01.

**Exit Criteria**
- [ ] Running a project returns a `run_id`; visiting `/runs/<id>` reloads the same KPIs/charts.
- [ ] Firestore rules deny client writes; functions can write.

**Phase Risks**
- **RISK-02-01:** Firestore document size limit (1 MB) — store KPIs + inputs, never the full hourly series; keep timeseries in Storage if needed.
- **RISK-02-02:** Sharing inputs may expose commercially sensitive assumptions — gate share links behind the access control from PHASE-03.

### PHASE-03 - Access control and abuse limits
**Goal**
The deployed app is protected against anonymous abuse and cost runaway.

**Tasks**
- [ ] TASK-03-01: Add Firebase App Check (reCAPTCHA) to the functions, or Firebase Auth (Google sign-in) if per-user runs are wanted; enforce in handlers.
- [ ] TASK-03-02: Set `maxInstances` (e.g. 10) and `minInstances: 1` in `firebase.json`/function config (cap cost, kill cold starts).
- [ ] TASK-03-03: Add request-size guards on uploads (reject CSV/Excel over a threshold) reusing/extending [web/functions/utils/validate.py](../web/functions/utils/validate.py).
- [ ] TASK-03-04: Document the access posture and rotation in README.

**Files / Surfaces**
- `firebase.json`, `web/functions/main.py`, `web/functions/utils/validate.py`, `web/frontend` (App Check/Auth init), `README.md`.

**Dependencies**
- PHASE-01.

**Exit Criteria**
- [ ] Unauthenticated/unverified requests to `/api/*` are rejected (or rate-limited) in production.
- [ ] `maxInstances` cap is active; a warm instance eliminates first-call cold start.

**Phase Risks**
- **RISK-03-01:** Auth friction for internal users — App Check is lower-friction than full Auth; choose per audience (see Grill Me).

## Verification Strategy
- **TEST-001:** `pytest tests/unit/test_web_handlers.py -v` plus a new test that a successful run writes a `runs` record (mock Firestore).
- **MANUAL-001:** Deploy to a preview channel (`firebase hosting:channel:deploy preview`); run the Emivest fixture; copy the share link in a fresh browser and confirm read-only reload.
- **OBS-001:** Cloud Console — verify function memory/timeout, cold-start counts after `minInstances:1`, and Firestore write success rate.

## Risks and Alternatives
- **RISK-001:** Billing/quota surprises on a public deploy — mitigate with `maxInstances`, App Check, and upload-size guards before any non-internal launch.
- **RISK-002:** Stale committed `dist/` ships old UI — resolved in PHASE-01 TASK-01-03.
- **ALT-001:** Skip Firestore; encode the entire run state in the share URL (query string). Rejected: 8,760-row inputs and many params exceed practical URL limits.

## Grill Me
1. **Q-001:** Who is the audience for the first deploy — internal-only, named external clients, or fully public?
   - **Recommended default:** Internal/limited — App Check + `maxInstances` cap, defer full Auth.
   - **Why this matters:** Sets PHASE-03 (App Check vs Auth) and whether share links need per-user gating.
   - **If answered differently:** Public → add Firebase Auth, stricter rate limiting (Cloud Armor), and a privacy review of stored inputs.
2. **Q-002:** Should raw uploaded Excel/CSV be persisted (audit trail) or only inputs+KPIs?
   - **Recommended default:** Inputs + KPIs only (Firestore); no raw file storage for MVP.
   - **Why this matters:** Determines whether Firebase Storage is provisioned in PHASE-02 and re-run UX.
   - **If answered differently:** Add Storage bucket + lifecycle rules and store object references on each run.

## Suggested Next Step
Answer Q-001/Q-002, complete the manual Firebase project provisioning, then execute PHASE-01 — it is the smallest HIGH gap and unblocks live testing of GAP-01/02/03.
