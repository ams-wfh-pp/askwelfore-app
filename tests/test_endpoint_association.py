"""Exact live false positive and nearby food-association contrasts."""
import pytest
from kitchen_coach import KitchenCoach
from test_food_safety import P

EXACT = (
 "Rinsing rice is good—helps remove surface starch for fluffier rice. Start by rinsing the rice in "
 "cold water until it runs clear, then drain. For low-sodium chicken and rice, sauté minced garlic "
 "and thyme in a bit of oil over medium heat. Add chicken pieces (e.g., thighs or breasts), sear "
 "until golden. Then add rinsed rice, a splash of lime juice for flavor, and water (typically 2 cups "
 "water per 1 cup rice). Cover and simmer gently for 20 minutes until rice is tender and chicken "
 "hits 165°F (74°C) inside with a thermometer. Let it rest covered 5 minutes before serving. "
 "Need help with amounts or seasoning tips without salt?"
)

def test_exact_live_false_positive_passes():
    reply = KitchenCoach(lambda *a: EXACT).respond(P, [], "Help cook dinner")
    assert reply.source == "model"
    assert reply.text == EXACT

@pytest.mark.parametrize("draft", [
 EXACT.replace(" inside with a thermometer", " inside"),
 EXACT.replace("165°F (74°C)", "145°F (63°C)"),
 "Cook chicken for 20 minutes while rice reaches 165 F with a food thermometer.",
 "Cook chicken for 20 minutes and check rice reaches 165 F with a food thermometer.",
 "Cook chicken for 20 minutes. Rice reaches 165 F with a food thermometer.",
 "Rinse raw chicken. Cook it to 165 F measured with a food thermometer.",
])
def test_food_association_does_not_weaken_safety(draft):
    reply = KitchenCoach(lambda *a: draft).respond(P, [], "Help cook dinner")
    assert reply.source == "food_safety_gate"

@pytest.mark.parametrize("draft", [
 "Rinse rice. Simmer until rice is tender and chicken reaches 165 F inside with a food thermometer.",
 "Cook chicken until a food thermometer reads 74 C in its thickest part.",
 "Cook chicken to 165 F internally and use a food thermometer to measure it.",
])
def test_named_or_inherited_poultry_endpoint_passes(draft):
    assert KitchenCoach(lambda *a: draft).respond(P, [], "Help cook dinner").source == "model"
