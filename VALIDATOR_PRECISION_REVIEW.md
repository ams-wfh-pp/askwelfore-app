# Validator precision correction

Development only. Safety rules and clinical gate unchanged.
Implementation identifier: food-safety-v2.1 (precision revision, not a new policy).

## Exact rejection path

The saved rice/poultry draft included:

> ...until rice is tender and chicken hits 165°F (74°C) inside with a thermometer.

The initial action parser stopped the simmering action's object at a relationship word and carried forward rice/produce context. The resulting statement had foods `rice` and `produce`.

In `poultry_endpoint()`, the condition `if "poultry" not in statement.foods: continue` therefore skipped this statement entirely. Neither the valid temperature nor the thermometer measurement was considered. The function returned false, and `screen()` returned the fixed poultry-endpoint fallback. Rice washing was not the rejecting rule.

## Small correction

The endpoint check now examines coordinated endpoint clauses and uses the food explicitly named in each clause, retaining the preceding food only when no food is named. It now associates “chicken hits ...” with poultry.

This does not change action-object extraction, permitted temperatures, required measurement, raw-poultry washing rules, fallback wording, model instructions or clinical gating. A rice endpoint in a different clause cannot satisfy a poultry endpoint. There are no new food/action keywords or broader blocking rules.

Production code change: a small endpoint-clause helper and its use in the existing endpoint check. The implementation version changes only to prevent resuming evaluation evidence across different validators.

## Offline evidence

The regression contains the exact full rejected model response. Before correction, it reproduced the false rejection. Nearby contrasts also exposed the reverse association error: crediting a rice temperature to chicken in a compound sentence.

After correction, **205 offline tests passed**:
- Exact compliant rice/poultry response passes unchanged.
- The same response without thermometer measurement is intercepted.
- A too-low poultry temperature is intercepted.
- Rice temperatures cannot satisfy poultry requirements, in either a compound sentence or separate sentence.
- Rice rinsing remains permitted; raw poultry rinsing remains prohibited.
- Existing clinical gate regressions pass unchanged.

The corrected trace identifies the endpoint clause's food as poultry and returns true. A comparison against the previous commit confirms the policy constants, instructions, clinical gate and evaluation sequence are unchanged.

## Live recheck

Pending. The authorized sequence remains the two initial cases, reviewed separately, followed by the five paused responses only if both pass. No paid call has been made for this correction at the time this note was written. Phase 1 remains undeployed; no merge, voice work or scope expansion.
