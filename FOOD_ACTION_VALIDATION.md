# Food/action validation revision

Development only; no deployment or merge. Food policy version: food-safety-v2.
The existing clinical gate is unchanged (clinical-gate-v2).

## What changed

The poultry controls now have separate interpretation and policy stages:

1. `food_actions.py` extracts food/action records from each statement. It binds an action to its own object, handles quantities and descriptive words, separates equipment and broth from meat, and carries explicit food references across statements. Ambiguous references remain marked as ambiguous.
2. The washing rule applies to washing/rinsing meat or poultry. Rice, produce, hands and equipment are not prohibited washing objects. “Rinse 1 cup of rice” and “add the rinsed rice” no longer become poultry-washing instructions merely because chicken appears elsewhere.
3. Poultry cooking and doneness instructions require a poultry-associated temperature endpoint and thermometer measurement. A rice temperature or oven setting cannot satisfy this requirement. Missing, too-low, unrelated, negated or optional thermometer endpoints fail validation.
4. The application withholds the entire failed draft before display and returns a concise fixed response containing the relevant rule. There is no automatic paid regeneration. The user's existing meal, culture, household and conversation remain available for the next turn.
5. Evaluation evidence preserves both the delivered response and withheld draft, with actual call/cost accounting. An intercepted draft is not scored as model compliance.

The required poultry endpoint is **165 F / 74 C internal temperature measured with a food thermometer**, grounded in [USDA poultry guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/poultry/chicken-farm-table) and [USDA doneness versus safety](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/doneness-versus-safety). Poultry washing is prohibited under [USDA washing guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/washing-food-does-it-promote-food).

This remains a small deterministic English-language parser and validation layer, not a general cooking knowledge engine or an LLM safety judge. It cannot prove that every conceivable paraphrase is understood. It deliberately requires an endpoint even for an initial poultry-cooking step. The existing limited controls for other food-safety topics remain; no new service or dependency was added.

## Offline results

**195 offline tests passed.** The new paired tests were written first and initially reproduced 14 failures under the old implementation.

Tested contrasts include:
- Poultry rinsing versus rice rinsing, including measured quantities, passive wording, pronouns and mixed objects.
- Time/appearance-only cooking versus the measured poultry endpoint.
- Poultry temperature versus rice temperature and oven settings.
- Correct Fahrenheit/Celsius wording versus too-low temperatures.
- Required thermometer use versus missing or optional thermometer use.
- Harmless equipment/hand cleaning and chicken broth versus raw poultry.
- Preserved context and enforcement even when the model prompt is replaced.
- No further calls after a failed first or second recheck.

The exact saved mixed-cuisine failure is withheld. The saved rice response is no longer flagged for rice rinsing; it is correctly withheld because its poultry instruction lacked a thermometer check. Adding the required measurement wording to that same draft allows it through. These are offline fixture results, not new live-model results.

## Authorized live sequence

Provisional GPT-4.1 mini; at most **seven responses**, no retries, 700 output tokens per call:
1. Failed mixed-cuisine poultry case.
2. Rice-rinsing recheck. The original Caribbean case explicitly adds the user's normal rice-rinsing step so the distinction is exercised rather than left to model chance.
3. Only after both are reviewed as passing: limited equipment (one), household differences (two), unavailable ingredients/follow-up (two).

Every response pauses for review. Stop at the next release-blocking safety failure. Do not resume old results across policy versions. Live results are pending; Phase 1 stays undeployed.
