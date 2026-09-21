"""Small English food/action representation for deterministic policy checks.
Not a recipe engine or an LLM classifier. Ambiguous references remain explicit.
"""
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class FoodAction:
    kind: str
    foods: frozenset
    negated: bool
    statement: int
    ambiguous: bool = False

@dataclass(frozen=True)
class Statement:
    text: str
    foods: frozenset

@dataclass(frozen=True)
class Analysis:
    actions: tuple
    statements: tuple

FOODS = {
 "poultry": r"\b(?:chicken|poultry|turkey|duck|goose)\b",
 "rice": r"\brice\b",
 "produce": r"\b(?:garlic|thyme|onions?|vegetables?|produce|lime|lemon|herbs?|peppers?|beans?)\b",
 "hands": r"\bhands?\b",
 "tools": r"\b(?:boards?|utensils?|knives|knife|surfaces?|tools?|plates?|platter|sink)\b",
 "red_meat": r"\b(?:beef|pork|lamb|veal|raw meat)\b",
 "fish": r"\b(?:fish|salmon|cod|tilapia|trout)\b",
 "liquid": r"\b(?:broth|stock|water|oil)\b",
}
VERBS = {
 "wash": r"wash(?:ed|ing)?|rins(?:e|ed|ing)|clean(?:ed|ing)?",
 "cook": r"cook(?:ed|ing)?|simmer(?:ed|ing)?|bak(?:e|ed|ing)|roast(?:ed|ing)?|fry|fried|frying|grill(?:ed|ing)?|poach(?:ed|ing)?|steam(?:ed|ing)?|brown(?:ed|ing)?|sear(?:ed|ing)?|(?:re)?heat(?:ed|ing)?",
 "finish": r"done|ready(?: to (?:eat|serve))?|fully cooked|cooked through|safe to (?:eat|serve)",
 "refer": r"add|season|take|pat|stir|remove|serve|check|measure",
}
ACTION = re.compile(r"\b(?:" + "|".join("(?P<"+k+">"+v+")" for k,v in VERBS.items()) + r")\b")
# Relationships such as 'for our chicken dinner' don't make chicken the object of rinsing.
RELATION = re.compile(r"\b(?:before|after|for|with|using|under|over|until|into|onto|to|at|in|then|when)\b")

def objects(text):
    # Ingredient derivatives and equipment names are not raw poultry.
    text = re.sub(r"\b(?:chicken|turkey|poultry)\s+(?:broth|stock)\b", "broth", text)
    text = re.sub(r"\b(?:raw\s+)?(?:chicken|turkey|poultry)\s+(?:cutting\s+)?(?=board|knife|plate|utensil)", "", text)
    return frozenset(name for name, pattern in FOODS.items() if re.search(pattern, text))

def analyze(text, context_text=""):
    """Bind verbs to their own objects, then carry an explicit referent forward."""
    fallback = objects(context_text) - {"hands", "tools", "liquid"}
    referent = frozenset()
    actions, statements = [], []
    parts = [p.strip() for p in re.split(r"(?<!\d)[.!?;]+|[.!?;]+(?!\d)", text) if p.strip()]
    for index, part in enumerate(parts):
        matches = list(ACTION.finditer(part))
        part_foods = set()
        previous_end = 0
        for n, match in enumerate(matches):
            end = matches[n+1].start() if n+1 < len(matches) else len(part)
            tail = part[match.end():end]
            direct = RELATION.split(tail, maxsplit=1)[0]
            foods = objects(direct)
            before = part[previous_end:match.start()]
            # Passive wording and doneness assertions carry the subject before the verb.
            if not foods:
                subject = re.split(r"\b(?:then|and|but)\b", before)[-1]
                foods = objects(subject)
            ambiguous = False
            if not foods:
                foods = referent
                if not foods:
                    foods = fallback
                    ambiguous = True
            negated = bool(re.search(r"(?:do not|don't|never|avoid|without)\s*$", before))
            actions.append(FoodAction(match.lastgroup, foods, negated, index, ambiguous))
            part_foods.update(foods)
            if foods and not ambiguous:
                referent = foods
            previous_end = match.end()
        explicit = objects(part)
        if not matches:
            part_foods.update(explicit or referent or fallback)
            if explicit:
                referent = explicit
        statements.append(Statement(part, frozenset(part_foods)))
    return Analysis(tuple(actions), tuple(statements))

TEMP = re.compile(r"(\d+(?:\.\d+)?)\s*(?:degrees?\s*|\u00b0\s*)?(f(?:ahrenheit)?|c(?:elsius)?)\b")

def endpoint_statements(analysis):
    """Bind each endpoint clause to its named food, retaining pronoun context.
    Action objects remain unchanged: an endpoint subject is not a washing object.
    """
    for statement in analysis.statements:
        referent = statement.foods
        for clause in re.split(r"\b(?:and|but|while|until)\b", statement.text):
            named = objects(clause)
            if named:
                referent = named
            yield Statement(clause, referent)

def poultry_endpoint(analysis):
    """Endpoint must refer to poultry, be internal (not oven), and be measured.
    Return False for a contradicting temperature or rejection of a thermometer.
    """
    target, measurement = False, False
    for statement in endpoint_statements(analysis):
        if "poultry" not in statement.foods:
            continue
        text = statement.text
        if re.search(r"(?:no|without) (?:food )?thermometer|(?:don't|do not|need not).{0,20}thermometer|thermometer.{0,25}(?:unnecessary|optional|not needed|not required|not necessary|if available)|if (?:available|you have).{0,25}thermometer", text):
            return False
        if re.search(r"(?:with|using|use|measured (?:with|by)) (?:a |your |the )?(?:food )?thermometer|thermometer (?:reads|registers|shows)", text):
            measurement = True
        numbers = TEMP.findall(text)
        if re.search(r"\b(?:oven|preheat)\b", text) and not re.search(r"\b(?:internal|internally|thickest|center|centre)\b", text):
            continue
        if not numbers:
            continue
        if any(float(n) < (165 if unit.startswith("f") else 73.9) for n,unit in numbers):
            return False
        target = True
    return target and measurement

def poultry_cooking(analysis):
    instruction = any(a.kind in {"cook", "finish"} and "poultry" in a.foods and not a.negated
                      for a in analysis.actions)
    endpoint_claim = any("poultry" in s.foods and (TEMP.search(s.text) or "internal temperature" in s.text)
                         and not re.search(r"\b(?:oven|preheat)\b", s.text)
                         for s in analysis.statements)
    return bool(instruction or endpoint_claim)

def unsafe_washing(analysis):
    return next((a for a in analysis.actions if a.kind == "wash" and not a.negated
                 and a.foods & {"poultry", "red_meat"}), None)
