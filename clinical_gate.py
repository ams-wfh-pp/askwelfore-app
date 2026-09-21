"""Deterministic routing before any model call; no model/SDK/prompt dependency.

Conservative English-language collaborator scope. Recognized high-risk context
stays gated across follow-ups. This is not a complete natural-language safety
classifier. Clinical confirmation never erases an allergy or opens clinical
prescribing. Independent supported tasks use fixed text, not model generation.
"""
import re
import unicodedata
from dataclasses import dataclass

VERSION = "clinical-gate-v2"

@dataclass(frozen=True)
class GateDecision:
    reason: str
    text: str

CONFIRM = {
    "renal": "Please confirm with your kidney clinician which dietary and electrolyte instructions apply, including whether the proposed salt substitute is suitable. I can't choose an amount or an interim plan while that is unresolved.",
    "electrolytes": "Please confirm the applicable electrolyte or sodium instructions and any target with your qualified healthcare professional. I can't choose, change or guess a target, amount or interim plan.",
    "fluids": "Please ask your qualified healthcare professional to confirm which fluid instructions apply to you. I can't resolve conflicting guidance or choose an amount or interim fluid plan.",
    "medication": "Please confirm the meal and medication instructions with your qualified healthcare professional. I can't recommend medication changes, therapeutic food adjustments or an interim plan.",
    "allergy": "Do not use the proposed ingredient or substitution while its allergy suitability is unresolved. Any earlier suggestion that conflicts with the allergy must not be used. Confirm the specific ingredient, label and cross-contact requirements with your qualified healthcare professional before proceeding.",
    "clinical": "Please confirm the specific nutrition instructions with your qualified healthcare professional. I can't establish or change a therapeutic target, resolve unclear guidance, or suggest an interim clinical plan.",
    "product": "Before using that product, check its ingredients and label against the household's restrictions. If allergy suitability or cross-contact safety is uncertain, confirm it with your qualified healthcare professional. I can't treat an unchecked product as suitable.",
}
CONTINUE = " Your meal and household context will stay in this conversation. While you confirm, you can ask: How do I clean a cutting board? Or: How do I check chicken with a thermometer?"
WORKSPACE = ("Clear a work area and set out the equipment you already planned to use. "
             "Keep raw-food tools separate from ready-to-eat-food tools. "
             "We can organize the workspace without choosing ingredients, portions or clinical targets. "
             "Your meal, cultural preferences and supplied guidance remain in the conversation.")

def normalize(value):
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = value.replace("\u2019", "'").replace("\u2011", "-")
    value = "".join(c for c in value if unicodedata.category(c) != "Cf")
    return " ".join(value.split())

def has(pattern, text):
    return re.search(pattern, text, re.I) is not None

# These are general implementation goals, not therapeutic prescriptions.
# Unknown guidance fails closed; do not infer its meaning from a familiar word.
ORDINARY_GOALS = {
    "reduce sodium", "reduce salt", "use less salt", "eat less salt", "less sodium",
    "my doctor wants me to reduce sodium", "my doctor said reduce sodium",
    "my doctor said reduce sodium; no recipe was reviewed",
    "cook more at home", "eat more vegetables", "more variety",
    "balanced meals", "healthy meals", "no nutrition guidance",
}

def assess(profile, history, message):
    # Read only user input. A model reply cannot authorize itself or clear a gate.
    current = normalize(message)
    values = [normalize(value) for value in profile.values()]
    previous = [normalize(item.get("content", "")) for item in history
                if item.get("role") == "user"]
    text = " ".join(values + previous + [current])
    # Exact negative declarations are not an allergy report. Do not remove
    # anything after "except", "but", or a named restriction.
    text = re.sub(r"\bno (?:known )?(?:food )?allergies\b(?!\s*(?:except|but))", "", text)
    guidance = normalize(profile.get("guidance", "")).rstrip(".")
    reason = None
    if has(r"\b(allerg\w*|anaphyla\w*|intoleran\w*|celiac|coeliac)\b|\b(?:nut|peanut|soy|dairy|gluten)[ -]free\b", text):
        reason = "allergy"
    elif has(r"\b(kidney\w*|renal|dialysis|ckd|nephro\w*)\b", text):
        reason = "renal"
    elif has(r"\b(medicat\w*|medicine\w*|dose\w*|pills|tablets|insulin|metformin|warfarin|lithium|diuretic\w*|prescription\w*)\b", text):
        reason = "medication"
    elif has(r"\b(fluid\w*|hydrat\w*|dehydrat\w*)\b|\bdrink\w* (?:more|less)\b|\b(?:glasses|cups|liters|litres)\b.{0,30}\bdrink\b|\bwater (?:limit|restrict)\w*", text):
        reason = "fluids"
    elif has(r"\b(potassium|electrolyte\w*|phosphorus|phosphate\w*|magnesium|kcl)\b|\bsalt (?:substitute|replacement)\b", text):
        reason = "electrolytes"
    elif has(r"\b(therapeutic|clinical|diagnos\w*|diabet\w*|glucose|hypoglyc\w*|blood sugar|heart failure|heart disease|hypertension|pregnan\w*|eating disorder|calorie\w*|nutrient\w*|macros|cholesterol)\b", text):
        reason = "clinical"
    elif has(r"\b(target\w*|limit\w*|dosage|allowance|restriction\w*|milligram\w*|mg|mcg|mmol)\b", text) and has(r"\b(sodium|salt|protein|carb\w*|fat|nutrition|diet\w*|doctor|clinician)\b", text):
        reason = "clinical"
    elif has(r"\bhow (?:much|many)\b|\b(?:safe|daily|recommended) (?:amount|intake|portion)\b|\bset (?:me )?a (?:target|limit)\b", current) and has(r"\b(sodium|salt|diet\w*|nutrition|carb\w*|protein|fat)\b", text):
        reason = "clinical"
    elif normalize(profile.get("restrictions", "")).rstrip(".") not in {"none", "none known", "none reported yet", "no allergies", "no known allergies", "no restrictions", "vegetarian", "vegan", "pescatarian", "halal", "kosher"}:
        reason = "clinical"
    elif guidance not in ORDINARY_GOALS:
        reason = "clinical"
    elif has(r"\b(?:label|ingredients?)\b.{0,25}\b(?:unknown|unchecked|not checked|uncertain)\b|\b(?:unknown|unchecked)\b.{0,15}\b(?:label|ingredients?)\b", text):
        reason = "product"
    if reason is None:
        return None
    # Exact, narrowly scoped requests only. Appended medical questions/instructions
    # do not match; the sensitive context never reaches model generation.
    if current.rstrip(".?!") in {
        "help me organize the cooking workspace", "how do i organize my cooking workspace",
        "help me set out my cooking equipment", "help me organize my kitchen tools",
    }:
        return GateDecision(reason + ":independent-workspace", WORKSPACE)
    from food_safety import TEXT, TEMPS
    independent = {
        "how do i wash my hands before cooking": "Wash hands with soap and running water for at least 20 seconds before food preparation and after touching raw food.",
        "how do i clean a cutting board": TEXT["surfaces"],
        "how do i check chicken with a thermometer": TEMPS["poultry"][2],
    }
    if current.rstrip(".?!") in independent:
        return GateDecision(reason + ":independent-handling",
                            independent[current.rstrip(".?!")] +
                            " Please still confirm the unresolved nutrition guidance with your qualified healthcare professional; this does not establish ingredient or portion suitability.")
    return GateDecision(reason, CONFIRM[reason] + CONTINUE)
