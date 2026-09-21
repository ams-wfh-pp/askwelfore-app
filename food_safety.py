"""Model-independent, conservative English food-handling controls.
See FOOD_SAFETY_POLICY.md for sources, supported scope and limitations.
No clinical quantities are inferred here. Clinical gating runs first.
"""
import re
import unicodedata
from dataclasses import dataclass

VERSION = "food-safety-v1"

@dataclass(frozen=True)
class Decision:
    reason: str
    text: str

def norm(value):
    s = unicodedata.normalize("NFKC", str(value)).casefold().replace("\u2019", "'")
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Cf").split())

def has(pattern, value):
    return re.search(pattern, value, re.I) is not None

TEXT = {
 "washing": "Do not wash or rinse raw meat or poultry, including with lemon or vinegar: splashes can spread germs. Keep your familiar seasoning approach; apply suitable seasonings without washing the meat. Wash hands and clean tools after handling it.",
 "surfaces": "Keep raw meat and its juices away from ready-to-eat food. Use separate clean boards and utensils. After raw-food contact, wash hands with soap for 20 seconds and wash tools and surfaces with hot, soapy water. Use fresh, suitable sauce for serving; don't reuse raw-meat marinade as a finishing sauce.",
 "thawing": "Thaw in the refrigerator at 40 F (4 C) or below. For faster thawing, use a leakproof bag in cold water, changing water every 30 minutes, then cook immediately. Microwave thawing also requires immediate cooking. Do not thaw on the counter or in hot water.",
 "leftovers": "Refrigerate cooked food promptly in shallow containers, within 2 hours (1 hour above 90 F/32 C). Keep the fridge at 40 F/4 C or below; use refrigerated leftovers within 3-4 days. Reheat leftovers to 165 F/74 C, checking with a thermometer. If storage time or temperature is uncertain, don't assume reheating makes it safe.",
 "discard": "Discard perishable food left at room temperature overnight or beyond 2 hours (1 hour above 90 F/32 C). Reheating does not reliably make improperly stored food safe. We can keep the meal idea and use properly stored ingredients instead.",
 "temperature_unknown": "Which food and cut are you cooking, and is it raw or already cooked? The minimum internal temperature depends on that. Use a food thermometer; time, color and clear juices alone cannot establish doneness.",
}
TEMPS = {
 "poultry": (165, 73.9, "Cook poultry, including ground poultry, to 165 F (74 C), checked with a food thermometer in the thickest part, away from bone. Time and color alone do not establish doneness."),
 "ground": (160, 71.1, "Cook ground beef, pork, lamb or veal to 160 F (71 C), checked with a food thermometer."),
 "whole": (145, 62.8, "Cook whole beef, pork, lamb or veal steaks, chops and roasts to 145 F (63 C), checked with a food thermometer, then rest for at least 3 minutes."),
 "fish": (145, 62.8, "Cook fish to 145 F (63 C), checked with a food thermometer."),
 "leftovers": (165, 73.9, "Reheat leftovers and casseroles to 165 F (74 C). In a microwave, cover, stir or rotate, and check several spots with a food thermometer."),
}
POLICY_INSTRUCTIONS = """
FOOD SAFETY POLICY (application rules, independent of model choice)
Never wash/rinse raw meat or poultry, including with citrus or vinegar.
Prevent raw-food cross-contamination; use clean separate tools for ready-to-eat food.
Use a thermometer: poultry/leftovers/casseroles 165 F (74 C); ground red meat
160 F (71 C); whole red-meat steaks/chops/roasts 145 F (63 C) plus 3 minutes rest;
fish 145 F (63 C). Color, clear juices and cooking time cannot prove doneness.
Thaw in the fridge <=40 F/4 C, or leakproof cold water changed every 30 minutes,
or microwave; the latter two require immediate cooking. Never counter/hot-water thaw.
Refrigerate perishables promptly within 2 hours, or 1 hour above 90 F/32 C,
in shallow containers; fridge <=40 F/4 C, leftovers 3-4 days. Never rescue
improper storage by reheating. Clarify unknown storage before recommending use.
Never approve an uncertain allergy substitution, trace exposure, or unchecked label.
Apply only rules relevant to this cooking task; do not recite the whole policy.
"""

def context(profile, history, message):
    return norm(" ".join([str(v) for v in profile.values()] +
                        [h.get("content", "") for h in history if h.get("role") == "user"] + [message]))

def category(text):
    if has(r"\bleftovers?\b|\breheat\w*\b|\bcasserole", text): return "leftovers"
    if has(r"\b(chicken|turkey|poultry|duck|goose)\b", text): return "poultry"
    if has(r"\b(?:ground|minced) (?:beef|pork|lamb|veal|meat)\b|\bburger", text): return "ground"
    if has(r"\b(?:steaks?|chops?|roasts?)\b", text) and has(r"\b(beef|pork|lamb|veal)\b", text): return "whole"
    if has(r"\b(fish|salmon|cod|tilapia|trout)\b", text): return "fish"
    return None

def decision(topic, ctx=""):
    if topic == "temperature":
        kind = category(ctx)
        return Decision(topic, TEMPS[kind][2] if kind else TEXT["temperature_unknown"])
    return Decision(topic, TEXT[topic])

