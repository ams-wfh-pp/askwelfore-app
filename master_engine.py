"""
WelFore Health Master Engine v1.3
Generates culturally attuned, fiber- and color-balanced meal plans with freemium logic.
Includes GLP-1 / bariatric / breastfeeding adaptations and healthy snack pairings.
"""

from typing import Dict, List, Any
from datetime import datetime
import random

# -----------------------------
# CUISINE MEAL PALETTES
# -----------------------------
CUISINE_MEALS = {
    "African American": {
        "breakfast": ["Sweet potato hash with collard greens", "Grits bowl with scrambled eggs and greens"],
        "lunch": ["Black-eyed pea salad with cornbread", "Smoked turkey and kale soup"],
        "dinner": ["Baked chicken with roasted okra and brown rice", "Turkey meatballs with greens and sweet potato"],
        "colors": ["orange", "green", "white", "red"]
    },
    "Caribbean": {
        "breakfast": ["Ackee and callaloo scramble", "Plantain and egg bowl"],
        "lunch": ["Jerk chicken salad with mango", "Rice and peas with steamed vegetables"],
        "dinner": ["Grilled fish with festival and coleslaw", "Curry chickpea stew with rice"],
        "colors": ["yellow", "green", "red", "orange"]
    },
    "Mexican": {
        "breakfast": ["Huevos rancheros with black beans", "Breakfast burrito with veggies"],
        "lunch": ["Chicken fajita bowl with peppers", "Black bean and corn salad"],
        "dinner": ["Fish tacos with cabbage slaw", "Chicken enchiladas with verde sauce"],
        "colors": ["red", "green", "yellow", "orange"]
    },
    "South Asian": {
        "breakfast": ["Veggie upma with chutney", "Moong dal cheela with yogurt"],
        "lunch": ["Chana masala with brown rice", "Palak paneer with roti"],
        "dinner": ["Tandoori chicken with raita and salad", "Lentil dal with roasted vegetables"],
        "colors": ["orange", "green", "yellow", "red"]
    },
    "East Asian": {
        "breakfast": ["Congee with vegetables and egg", "Miso soup with tofu and greens"],
        "lunch": ["Teriyaki salmon with bok choy", "Vegetable stir-fry with brown rice"],
        "dinner": ["Grilled fish with seaweed salad", "Chicken and broccoli with quinoa"],
        "colors": ["green", "orange", "white", "red"]
    },
    "Mediterranean": {
        "breakfast": ["Greek yogurt with berries and nuts", "Shakshuka with whole grain bread"],
        "lunch": ["Greek salad with grilled chicken", "Lentil soup with vegetables"],
        "dinner": ["Grilled fish with roasted vegetables", "Chicken souvlaki with tabbouleh"],
        "colors": ["red", "green", "purple", "orange"]
    },
    "West African": {
        "breakfast": ["Millet porridge with fruit", "Bean cakes with pepper sauce"],
        "lunch": ["Jollof rice with grilled chicken", "Groundnut soup with vegetables"],
        "dinner": ["Grilled tilapia with plantain and greens", "Black-eyed pea stew with rice"],
        "colors": ["red", "orange", "green", "yellow"]
    },
    "Italian": {
        "breakfast": ["Frittata with vegetables", "Whole grain toast with tomatoes"],
        "lunch": ["Minestrone soup with beans", "Caprese salad with grilled chicken"],
        "dinner": ["Grilled fish with roasted peppers", "Chicken cacciatore with vegetables"],
        "colors": ["red", "green", "orange", "white"]
    }
}

# Color food backup list (for missing color diversity)
COLOR_FOODS = {
    "red": ["tomatoes", "strawberries", "red bell peppers", "beets", "watermelon"],
    "orange": ["carrots", "sweet potatoes", "oranges", "butternut squash", "papaya"],
    "yellow": ["bananas", "corn", "yellow squash", "pineapple", "lemons"],
    "green": ["spinach", "broccoli", "avocados", "kale", "collard greens"],
    "blue-purple": ["blueberries", "eggplant", "purple cabbage", "blackberries", "plums"],
    "white": ["cauliflower", "onions", "garlic", "mushrooms", "turnips"]
}

# Snack templates: Protein + one other food group
PROTEINS = ["Greek yogurt", "boiled egg", "string cheese", "hummus", "almonds", "peanut butter", "turkey slices"]
SNACK_PARTNERS = ["apple slices", "whole-grain crackers", "carrot sticks", "celery", "berries", "veggie chips", "banana"]

