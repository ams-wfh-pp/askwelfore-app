# Targeted guardrail revision — 21 September 2026

Status: development branch only; no deployment or merge. GPT-4.1 mini is provisional for this evaluation only. The application still requires an explicitly configured model.

## Changed
The shared KitchenCoach instructions now make supplied guidance a hard boundary. Conflicting or clinically unclear guidance must go back to the user's qualified healthcare professional; no guessed target, interim compromise, medication adjustment or diagnosis-derived prescription is allowed. Independent cooking help may continue.

Professional approval cannot be invented or extended from a general goal to a new recipe. Explicit user-reported approval of a specific recommendation may only be attributed as such.

The coach preserves familiar meals and exact cultural/household preferences. Known allergens remain excluded across turns; uncertain labels need clarification, and newly incompatible earlier suggestions must be withdrawn.

Default responses are 40–100 words, maximum 120, giving 1–3 useful next actions. Full recipes require an explicit request and have a 220-word maximum. The old multi-heading recipe checklist was removed.

These are model instructions, not a guarantee of clinical correctness. Offline tests cannot demonstrate that the live model follows them.

## Evaluation controls
evaluate_guarded.py uses the same KitchenCoach and Responses adapter as the application. It selects GPT-4.1 mini for this run, with a 700-token response budget. No paid judge, retries or model fallback.

There are 11 fictional scenarios and at most 16 responses, including original cases and targeted unclear-renal, diabetes-medication, fabricated-approval and new-allergy checks. Clinical conflict and allergy cases run first.

Each response is saved locally and execution blocks on operator review. The operator must review that exact response, provide nine rubric scores (N/A permitted), notes and a hard-fail decision. Unknown/missing input, a review failure, an API error or an explicit stop prevents every subsequent request. Response hashes prevent stale review input from advancing the run.

The operator must stop for any new clinical guidance, unsafe allergy handling, invented professional endorsement, or material violation of supplied guidance. A stop leaves later cases untested, not passed.

Credentials are entered in a masked local window, held in memory and never included in evidence or shell history. Evidence remains under ignored eval-results; no real household data is used.

## Verification
55 offline tests passed before opening the authorized paid evaluation. They cover existing application boundaries and the new review gate. No production configuration, voice integration, billing purchase, main branch or Render deployment changed.

Official prompting guidance consulted: https://developers.openai.com/api/docs/guides/latest-model?model=gpt-4.1
Specific instructions and examples were revised against observed failures; actual evaluation, not model reputation, determines the next decision.

Live results will be reported separately, including every failure and every untested scenario.
