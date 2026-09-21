# Kitchen-context implementation and offline results

Development branch only. No paid evaluations, merge, deployment or voice work.
Kitchen-context implementation version: kitchen-context-v1.

## Behavior implemented

The existing seven-field form and temporary server sessions remain. No equipment questionnaire or new required field was added.

The session now records materially relevant tools as **available / unavailable / unknown**, plus the outstanding tool question and the original request to resume. Supported tools are a food/meat thermometer, oven, stove/hob, microwave, blender, food processor and specialty cutting tool (including a mandoline).

Clear user declarations and the existing equipment/constraints field supply this record. Earlier user messages are reused; assistant assertions cannot create tool availability. Explicit later user updates can change a tool's status. Questions, uncertainty and statements that a tool is required do not establish ownership.

When a proposed response depends on an unknown tool, the response is withheld and replaced by one concise tool question. Short yes/no answers resolve that question. The coach does not repeat it when the answer is known or while the user remains unsure. An unrelated intervening question cannot accidentally redirect a short “no” to an old equipment question.

Confirmed equipment persists across page reloads and “Try another situation,” within the same temporary session. Reset clears outstanding questions; logout, expiry or server restart clears session data. Equipment is not shared between households. Failed generation does not commit a partial context update.

## Safe adaptation

Both generated advice and fixed food-safety responses consult the tool record before display. Existing food-safety validation still occurs; availability never waives its requirements.

- Unknown thermometer: ask about availability before displaying thermometer-dependent poultry instructions.
- No thermometer: do not display a poultry-cooking method or imply that appearance/time establishes safety. Keep the meal context and support an independent component, such as the rice and familiar seasonings.
- No oven or blender: withhold methods that require it. The model receives the absence and is instructed to use confirmed equipment or a suitable component/texture instead.
- Microwave-only: record that appliance as available and other tracked cooking appliances as unavailable; this does not imply ownership of a thermometer.
- Limited time/no purchase: retain the supplied constraints; withhold explicitly overlong methods and shopping instructions that conflict with an explicit no-purchase constraint.

No automatic regeneration or extra paid retry was added. A model-generated proposal may be needed to identify its tool dependencies, but the unusable proposal is not displayed. Fixed food-safety questions can be handled without a model call.

## Code locations

- `kitchen_context.py`: tool facts, clarification association, relevant tool checks and practical fallbacks.
- `coach_web.py`: session storage, isolated updates, reset/logout/expiry behavior and state retrieval.
- `kitchen_coach.py`: context passed to the model, concise clarification instructions, and a shared display check for model/fixed replies.
- `templates/coach.html` and `coach_assets/coach.js`: reset explanatory text only; form structure unchanged.
- Evaluation helpers retain kitchen context across turns and record its version. Old evidence cannot be resumed across context changes. They were not run against a paid model.

The clinical-gate file, food-safety policy/validator files and legacy entry point are unchanged. Clinical uncertainty still prevents generation. Existing independent handling responses are checked for tool availability without permitting clinical advice.

## Offline validation

**245 tests passed**, including all existing regressions and new kitchen-context cases:
- unknown tool → one clarification;
- available tool → appropriate response proceeds;
- unavailable tool → no pretending or unsafe substitute;
- yes/no and “unsure” follow-ups resolve the correct question;
- profile/history facts prevent repeat questions;
- rice rinsing allowed; raw-poultry rinsing prohibited;
- measured poultry endpoint still required when a thermometer is available;
- microwave-only, no oven, no blender and no food processor;
- known stove and non-blended alternatives remain usable;
- explicit limited-time and no-shopping constraints;
- familiar/cultural meal and shared-household context retained;
- reload/reset retention, session isolation, logout clearing and failure handling;
- unchanged clinical-gate regressions.

Existing food-rule fixtures explicitly confirm tool availability so those tests continue testing the food rules; separate tests exercise unknown and unavailable tools. Existing profile-delivery tests also verify the new context is included without losing original fields.

## Limits and status

These are deterministic offline fixtures, not new live-model quality evidence. The tool recognizer covers clear English declarations and the listed equipment; it is not a universal language or appliance classifier. Duration checks cover explicit stated minutes, not a complete recipe schedule or cost calculator. Safe fallback responses can be less helpful than a successful adapted model answer.

The five paused paid evaluations remain paused. Phase 1 remains undeployed.
