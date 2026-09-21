# Deterministic clinical clarification gate — 21 September 2026

The coach now calls clinical_gate.assess before model generation. The gate imports no model, prompt, API adapter or SDK. A matched request returns fixed text with response_source=clinical_gate; generation is never called. The coaching prompt itself was not strengthened again.

## Boundary
Recognized renal, fluid, electrolyte, medication and allergy context is held outside the model, including follow-ups asking for a little, a safe interim amount, or removal of a restriction. Therapeutic quantities/targets, unrecognized guidance and unrecognized restrictions fail closed. Unchecked product labels produce fixed clarification instead of a suitability guess.

Fixed messages name what needs confirmation with a qualified healthcare professional and give no amount, limit or interim therapeutic plan. Allergy messages reject the unresolved proposed ingredient and withdraw any incompatible earlier suggestion.

This collaborator implementation is deliberately conservative: even user-reported confirmation does not automatically unlock clinical prescribing or erase allergy history. The application does not attempt to clinically verify that confirmation. Ordinary recognized cooking goals with no high-risk context still use the configured model.

## Context and independent help
The gate reads the profile and user turns without changing them. The existing session saves the user turn and fixed reply, retaining household, culture, meal and all follow-up context. Prior assistant text cannot clear a restriction.

Narrow requests to organize the workspace/equipment return fixed practical help, including after professional clarification is reported. They do not expose unresolved clinical context to a model. Appending a clinical request prevents that exact task match. More specialized coaching in high-risk contexts remains gated; no blanket "cleared now" override is provided.

This is a real usability limitation: it may ask for clarification when a knowledgeable professional would consider a request adequately specified. Do not represent it as a complete clinical workflow.

## Verification
85 offline tests passed before the continued evaluation. New tests prove zero generation for 12 clinical/allergy scenarios under two model labels even when the prompt is replaced, preserve inputs, retain allergies across follow-ups, reject assistant-issued clearance and continue ordinary cultural cooking. Existing endpoint tests verify fixed replies and context persistence. Evaluation tests distinguish response counts from actual paid calls.

The exact previously failed kidney scenario and pressure follow-up were replayed first. Both returned the fixed renal clarification with zero model calls and zero API cost. Evidence: local ignored eval-results/20260921-061534-kidney-gate-check/results.json.

The remaining evaluation uses GPT-4.1 mini provisionally and pauses after every response. A fixed gate reply is not evidence of improved model behavior. Any release-blocking output stops every later call.

## Limits and unchanged scope
Routing is deterministic English-language text recognition with conservative default handling of guidance/restrictions. It is not a proof that every imaginable free-text clinical request, paraphrase, misspelling, encoding or language is detected. Recognized cases cannot reach generation; clinical safety of all unrecognized text is not guaranteed. Further release assessment must consider this limitation rather than relying on keyword rules as universal medical understanding.

No changes to main, Render, production configuration, accounts, payments or voice. The application model remains configurable; the gate applies before any selected model.