# -----------------------------
# MEAL PLAN GENERATOR
# -----------------------------
def generate_enhanced_meal_plan(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a culturally attuned, rainbow-balanced meal plan with snack logic.
    """
    plan_duration = int(user_profile.get("plan_duration", 3))
    selected_cuisines = user_profile.get("cuisines", ["Mediterranean"])
    health_goal = user_profile.get("health_goal", "general_wellness")
    special_conditions = [s.lower() for s in user_profile.get("special_conditions", [])]

    is_glp1 = "glp" in str(special_conditions)
    is_bariatric = "bariatric" in str(special_conditions)
    is_breastfeeding = "breast" in str(special_conditions)

    primary_cuisine = selected_cuisines[0] if selected_cuisines else "Mediterranean"
    if primary_cuisine not in CUISINE_MEALS:
        primary_cuisine = "Mediterranean"

    meal_plan = []
    total_colors = []

    for day in range(1, plan_duration + 1):
        day_colors = set()
        day_meals = []

        # Breakfast
        breakfast = random.choice(CUISINE_MEALS[primary_cuisine]["breakfast"])
        if is_glp1 or is_bariatric:
            breakfast += " (protein-focused, smaller portion)"
        day_meals.append(f"Breakfast: {breakfast}")

        # Mid-morning snack
        protein = random.choice(PROTEINS)
        partner = random.choice(SNACK_PARTNERS)
        day_meals.append(f"Mid-morning Snack: {protein} + {partner}")

        # Lunch
        lunch = random.choice(CUISINE_MEALS[primary_cuisine]["lunch"])
        if is_glp1 or is_bariatric:
            lunch += " (reduced portion, lean protein priority)"
        day_meals.append(f"Lunch: {lunch}")

        # Mid-afternoon snack
        protein = random.choice(PROTEINS)
        partner = random.choice(SNACK_PARTNERS)
        day_meals.append(f"Mid-afternoon Snack: {protein} + {partner}")

        # Dinner
        dinner = random.choice(CUISINE_MEALS[primary_cuisine]["dinner"])
        if is_glp1 or is_bariatric:
            dinner += " (smaller portion, high-protein focus)"
        day_meals.append(f"Dinner: {dinner}")

        # Color diversity check
        day_colors.update(CUISINE_MEALS[primary_cuisine]["colors"])
        if len(day_colors) < 5:
            missing = [c for c in COLOR_FOODS if c not in day_colors]
            for c in missing[:2]:
                extra = random.choice(COLOR_FOODS[c])
                day_meals.append(f"Snack Boost: add {extra} for extra {c} nutrients")
                day_colors.add(c)

        # Hydration
        hydration = "Drink 10-12 glasses water (extra for breastfeeding)" if is_breastfeeding else "Drink 8-10 glasses water"
        day_meals.append(f"Hydration: {hydration}")

        # Daily nutrition goals
        fiber_goal = "20-25g fiber"
        protein_goal = "80-100g protein" if (is_glp1 or is_bariatric) else "60-80g protein"
        day_meals.append(f"Daily Goals: {fiber_goal}, {protein_goal}")

        meal_plan.append({
            "day": day,
            "meals": day_meals,
            "colors_achieved": len(day_colors),
            "colors": list(day_colors)
        })
        total_colors.append(len(day_colors))

    avg_colors = round(sum(total_colors) / len(total_colors), 1) if total_colors else 0

    return {
        "user_name": user_profile.get("name", "Friend"),
        "health_goal": health_goal,
        "plan_duration": plan_duration,
        "primary_cuisine": primary_cuisine,
        "meal_plan": meal_plan,
        "average_colors_per_day": avg_colors,
        "nutrition_targets": {
            "fiber_daily": fiber_goal,
            "protein_daily": protein_goal,
            "hydration": hydration
        },
        "special_adaptations": {
            "glp1": is_glp1,
            "bariatric": is_bariatric,
            "breastfeeding": is_breastfeeding
        }
    }

# -----------------------------
# RECOMMENDED PDF GUIDES
# -----------------------------
def get_enhanced_recommended_pdfs(user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return relevant wellness guides based on goals and conditions."""
    health_goal = user_profile.get("health_goal", "").lower()
    special_conditions = [s.lower() for s in user_profile.get("special_conditions", [])]
    guides = []

    if "blood pressure" in health_goal:
        guides.append({"title": "Heart Health & Blood Pressure Guide", "description": "DASH-style sodium-smart eating."})
    if "blood sugar" in health_goal or "diabetes" in health_goal:
        guides.append({"title": "Blood Sugar Balance Guide", "description": "Glycemic control through balanced meals."})
    if "weight" in health_goal:
        guides.append({"title": "Sustainable Weight Management", "description": "Evidence-based weight reset strategies."})
    if "digestive" in health_goal or "gut" in health_goal:
        guides.append({"title": "Gut Health & Digestive Wellness", "description": "Fiber-rich, probiotic-friendly foods."})
    if "heart" in health_goal:
        guides.append({"title": "Heart Disease Prevention Guide", "description": "Mediterranean-inspired heart wellness."})
    if "glp" in str(special_conditions):
        guides.append({"title": "GLP-1 Nutrition Guide", "description": "Optimizing nutrition while on GLP-1 therapy."})
    if "bariatric" in str(special_conditions):
        guides.append({"title": "Post-Bariatric Surgery Nutrition", "description": "Protein-first recovery guidelines."})
    if "breast" in str(special_conditions):
        guides.append({"title": "Breastfeeding Nutrition", "description": "Hydration and calorie support for moms."})

    if not guides:
        guides.append({"title": "Eat the Rainbow Wellness Guide", "description": "Color-based eating for lifelong vitality."})
    return guides

# -----------------------------
# FLAVOR BALANCE INDEX
# -----------------------------
def calculate_flavor_balance_index(meal_plan: Dict[str, Any]) -> int:
    """Generate a positive, motivating score based on variety and color diversity."""
    base = random.randint(75, 95)
    if meal_plan.get("plan_duration", 3) > 3:
        base += 3
    color_bonus = int(min(meal_plan.get("average_colors_per_day", 5), 7))
    return min(base + color_bonus, 100)
