# AskWelFore Phase 1 — review guide

Status: implemented on the development branch, not deployed. Paid AI is disabled.
The interface and offline application tests are ready. Live model quality evaluation
remains pending explicit approval and an API key.

## What changed

- A separate, protected /coach/ text experience with temporary context and follow-ups.
- Culture, household preferences, supplied guidance/source, allergies, available
  ingredients, time, equipment, budget and confidence reach one coaching component.
- Repeat situations, sign-out, access expiry, clear model failures and request limits.
- The same text-in/text-out component can later receive transcribed speech and
  provide text for spoken playback. No voice service or microphone access is added.

The public questionnaire, meal generator, existing templates, GHL, email and Stripe
code are unchanged. main.py only has an opt-in mount for the separate coach app.
No production settings, hosting, billing, or database architecture changed.

## Review locally now — no API key, no paid calls

On this computer, open PowerShell and run:

    Set-Location "C:\Users\ams\.codex\.chatgpt-projects\g-p-68e913d548448191bf0b05850080c938\askwelfore-phase1"
    & .\.venv\Scripts\python.exe -X utf8 preview_coach.py

Keep that window open. It displays a newly generated temporary access code.
Open http://127.0.0.1:8765/coach/ and paste that code.

1. Sign in and enter fictional kitchen context.
2. Enter a cooking question and press "Help me make this work".
3. With AI disconnected, expect a clear "not connected" message, not fabricated advice.
4. Refresh: saved context remains in this session. The unsent question is not saved.
5. Try another situation, sign out, and sign in again.
6. A wrong access code is rejected. Access expires after four hours.
7. Press Ctrl+C in PowerShell to stop the preview and discard all sessions.

This launcher always disables AI even if an API key exists in the environment.
It listens on this computer only, not on a public network. An existing preview
must be stopped before starting another on the same port.

The current public Render URL has NOT gained /coach/. Do not send it to the
collaborator as the new test experience. A remotely accessible test deployment
would need separate approval. No Render preview or production deployment was made.

## Model comparison and action needed

No model is selected. See MODEL_EVALUATION.md for the shared prompt, nine-dimension rubric, seven fictional scenarios and secure test instructions. The six-call pilot checks basic operation; the full comparison uses twenty calls. Offline tests do not establish model quality. An API project/key and available credits are needed for real replies. New prepaid accounts currently require a $5 minimum purchase; no purchase or paid request has been made. Never paste API keys into chat or commit them.

## After model activation is approved

The operator can configure the following for a LOCAL developer test only.
These names are documentation, not active configuration:

- COACH_ENABLED=1
- COACH_ACCESS_CODE: a randomly generated secret of at least 32 characters
- COACH_ORIGIN=http://127.0.0.1:8765
- COACH_LOCAL_HTTP=1 (loopback development only)
- COACH_AI_ENABLED=1 (explicit paid-call opt-in)
- COACH_OPENAI_API_KEY: secret entered securely
- COACH_MODEL: model chosen after evaluation
- COACH_REASONING_EFFORT: low for GPT-5 mini; empty for GPT-4.1 mini
- COACH_MAX_OUTPUT_TOKENS: 2048 for the comparison (default 700)

Then run the existing app locally with one worker:

    python -m uvicorn main:app --host 127.0.0.1 --port 8765 --no-access-log

Do not use preview_coach.py for real model testing; it deliberately stays offline.
No .env loader is installed; variables must actually be present in the process.
For any approved HTTPS test environment, use its exact HTTPS origin and omit
COACH_LOCAL_HTTP. Invalid or incomplete access configuration fails closed.
Do not change production settings or merge this branch without separate approval.

## Tests and honest limits

    python -m pip install -r requirements-coach-dev.txt
    python -m pytest tests -q

Offline tests block external networking and exercise:
- every requested cooking scenario's context and follow-up transmission;
- access rejection, expiry, CSRF/origin checks, cookie protections and session isolation;
- request/body/context/output limits and provider failure;
- repeat situations and sessions, with limits preserved;
- preservation of the public home page and API schema;
- no invocation of CRM, email, payment, or randomized meal-plan paths by the coach.

Offline tests validate mechanics, not the truth, allergy safety, or helpfulness of
generated advice. Before collaborator use, run each scenario in
tests/coach_scenarios.json against the approved model and review against its
expectation. Include injection attempts asking the coach to ignore restrictions,
invent medical targets, or override a clinician. A failed safety case blocks
collaborator release; prompts alone are not a guarantee.

## Privacy and operating limits

Use fictional data for collaborator tests. No persistent household records,
database, browser localStorage, or full prompt/response logging is added.
Opaque session IDs live in HTTP-only, SameSite=Strict cookies. Context stays
in server memory. Sessions expire after four hours, are cleared at expiry/sign-out,
and vanish on restart. Browser refresh retains server context; tab closure alone
does not immediately clear it. No transcript export is provided.

Provider calls use store=false, but that is NOT a promise of zero retention by
the provider. Review the provider's data controls before using real health data:
https://platform.openai.com/docs/guides/your-data

Limits: 40 simultaneous sessions; 10 login attempts/minute across the preview;
two concurrent AI calls; two seconds between requests; 30 attempted calls/session;
100 attempted calls per rolling 24 hours per process; 10 successful turns per
situation; 24,000 bytes of assembled input and a configurable output budget (default 700, maximum 2,048 tokens) per request.
Starting another situation does not reset the session/global call counts.
Old conversation turns are never silently removed to fit a context limit.
After reset, the user must carry forward restrictions newly mentioned in follow-ups.

This is intentionally one process with in-memory state. Multiple workers would
split sessions and budgets. Restart resets the counters. These are bounded test
controls, not a persistent dollar-based billing cap. No new database is proposed.

Existing unpinned dependencies/runtime discrepancies and legacy CRM defects remain
outside scope. The dev requirements record a compatible test setup without altering
production requirements. Before any separately approved deployment, check against
the actual Render runtime and dependency versions.

## Review / rollback

All work is on codex/kitchen-coach-phase1. Do not merge to main or deploy to Render.
COACH_ENABLED is absent/off by default. No links were added to the public quiz.
A future authorized operator can disable the coach mount by removing that flag.
