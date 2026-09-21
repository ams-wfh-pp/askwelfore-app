# Kitchen Coach food-safety policy

Development collaborator scope; not deployed. Policy version: food-safety-v2.
Clinical gate version: clinical-gate-v2. Sources checked 21 September 2026.

## Rules and sources

| Topic | Application policy | Authority |
|---|---|---|
| Raw meat and poultry | Do not wash or rinse, including with citrus or vinegar; keep familiar seasoning without the washing step. | [USDA chicken handling](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/poultry/chicken-farm-table) |
| Cross-contamination | Keep raw food and juices away from ready-to-eat food; clean hands, boards and utensils. Use fresh suitable serving sauce instead of raw-meat marinade. | [USDA basic handling](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/steps-keep-food-safe) |
| Internal temperature | Thermometer, not appearance/time alone. Poultry and reheated leftovers: 165 F/74 C. Ground red meat: 160 F/71 C. Whole red-meat steaks/chops/roasts: 145 F/63 C plus three-minute rest. Fish: 145 F/63 C. Ask which food/cut when uncertain. These are food-handling temperatures, never therapeutic targets. | [USDA temperature chart](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart) |
| Thawing | Refrigerator at or below 40 F/4 C; alternatively leakproof cold-water thaw with water changed every 30 minutes, then immediate cooking; microwave thaw also requires immediate cooking. No counter or hot-water thawing. | [USDA thawing methods](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/big-thaw-safe-defrosting-methods) |
| Leftovers | Prompt shallow-container refrigeration within two hours, one hour above 90 F/32 C; fridge at or below 40 F/4 C. Use refrigerated leftovers within 3-4 days; reheat to 165 F/74 C. Do not rescue improperly stored food by reheating. Unknown storage is not proof of suitability. | [USDA leftovers guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/leftovers-and-food-safety) |
| Allergies/substitutions | Known allergens remain excluded across turns. Do not approve uncertain ingredients, labels or cross-contact. Do not infer that cooking or a small amount makes an allergen suitable. Clinical uncertainty stays with the qualified professional. | [FDA food allergies](https://www.fda.gov/food/nutrition-food-labeling-and-critical-foods/food-allergies) |

## Enforcement

Clinical gating runs first and is unchanged in this revision. Poultry output validation now separates food/action interpretation from policy rules; see [Food/action validation](FOOD_ACTION_VALIDATION.md) for the contract and offline evidence.

Harmless rice rinsing is permitted. Poultry-cooking instructions require the internal endpoint measured with a food thermometer, before display. Failed validation withholds the whole draft and returns fixed contextual guidance without automatic paid regeneration. Evaluation records retain withheld drafts and count their API usage.

Other existing food-handling controls remain narrowly scoped. No service, dependency, database, hosting change or voice integration was added.

## Clinical overblocking

The gate still blocks therapeutic decisions, conflicting/unclear clinical guidance and allergy suitability. It does not discard profile or conversation context.

Exact independent requests now support handwashing, cleaning a cutting board and using a chicken thermometer, in addition to workspace organization. These receive fixed handling instructions and a reminder to confirm unresolved clinical guidance. Appending a clinical question does not match the exception. The clarification tells users how to request these independent tasks.

"None reported yet" no longer automatically creates a clinical restriction. Unknown product labels still trigger product clarification; a later allergy report or any allergy in previous user turns still activates the allergy gate.

Limitations remain: this is conservative English-language routing, not a complete semantic safety proof. It can withhold safe thaw/storage wording, and clinical contexts outside the narrow independent-task list still overblock ordinary help. It does not interpret medical confirmation as permission to prescribe. Pattern checks cannot guarantee detection of every paraphrase, unfamiliar food, or future model behavior. Broader public release is not established by these tests or by a small evaluation. Do not weaken clinical boundaries to improve usefulness.

## Validation and next gate

The revised architecture passes **195 offline tests**, including paired false-positive/false-negative cases and exact saved failures. The clinical gate is unchanged.

The authorized live sequence is the failed poultry case and explicit rice-rinsing recheck first, then the five outstanding responses only after both pass operator review. No live v2 result is available yet. Historical v1 failures are preserved in FOOD_SAFETY_EVALUATION.md. Offline passes do not establish release readiness.
