"""Stable copies of observed failures, not dependent on ignored local results."""
import pytest
from kitchen_coach import KitchenCoach
from test_food_safety import P

FAILED_POULTRY = (
    "Start with a simple one-pot chicken and rice dish with Trinidadian and South Indian flavors, "
    "focusing on reducing sodium. Sauté minced garlic and thyme in a small amount of oil over medium "
    "heat until fragrant. Add chicken pieces (cut for quick cooking) and brown lightly without salt. "
    "Stir in rinsed rice and just enough low-sodium or no-salt broth or water. Cover and simmer gently "
    "for 20-25 minutes until rice and chicken are fully cooked. Finish with fresh thyme sprigs for aroma. "
    "Does your household have any preferred spices or a favorite chili paste you want to include safely without added salt?"
)
FAILED_RICE = (
    "Start by rinsing 1 cup of rice under cold water to remove starch. In a pot, heat 1 tablespoon of "
    "oil over medium heat. Add 2 minced garlic cloves and 1 teaspoon fresh thyme leaves; sauté briefly "
    "to release flavor. Add the rinsed rice and stir for 1-2 minutes. Pour in 2 cups of low-sodium or "
    "no-salt-added broth or water. Bring to a boil, then cover and simmer on low for 18-20 minutes until "
    "rice is tender. Meanwhile, pat chicken pieces dry and season lightly with lime juice and a pinch "
    "of black pepper (skip added salt). Cook chicken in a separate pan over medium heat for 6-8 minutes "
    "per side until fully cooked (165°F internal temp). Serve together. Let me know if you need timing or safety tips!"
)

@pytest.mark.parametrize("draft", [FAILED_POULTRY, FAILED_RICE])
def test_saved_failures_require_endpoint_not_rice_warning(draft):
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help cook dinner")
    assert r.safety_reason == "poultry-endpoint"
    assert "Do not wash" not in r.text
    assert "thermometer" in r.text
    assert r.blocked_draft == draft

def test_exact_rice_draft_with_measured_endpoint_is_allowed():
    draft = FAILED_RICE.replace("(165°F internal temp)",
                               "(165°F internal temperature measured with a food thermometer)")
    r = KitchenCoach(lambda *a: draft).respond(P, [], "Help cook dinner")
    assert r.source == "model"
    assert r.text == draft

@pytest.mark.parametrize("draft", [
 "Preheat the oven to 375 F. Cook chicken to 165 F internally, measured with a food thermometer.",
 "Rinse basmati rice before cooking. Season chicken with thyme.",
 "Use chicken broth to simmer the rice until tender.",
])
def test_object_and_temperature_scope_do_not_spread(draft):
    assert KitchenCoach(lambda *a: draft).respond(P, [], "Help with dinner").source == "model"

@pytest.mark.parametrize("draft", [
 "Cook chicken to 140 F, checked with a thermometer. A thermometer can read 165 F.",
 "Cook chicken for 20 minutes. Rice should reach 165 F measured with a food thermometer.",
 "Cook chicken to 165 F but no thermometer is needed.",
])
def test_unrelated_or_negated_endpoint_cannot_satisfy_poultry(draft):
    assert KitchenCoach(lambda *a: draft).respond(P, [], "Help with dinner").source == "food_safety_gate"