def preflight(profile, history, message):
    m, ctx = norm(message), context(profile, history, message)
    if has(r"\b(?:wash|rinse|clean)\w*\b.{0,35}\b(?:chicken|poultry|turkey|raw meat)\b", m):
        return decision("washing")
    if has(r"\b(?:raw|unwashed)\b.{0,35}\b(?:board|utensil|knife|surface|salad|marinade)\b", m):
        return decision("surfaces")
    if has(r"\b(?:thaw|defrost)\w*\b", m):
        return decision("thawing")
    if has(r"(?:left|sat|sitting|stored|kept).{0,30}(?:out|counter|room).{0,25}overnight", m):
        return decision("discard")
    if has(r"\b(?:rice|cooked|leftovers?|meat|chicken)\b", ctx) and has(r"\b(?:left out|sat out|room temperature|on the counter)\b", ctx):
        if has(r"\b(?:overnight|all night)\b", ctx):
            return decision("discard")
        return decision("leftovers")
    if has(r"\b(?:internal temperature|thermometer|doneness)\b", m):
        return decision("temperature", m if category(m) else ctx)
    if has(r"\b(?:how long|store|refrigerat\w*|keep)\b.{0,30}\bleftovers?\b", m):
        return decision("leftovers")
    return None

def screen(profile, history, message, answer):
    """Withhold the entire draft on a recognized risk; never patch a dangerous sentence."""
    a, ctx = norm(answer), context(profile, history, message)
    # Split on sentences/newlines; don't treat a distant 'not' as negating an action.
    clauses = re.split(r"(?<!\d)[.!?;]+|[.!?;]+(?!\d)", a)
    meat = has(r"\b(chicken|poultry|turkey|duck|raw meat|beef|pork)\b", ctx + " " + a)
    for clause in clauses:
        for action in re.finditer(r"\b(wash\w*|rins\w*|clean\w*|soak\w*)\b", clause):
            tail = clause[action.end():]
            prefix = clause[:action.start()]
            negated = has(r"(?:do not|don't|never|avoid)\s*$", prefix)
            safe_object = has(r"^ (?:the |your )?(?:rice|hands|vegetables|produce|board\w*|tools|utensils|surfaces)\b", tail)
            if safe_object and has(r"\b(?:and|plus|along with)\b.{0,15}\b(?:chicken|poultry|turkey|meat)\b", tail):
                safe_object = False
            if meat and not negated and not safe_object:
                return decision("washing")
        if has(r"\bunwashed\b|\breuse\b.{0,40}\b(?:board|knife|utensil)\b|\braw(?:-meat| meat)? marinade\b", clause):
            return decision("surfaces")
        if has(r"\b(?:juices? (?:run |are )?clear|no longer pink|pinkness)\b", clause):
            if not has(r"\b(?:not|never|don't|cannot|can't|alone)\b", clause):
                return decision("temperature", ctx)
    if meat and has(r"\b(?:same|unwashed)\b.{0,30}\b(?:board|knife|utensil|plate)\b", a):
        return decision("surfaces")
    if meat and has(r"\b(?:done|cooked through|ready to eat|serve)\b", a):
        if has(r"\b(?:cook|simmer|fry|bake|roast|grill)\w*\b", a) and not has(r"\bthermometer\b", a):
            return decision("temperature", ctx)
    # Safety-bearing thaw/storage advice is owned by fixed policy, not free text.
    if has(r"\b(?:thaw|defrost)\w*\b", a):
        return decision("thawing")
    if has(r"\b(?:overnight|cool completely|seven days|7 days|a week)\b", a) and has(r"\b(?:rice|cooked|leftovers?|food|fridge|counter)\b", a):
        return decision("discard" if has(r"\b(?:out|counter|room)\b", a) else "leftovers")
    if has(r"\b(?:refrigerat\w*|store|keep|leave)\b.{0,60}\b(?:hours?|days?|minutes?)\b", a):
        return decision("leftovers")
    # Validate explicit internal temperatures, not clearly identified oven settings.
    for clause in clauses:
        numbers = re.findall(r"(\d+(?:\.\d+)?)\s*(?:degrees?\s*|\u00b0\s*)?([fc])\b", clause)
        if not numbers:
            if has(r"\b(?:internal temperature|degrees? fahrenheit|degrees? celsius)\b", clause):
                return decision("temperature", clause if category(clause) else ctx)
            continue
        if has(r"\b(?:oven|preheat)\b", clause) and not has(r"\b(?:internal|thermometer|reaches?)\b", clause):
            continue
        kind = category(clause) or category(ctx)
        if not kind: return decision("temperature", ctx)
        f, c, _ = TEMPS[kind]
        # Accept standard rounded Celsius equivalents (71/63/74).
        for number, unit in numbers:
            minimum = f if unit == "f" else c
            rounded_celsius = unit == "c" and float(number) == round(c)
            if float(number) < minimum and not rounded_celsius:
                return decision("temperature", clause if category(clause) else ctx)
        if kind == "whole" and not has(r"\b3[ -]minute|\bthree[ -]minute|rest.{0,20}\b3\b", clause):
            return decision("temperature", clause)
    return None
