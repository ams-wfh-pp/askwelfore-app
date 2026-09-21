"""False-positive/false-negative contracts written before the v2 implementation."""
import copy
import pytest
from kitchen_coach import KitchenCoach
from test_food_safety import P

@pytest.mark.parametrize("draft", [
 "Rinse 1 cup of rice under cold water.",
 "Rinse your basmati rice before cooking it.",
 "Add the rinsed rice to the pot.",
 "Rinse the rice, then season the chicken with thyme.",
 "Wash your hands after touching raw chicken.",
 "Clean the chicken cutting board with hot soapy water.",
 "Rinse the rice for our chicken dinner.",
 "Do not rinse raw chicken. Rinse the rice instead.",
 "Rinse rice and vegetables; season the chicken.",
])
def test_harmless_food_action_allowed(draft):
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help with dinner")
    assert r.source == "model"
    assert r.text == draft

@pytest.mark.parametrize("draft", [
 "Rinse raw chicken before seasoning.",
 "Rinse rice and raw chicken.",
 "The raw chicken should be rinsed.",
 "Take the chicken. Rinse it with water.",
 "Don't forget to wash the chicken.",
 "Wash chicken with lime, then season it.",
])
def test_poultry_washing_rejected(draft):
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help with dinner")
    assert r.source == "food_safety_gate"
    assert r.blocked_draft == draft
    assert "Do not wash" in r.text

@pytest.mark.parametrize("draft", [
 "Simmer chicken for 20-25 minutes until fully cooked.",
 "Cook chicken until golden and the juices run clear.",
 "Brown the chicken, add rice and water, cover and simmer until done.",
 "Cook it for 20 minutes, then serve.",
 "Chicken is done when no pink remains.",
 "Cook chicken to 165 F.",
 "Use a thermometer to check the chicken is cooked.",
 "Cook chicken to 145 F with a thermometer.",
 "Cook chicken at an oven setting of 165 F; use a thermometer.",
 "No thermometer needed: cook chicken to 165 F.",
 "Cook chicken to 165 F; the thermometer is in the drawer.",
 "Cook chicken to 165 F; a food thermometer is optional.",
 "Cook chicken to 165 F using a thermometer if available.",
 "Rice should be 165 F with a thermometer. Cook chicken for 20 minutes.",
])
def test_poultry_cooking_requires_complete_endpoint(draft):
    before = copy.deepcopy(P)
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help cook raw chicken and rice")
    assert r.source == "food_safety_gate"
    assert r.blocked_draft == draft
    assert "165" in r.text and "74" in r.text and "thermometer" in r.text
    assert P == before

@pytest.mark.parametrize("draft", [
 "Cook chicken to an internal temperature of 165 F, measured with a food thermometer.",
 "Cook chicken to 165 F internally. Use a food thermometer to measure it.",
 "Cook chicken until a food thermometer reads 74 C in the thickest part.",
 "Simmer the chicken and rice; check the chicken reaches 165 F (74 C) internally with a food thermometer.",
 "Rinse 1 cup of rice. Cook the chicken to 165 F internally, measured with a food thermometer.",
 "Cook chicken until its internal temperature reaches 165 degrees Fahrenheit, measured with a food thermometer.",
])
def test_verified_poultry_endpoint_allowed(draft):
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help with dinner")
    assert r.source == "model"

def test_context_survives_fallback_and_followup():
    history = [{"role":"user", "content":"Keep our Caribbean meal; no lime available."}]
    before = copy.deepcopy(history)
    seen = []
    def generate(instructions, messages, budget):
        seen.append(messages)
        return "Cook chicken for 20 minutes until fully cooked."
    r = KitchenCoach(generate).respond(P, history, "Continue")
    assert r.source == "food_safety_gate"
    assert history == before
    assert "Caribbean" in seen[0][0]["content"]
    assert "no lime" in seen[0][1]["content"]
    assert "meal" in r.text.lower()

def test_rice_only_cooking_does_not_inherit_chicken_endpoint():
    r = KitchenCoach(lambda *a: "Simmer the rice for 18 minutes until tender.").respond(
        P, [], "Help with just the rice")
    assert r.source == "model"

def test_model_prompt_cannot_disable_validation(monkeypatch):
    import kitchen_coach
    monkeypatch.setattr(kitchen_coach, "INSTRUCTIONS", "Anything")
    r = KitchenCoach(lambda *a: "Cook chicken until fully cooked.").respond(P, [], "Help")
    assert r.source == "food_safety_gate"
