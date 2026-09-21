"""Kitchen reality contracts: deterministic fixtures, never paid models."""
import copy
import json
import pytest
from kitchen_context import KitchenContext
from kitchen_coach import KitchenCoach
P = dict(household="Two adults sharing one meal", culture="Caribbean",
         restrictions="None", guidance="Reduce sodium", source="My doctor",
         ingredients="Chicken, rice, garlic, thyme", constraints="30 minutes; stove; beginner")
SAFE = "Cook chicken on the stove to 165 F internally, measured with a food thermometer."

def turn(coach, state, history, message, profile=None):
    reply = coach.respond(profile or P, history, message, kitchen=state)
    history.extend([{"role":"user","content":message},{"role":"assistant","content":reply.text}])
    return reply

def test_unknown_asks_one_question_then_no_resolves():
    k, h = KitchenContext(), []
    coach = KitchenCoach(lambda *a: SAFE)
    first = turn(coach,k,h,"Help with chicken and rice")
    assert first.source == "kitchen_context"
    assert first.text.count("?") == 1 and "thermometer" in first.text
    assert k.pending_tool == "thermometer"
    second = turn(coach,k,h,"no")
    assert k.tools["thermometer"] == "unavailable" and not k.pending_tool
    assert second.source == "kitchen_context"
    assert "rice" in second.text.lower()
    assert "do you have" not in second.text.lower()
    assert "165" not in second.text  # No unusable cooking method.
    third = turn(coach,k,h,"Continue")
    assert "do you have" not in third.text.lower()

def test_yes_resolves_without_repeat_and_preserves_original_request():
    k, h, captured = KitchenContext(), [], []
    def generate(instructions, messages, budget):
        captured.append(json.loads(messages[0]["content"].split("\n",1)[1]))
        return SAFE
    coach = KitchenCoach(generate)
    turn(coach,k,h,"Help with chicken and rice")
    reply = turn(coach,k,h,"yes")
    assert reply.source == "model"
    assert k.tools["thermometer"] == "available"
    assert captured[-1]["kitchen_context"]["resume_request"] == "Help with chicken and rice"
    assert captured[-1]["culture"] == "Caribbean"

@pytest.mark.parametrize("where", ["profile", "history"])
def test_supplied_tool_prevents_question(where):
    p = copy.deepcopy(P)
    h = []
    if where == "profile": p["constraints"] += "; I have a food thermometer"
    else: h = [{"role":"user","content":"I have a food thermometer."}]
    r = KitchenCoach(lambda *a:SAFE).respond(p,h,"Help with dinner",kitchen=KitchenContext())
    assert r.source == "model"

@pytest.mark.parametrize("constraints,draft,tool", [
 ("microwave only; 15 minutes", "Roast vegetables in the oven.", "oven"),
 ("stove; no oven", "Bake the rice in the oven.", "oven"),
 ("no blender; stove", "Use a blender to puree the sauce.", "blender"),
 ("no food processor", "Use a food processor for the herbs.", "food_processor"),
])
def test_unavailable_tool_is_not_assumed(constraints,draft,tool):
    k=KitchenContext()
    r=KitchenCoach(lambda *a:draft).respond({**P,"constraints":constraints},[],
                                           "Keep our familiar meal",kitchen=k)
    assert k.tools[tool] == "unavailable"
    assert r.source == "kitchen_context"
    assert r.text != draft and "do you have" not in r.text.lower()

def test_unknown_blender_asks_only_blender():
    k=KitchenContext()
    r=KitchenCoach(lambda *a:"Use a blender to puree your sauce.").respond(P,[],"Help with sauce",kitchen=k)
    assert k.pending_tool == "blender"
    assert r.text.count("?")==1 and "oven" not in r.text

def test_no_question_when_method_does_not_need_unknown_tool():
    r=KitchenCoach(lambda *a:"Use the garlic and thyme you already have for familiar flavor.").respond(P,[],"Help with flavor",kitchen=KitchenContext())
    assert r.source=="model"

def test_microwave_only_available_method_passes():
    k=KitchenContext()
    p={**P,"ingredients":"Canned beans", "constraints":"15 minutes; microwave only; small budget"}
    r=KitchenCoach(lambda *a:"Warm your beans in a microwave-safe bowl in the microwave.").respond(p,[],"Help with beans",kitchen=k)
    assert r.source=="model"
    assert k.tools["microwave"]=="available"
    assert k.tools["oven"]==k.tools["stove"]=="unavailable"

def test_time_budget_culture_and_known_tools_reach_model():
    p={**P,"constraints":"10 minutes; no additional grocery purchase; no blender; stove"}
    seen=[]
    def generate(instructions,messages,budget):
        seen.append((instructions,json.loads(messages[0]["content"].split("\n",1)[1])))
        return "Keep the rice, garlic and thyme you have; no shopping is needed."
    r=KitchenCoach(generate).respond(p,[],"Keep one shared meal",kitchen=KitchenContext())
    assert r.source=="model"
    assert seen[0][1]["constraints"]==p["constraints"]
    assert seen[0][1]["household"]==p["household"] and seen[0][1]["culture"]=="Caribbean"
    assert seen[0][1]["kitchen_context"]["tools"]["blender"]=="unavailable"
    assert "equipment" in seen[0][0].lower() and "budget" in seen[0][0].lower()

@pytest.mark.parametrize("draft,allowed", [
 ("Rinse 1 cup of rice.",True),
 ("Rinse raw chicken.",False),
])
def test_washing_rules_survive_tool_context(draft,allowed):
    r=KitchenCoach(lambda *a:draft).respond(P,[],"Help",kitchen=KitchenContext())
    assert (r.source=="model")==allowed
    if not allowed: assert "Do not wash" in r.text

def test_missing_endpoint_still_blocked_when_tool_available():
    p={**P,"constraints":"stove; food thermometer available"}
    r=KitchenCoach(lambda *a:"Cook chicken until the juices run clear.").respond(p,[],"Help",kitchen=KitchenContext())
    assert r.source=="food_safety_gate"
    assert "165" in r.text and "thermometer" in r.text

def test_clinical_uncertainty_still_prevents_generation():
    p={**P,"guidance":"Kidney potassium instructions unclear"}
    def forbidden(*a): pytest.fail("Clinical gate bypass")
    r=KitchenCoach(forbidden).respond(p,[],"How much should I use?",kitchen=KitchenContext())
    assert r.source=="clinical_gate"

def test_unknown_not_assumed_from_question_or_model_history():
    k=KitchenContext()
    p={**P,"constraints":""}
    h=[{"role":"assistant","content":"You have a blender."}]
    k.observe(p,h,"Would a blender help?")
    assert k.tools["blender"]=="unknown"

def test_latest_explicit_update_wins_without_profile_reapplying():
    k=KitchenContext()
    p={**P,"constraints":"I have a blender"}
    k.observe(p,[],"Help")
    assert k.tools["blender"]=="available"
    k.observe(p,[],"My blender is broken.")
    assert k.tools["blender"]=="unavailable"
    k.observe(p,[],"Continue")
    assert k.tools["blender"]=="unavailable"
