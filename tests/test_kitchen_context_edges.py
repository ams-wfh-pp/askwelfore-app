"""Clear user declarations, uncertainty, and safe alternatives."""
import pytest
from kitchen_context import KitchenContext
from kitchen_coach import KitchenCoach
from test_kitchen_context import P
from test_coach import no_network

@pytest.mark.parametrize("text,status", [
 ("food thermometer required", "unknown"),
 ("I might have a thermometer", "unknown"),
 ("no food thermometer", "unavailable"),
 ("food thermometer available", "available"),
 ("I have a food thermometer", "available"),
])
def test_requirements_and_uncertainty_are_not_availability(text,status):
    k=KitchenContext(); k.observe({**P,"constraints":text},[],"Help")
    assert k.tools["thermometer"]==status

def test_no_oven_does_not_block_known_stove_alternative():
    draft="Use your stove to sauté garlic and thyme for the rice."
    p={**P,"constraints":"no oven; stove"}
    r=KitchenCoach(lambda *a:draft).respond(p,[],"Help with rice",kitchen=KitchenContext())
    assert r.source=="model" and r.text==draft

def test_no_blender_can_keep_familiar_texture_without_purchase():
    draft="Keep the sauce chunky and stir in your garlic and thyme rather than making a smooth puree."
    p={**P,"constraints":"no blender; no additional grocery purchase"}
    r=KitchenCoach(lambda *a:draft).respond(p,[],"Help with sauce",kitchen=KitchenContext())
    assert r.source=="model" and r.text==draft

def test_negative_tool_declaration_in_message_changes_deterministic_reply():
    r=KitchenCoach(lambda *a:pytest.fail("Fixed response needs no model")).respond(
        P,[],"I don't have a thermometer",kitchen=KitchenContext())
    assert r.source=="kitchen_context" and "Without a food thermometer" in r.text
    assert "165" not in r.text and "rice" in r.text

def test_safety_is_not_shortened_to_meet_time_limit():
    draft="Cook chicken until the juices run clear in 5 minutes."
    p={**P,"constraints":"5 minutes; stove; food thermometer available"}
    r=KitchenCoach(lambda *a:draft).respond(p,[],"Help",kitchen=KitchenContext())
    assert r.source=="food_safety_gate"
    assert "165" in r.text and "thermometer" in r.text

def test_direct_rice_request_does_not_prompt_for_poultry_tool():
    r=KitchenCoach(lambda *a:"Rinse your rice until the water runs clear.").respond(
        P,[],"Only help me rinse rice",kitchen=KitchenContext())
    assert r.source=="model"
