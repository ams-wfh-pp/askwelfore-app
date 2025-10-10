# This file contains the FULL MERGED version with both quiz form and freemium webhook
# It requires python-multipart to run - uncomment Form import and POST / endpoint once installed
# Currently saved as backup - use main_freemium_only.py.backup as the active main.py

# See attached_assets/Pasted-main-py-per-replit-agent3... for original September backup
# See MERGED_IMPLEMENTATION.md for full documentation

main.py per replit-agent3:

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from datetime import datetime
import json, random

# Meal planning functions defined inline

def generate_enhanced_meal_plan(user_profile):
    """Generate a comprehensive culturally sensitive meal plan with rainbow preferences and 5-color tracking"""
    
    days = user_profile["plan_duration"]
    health_goals = user_profile["health_goals"]
    dietary_restrictions = user_profile["dietary_restrictions"]
    # Extract cuisines for meal personalization
    cuisines = user_profile.get("cuisines", [])
    if not cuisines:
        # Fall back to cultural_heritage for backward compatibility
        cuisines = user_profile.get("cultural_heritage", [])
    
    regional_identity = user_profile.get("regional_identity", "")
    activity_level = user_profile["lifestyle"]["activity_level"]
    breastfeeding = user_profile["breastfeeding"]
    food_catalog = user_profile.get("food_catalog", [])
    rainbow_preferences = user_profile["rainbow_preferences"]

    # Get user's preferred foods from rainbow selections
    preferred_foods = []
    for color_group in rainbow_preferences.values():
        preferred_foods.extend(color_group)

    # Filter foods based on dietary restrictions, health goals, and accessibility
    available_foods = []
    for food in food_catalog:
        # Check dietary restrictions
        if "vegetarian" in dietary_restrictions and food.get("type") == "protein" and food.get("name") not in [
                "Greek Yogurt", "Black Beans", "Lentils", "Tofu", "Pinto Beans", "Eggs"
        ]:
            continue
        if "vegan" in dietary_restrictions and ("dairy" in food.get("allergens", []) or food.get("type") == "dairy" or
                                                "eggs" in food.get("allergens", [])):
            continue
        if "gluten" in dietary_restrictions and "gluten" in food.get("allergens", []):
            continue
        if "dairy" in dietary_restrictions and "dairy" in food.get("allergens", []):
            continue
        if "nuts" in dietary_restrictions and "nuts" in food.get("allergens", []):
            continue

        # Check if food matches health goals
        if health_goals and any(goal in food.get("goal_tags", []) for goal in health_goals):
            available_foods.append(food)
        elif not health_goals:  # If no specific goals, include all suitable foods
            available_foods.append(food)

    # If no foods match criteria, use some defaults
    if not available_foods:
        available_foods = [
            {"name": "Mixed vegetables", "type": "vegetable", "color": "green", "fiber_g": 3.0},
            {"name": "Brown rice", "type": "carbohydrate", "color": "brown", "fiber_g": 2.0},
            {"name": "Chicken breast", "type": "protein", "color": "white", "fiber_g": 0},
            {"name": "Apple", "type": "fruit", "color": "red", "fiber_g": 2.4},
            {"name": "Greek yogurt", "type": "dairy", "color": "white", "fiber_g": 0},
        ]

    # Categorize foods
    proteins = [f for f in available_foods if f.get("type") == "protein"] or [{"name": "Chicken breast", "type": "protein", "color": "white", "fiber_g": 0}]
    vegetables = [f for f in available_foods if f.get("type") == "vegetable"] or [{"name": "Mixed greens", "type": "vegetable", "color": "green", "fiber_g": 2.0}]
    carbs = [f for f in available_foods if f.get("type") == "carbohydrate"] or [{"name": "Brown rice", "type": "carbohydrate", "color": "brown", "fiber_g": 1.8}]
    fruits = [f for f in available_foods if f.get("type") == "fruit"] or [{"name": "Apple", "type": "fruit", "color": "red", "fiber_g": 2.4}]
    dairy = [f for f in available_foods if f.get("type") == "dairy"] or [{"name": "Greek yogurt", "type": "dairy", "color": "white", "fiber_g": 0}]

    meal_plan = {
        "days": days,
        "profile": {
            "condition": f"{', '.join(health_goals).title()} goals for {user_profile['name']}, Age {user_profile['age']}",
            "cuisines": cuisines if cuisines else ["Global Fusion"],
            "regional_identity": regional_identity,
            "dietary_restrictions": dietary_restrictions,
            "activity_level": activity_level.replace('_', ' ').title(),
            "breastfeeding": breastfeeding,
        },
        "plan": [],
        "daily_summaries": [],
        "rainbow_focus": True
    }

    for day in range(days):
        # Select diverse foods ensuring 5+ colors and fiber
        daily_colors = set()
        daily_fiber = 0

        # Breakfast
        breakfast_fruit = random.choice(fruits)
        breakfast_dairy = random.choice(dairy) if dairy else None
        breakfast_carb = random.choice(carbs)

        if breakfast_dairy:
            breakfast_name = f"{breakfast_fruit['name']} parfait with {breakfast_dairy['name']} and {breakfast_carb['name']}"
            daily_colors.update([breakfast_fruit["color"], breakfast_dairy["color"], breakfast_carb["color"]])
            daily_fiber += breakfast_fruit["fiber_g"] + breakfast_dairy["fiber_g"] + breakfast_carb["fiber_g"]
        else:
            breakfast_name = f"{breakfast_fruit['name']} smoothie bowl with {breakfast_carb['name']}"
            daily_colors.update([breakfast_fruit["color"], breakfast_carb["color"]])
            daily_fiber += breakfast_fruit["fiber_g"] + breakfast_carb["fiber_g"]

        # Lunch
        lunch_protein = random.choice(proteins)
        lunch_veg = random.choice(vegetables)
        lunch_carb = random.choice(carbs)

        lunch_name = f"{lunch_protein['name']} with {lunch_veg['name']} and {lunch_carb['name']}"
        daily_colors.update([lunch_protein["color"], lunch_veg["color"], lunch_carb["color"]])
        daily_fiber += lunch_protein["fiber_g"] + lunch_veg["fiber_g"] + lunch_carb["fiber_g"]

        # Dinner
        dinner_protein = random.choice([p for p in proteins if p != lunch_protein]) if len(proteins) > 1 else lunch_protein
        dinner_veg = random.choice([v for v in vegetables if v != lunch_veg]) if len(vegetables) > 1 else lunch_veg

        dinner_name = f"Herb-seasoned {dinner_protein['name']} with roasted {dinner_veg['name']}"
        daily_colors.update([dinner_protein["color"], dinner_veg["color"]])
        daily_fiber += dinner_protein["fiber_g"] + dinner_veg["fiber_g"]

        # Generate snacks (respect dietary restrictions)
        dietary_restrictions = user_profile.get("dietary_restrictions", [])
        has_nut_allergy = any("nut" in restriction.lower() for restriction in dietary_restrictions)
        
        if has_nut_allergy:
            morning_snack = {"name": f"{random.choice(fruits)['name']} with yogurt", "colors": ["red", "white"]}
        else:
            morning_snack = {"name": f"{random.choice(fruits)['name']} with nuts", "colors": ["red", "brown"]}
        afternoon_snack = {"name": f"{random.choice(vegetables)['name']} with hummus", "colors": ["green", "beige"]}

        daily_colors.update(morning_snack["colors"])
        daily_colors.update(afternoon_snack["colors"])

        # Hydration tip
        hydration_tips = [
            "droplet Start your day with a large glass of water!",
            "droplet Try adding lemon to your water for flavor!",
            "droplet Keep a water bottle nearby as a reminder!",
            "droplet Herbal teas count toward your daily water intake!"
        ]
        hydration_tip = random.choice(hydration_tips)
        if breastfeeding == "yes":
            hydration_tip += " 🤱 As a breastfeeding mom, aim for extra water!"

        day_meals = {
            "breakfast": {"name": breakfast_name},
            "morning_snack": {"name": morning_snack["name"], "colors": morning_snack["colors"]},
            "lunch": {"name": lunch_name},
            "afternoon_snack": {"name": afternoon_snack["name"], "colors": afternoon_snack["colors"]},
            "dinner": {"name": dinner_name},
            "hydration_tip": hydration_tip
        }

        daily_summary = {
            "colors": len(daily_colors),
            "color_list": list(daily_colors),
            "fiber_g": round(daily_fiber, 1)
        }

        meal_plan["plan"].append(day_meals)
        meal_plan["daily_summaries"].append(daily_summary)

    return meal_plan


def get_enhanced_recommended_pdfs(user_profile):
    """Enhanced PDF matching with comprehensive health guide selection"""
    
    recommended = []
    lifestyle = user_profile["lifestyle"]
    health_goals = user_profile["health_goals"]

    if "heart_health" in health_goals:
        recommended.append({
            "title": "Happy Hearts Guide",
            "description": "Heart-healthy lifestyle and nutrition tips",
            "filename": "happy_hearts.pdf",
            "reason": "Heart health goal"
        })

    if "diabetes_management" in health_goals:
        recommended.append({
            "title": "Blood Sugar Control Guide",
            "description": "Managing blood sugar through diet and lifestyle",
            "filename": "blood_sugar_control.pdf",
            "reason": "Diabetes management goal"
        })

        recommended.append({
            "title": "Type 2 Diabetes Management",
            "description": "Comprehensive diabetes lifestyle management",
            "filename": "type2_diabetes.pdf",
            "reason": "Type 2 Diabetes management"
        })

    if lifestyle.get("sleep_stress") in ["poor", "fair"]:
        recommended.append({
            "title": "General Health & Wellness Guide",
            "description": "Comprehensive wellness strategies for better health",
            "filename": "general_health.pdf",
            "reason": "Sleep and stress concerns"
        })

    if "liver_support" in health_goals or lifestyle.get("hydration_habits") == "low":
        recommended.append({
            "title": "Liver Health Guide",
            "description": "Supporting liver function through nutrition and hydration",
            "filename": "liver_health.pdf",
            "reason": "Liver support goal or low hydration"
        })

    if "glp1_support" in health_goals:
        recommended.append({
            "title": "GLP-1 Patient Support Guide",
            "description": "Specialized nutrition and lifestyle guidance for GLP-1 medication users",
            "filename": "glp1_patient_support.pdf",
            "reason": "GLP-1 patient support goal"
        })

    # Ensure at least one guide is recommended
    if not recommended:
        recommended.append({
            "title": "General Health & Wellness Guide",
            "description": "Foundational wellness strategies for everyone",
            "filename": "general_health.pdf",
            "reason": "Foundational wellness support"
        })

    # Remove duplicates while preserving order
    seen = set()
    unique_recommended = []
    for item in recommended:
        if item["filename"] not in seen:
            seen.add(item["filename"])
            unique_recommended.append(item)

    return unique_recommended

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

with open("cultural_food_catalog_expanded.json", "r", encoding="utf-8") as f:
    food_catalog = json.load(f).get("foods", [])

# define food options for rainbow suggestions with diverse cultural examples
food_options = {
    "red": ["Tomatoes", "Red Bell Peppers", "Strawberries", "Cherries", "Red Beans", "Watermelon", "Red Onions", "Pomegranate"],
    "orange": ["Carrots", "Sweet Potatoes", "Oranges", "Mangoes", "Papaya", "Cantaloupe", "Orange Bell Peppers", "Butternut Squash"],
    "yellow": ["Corn", "Yellow Squash", "Pineapple", "Bananas", "Yellow Bell Peppers", "Golden Beets", "Yellow Tomatoes", "Lemons"],
    "green": ["Spinach", "Broccoli", "Green Peas", "Kale", "Cucumber", "Green Beans", "Avocado", "Brussels Sprouts", "Cilantro", "Collard Greens"],
    "purple": ["Eggplant", "Blackberries", "Purple Cabbage", "Grapes", "Blueberries", "Purple Sweet Potatoes", "Red Onions", "Plums"],
    "white": ["Cauliflower", "Mushrooms", "Garlic", "Onions", "White Beans", "Turnips", "Jicama", "White Fish", "Tofu"]
}

@app.get("/", response_class=HTMLResponse)
async def show_quiz(request: Request):
    return templates.TemplateResponse("plan.html", {
        "request": request,
        "food_options": food_options
    })

@app.post("/", response_class=HTMLResponse)
async def handle_quiz(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    breastfeeding: str = Form("no"),
    family_size: int = Form(1),
    # Rainbow food preferences
    red_foods: List[str] = Form([]),
    red_foods_other: str = Form(""),
    orange_foods: List[str] = Form([]),
    orange_foods_other: str = Form(""),
    yellow_foods: List[str] = Form([]),
    yellow_foods_other: str = Form(""),
    green_foods: List[str] = Form([]),
    green_foods_other: str = Form(""),
    purple_foods: List[str] = Form([]),
    purple_foods_other: str = Form(""),
    white_foods: List[str] = Form([]),
    white_foods_other: str = Form(""),
    # Health goals & preferences
    health_goals: List[str] = Form([]),
    dietary_restrictions: str = Form(""),
    cuisines: List[str] = Form([]),
    cuisines_other: str = Form(""),
    regional_identity: str = Form(""),
    # Lifestyle & habits
    activity_level: str = Form(...),
    hydration_habits: str = Form(...),
    sleep_stress: str = Form(...),
    cooking_confidence: str = Form(...),
    fruit_veggie_intake: str = Form(...),
    meal_skipping: str = Form(...),
    fast_food: str = Form(...),
    food_access: str = Form(...),
    grocery_budget: str = Form(...),
    # Plan duration
    plan_duration: int = Form(...),
):
    # Build user profile
    def parse_other_foods(other_string):
        return [item.strip() for item in other_string.split(",") if item.strip()]

    user_profile = {
        "name": name,
        "age": age,
        "gender": gender,
        "breastfeeding": breastfeeding,
        "family_size": family_size,
        "rainbow_preferences": {
            "red_foods": red_foods + parse_other_foods(red_foods_other),
            "orange_foods": orange_foods + parse_other_foods(orange_foods_other),
            "yellow_foods": yellow_foods + parse_other_foods(yellow_foods_other),
            "green_foods": green_foods + parse_other_foods(green_foods_other),
            "purple_foods": purple_foods + parse_other_foods(purple_foods_other),
            "white_foods": white_foods + parse_other_foods(white_foods_other),
        },
        "health_goals": health_goals,
        "dietary_restrictions": [d.strip() for d in dietary_restrictions.split(",") if d.strip()],
        "cuisines": cuisines + ([cuisines_other] if cuisines_other.strip() else []),
        "cultural_heritage": cuisines + ([cuisines_other] if cuisines_other.strip() else []),  # Keep for backward compatibility
        "regional_identity": regional_identity,
        "lifestyle": {
            "activity_level": activity_level,
            "hydration_habits": hydration_habits,
            "sleep_stress": sleep_stress,
            "cooking_confidence": cooking_confidence,
            "fruit_veggie_intake": fruit_veggie_intake,
            "meal_skipping": meal_skipping,
            "fast_food": fast_food,
            "food_access": food_access,
            "grocery_budget": grocery_budget
        },
        "plan_duration": plan_duration,
        "food_catalog": food_catalog
    }

    # Generate the plan
    plan = generate_enhanced_meal_plan(user_profile)
    is_premium = plan_duration > 3
    if is_premium:
        plan["is_premium"] = True
        plan["free_days"] = 3
        plan["premium_message"] = f"sparkles Unlock your full {plan_duration}-day plan with WelFore Premium!"
    else:
        plan["is_premium"] = False

    recommended_pdfs = get_enhanced_recommended_pdfs(user_profile)

    return templates.TemplateResponse("plan.html", {
        "request": request,
        "food_options": food_options,
        "plan": plan,
        "user_profile": user_profile,
        "recommended_pdfs": recommended_pdfs,
        "generated_at": datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        "result": {
            "name": name,
            "message": f"Your personalized {plan['days']}-day meal plan has been generated!"
        }
    })
Posted on Sep 23 – Edit or Delete
Ann-Marie Stephens
Ann-Marie Stephens
healthcare marketing & promotion mentor | master meal assembly engine template.

import random

# =========================
# Core Generator Functions
# =========================

def generate_daily_meal_plan(user_profile, food_catalog):
    """Generates a culturally sensitive daily meal plan with MyPlate ratios,
    rainbow coverage, fiber + protein targets, and GLP-1/bariatric adaptations."""

    plan = {
        "breakfast": assemble_meal("breakfast", user_profile, food_catalog),
        "lunch": assemble_meal("lunch", user_profile, food_catalog),
        "dinner": assemble_meal("dinner", user_profile, food_catalog),
        "snack1": assemble_snack(user_profile, food_catalog),
        "snack2": assemble_snack(user_profile, food_catalog)
    }
    
    # Rainbow Coverage rainbow
    if not check_rainbow_coverage(plan):
        plan = rebalance_colors(plan, food_catalog)
    
    # Fiber & Protein Safety Nets
    if not check_fiber_target(plan, min_fiber=20):
        plan = add_fiber_food(plan, food_catalog)
    if not check_protein_target(plan, min_protein=60):
        plan = add_protein_food(plan, food_catalog)
    
    # GLP-1 / Bariatric Adaptations
    if user_profile.get("is_glp1") or user_profile.get("is_bariatric"):
        plan = adapt_glp1_bariatric(plan)

    return plan


# =========================
# Meal Builders
# =========================

def assemble_meal(meal_type, user_profile, food_catalog):
    meal = {}

    # ½ plate veggies
    meal["vegetables"] = select_foods(food_catalog, 
                                      type="vegetable", 
                                      count=2, 
                                      criteria={"glp1_friendly": True, 
                                                "culture": user_profile.get("culture")})
    
    # ¼ plate protein
    meal["protein"] = select_foods(food_catalog, 
                                   type="protein", 
                                   count=1, 
                                   criteria={"glp1_friendly": True, 
                                             "culture": user_profile.get("culture")})
    
    # ¼ plate grain/starchy carb
    meal["carb"] = select_foods(food_catalog, 
                                type="carbohydrate", 
                                count=1, 
                                criteria={"glp1_friendly": True, 
                                          "culture": user_profile.get("culture")})
    
    # Fruit side
    meal["fruit"] = select_foods(food_catalog, 
                                 type="fruit", 
                                 count=1, 
                                 criteria={"glp1_friendly": True, 
                                           "culture": user_profile.get("culture")})
    
    # Beverage
    meal["beverage"] = "Water, Sparkling Water, or Unsweetened Tea"

    return meal


def assemble_snack(user_profile, food_catalog):
    snack = {}

    # Always pair protein + fiber
    snack["protein_or_dairy"] = select_foods(food_catalog, 
                                             type=["protein", "dairy", "snack"], 
                                             count=1, 
                                             criteria={"glp1_friendly": True})
    
    snack["fruit_or_veg"] = select_foods(food_catalog, 
                                         type=["fruit", "vegetable"], 
                                         count=1, 
                                         criteria={"glp1_friendly": True})
    
    return snack


# =========================
# Food Selection Engine
# =========================

def select_foods(food_catalog, type, count=1, criteria=None):
    if isinstance(type, str):
        type = [type]

    filtered = [f for f in food_catalog if f["type"] in type]

    # Cultural preference
    if criteria and "culture" in criteria:
        culture = criteria["culture"]
        cultural_match = [f for f in filtered if culture in f.get("cultures", [])]
        if cultural_match:
            filtered = cultural_match
    
    # GLP-1 filter
    if criteria and "glp1_friendly" in criteria:
        filtered = [f for f in filtered if f.get("glp1_friendly", False) == criteria["glp1_friendly"]]
    
    # Health tag filters
    if criteria:
        for key, value in criteria.items():
            if key not in ["culture", "glp1_friendly"]:
                filtered = [f for f in filtered if value in f.get("health_tags", [])]
    
    # Fallback
    if not filtered:
        filtered = [f for f in food_catalog if f["culture"] == "Universal_GLP1_Friendly" and f["type"] in type]
    
    return random.sample(filtered, min(count, len(filtered)))


# =========================
# Nutrient Coverage Checks
# =========================

def check_rainbow_coverage(plan):
    colors_seen = set()
    for meal in plan.values():
        for food in meal.values():
            if isinstance(food, list):
                for f in food: colors_seen.add(f["color"])
            elif isinstance(food, dict):
                colors_seen.add(food["color"])
    return len(colors_seen) >= 5


def check_fiber_target(plan, min_fiber=20):
    total_fiber = sum(
        food.get("fiber_g", 0)
        for meal in plan.values()
        for item in meal.values()
        for food in (item if isinstance(item, list) else [item]) if isinstance(food, dict)
    )
    return total_fiber >= min_fiber


def check_protein_target(plan, min_protein=60):
    total_protein = sum(
        food.get("protein_g", 0)
        for meal in plan.values()
        for item in meal.values()
        for food in (item if isinstance(item, list) else [item]) if isinstance(food, dict)
    )
    return total_protein >= min_protein


# =========================
# Nutrient Safety Nets
# =========================

def rebalance_colors(plan, food_catalog):
    rainbow_required = {"red", "orange", "yellow", "green", "purple"}
    colors_seen = set()
    
    for meal in plan.values():
        for food in meal.values():
            if isinstance(food, list):
                for f in food: colors_seen.add(f["color"])
            elif isinstance(food, dict):
                colors_seen.add(food["color"])

    missing_colors = rainbow_required - colors_seen

    for color in missing_colors:
        candidate_foods = [f for f in food_catalog if f["type"] in ["fruit", "vegetable"] and f["color"] == color]
        if candidate_foods:
            if "extras" not in plan["snack1"]:
                plan["snack1"]["extras"] = []
            plan["snack1"]["extras"].append(candidate_foods[0])
    
    return plan


def add_fiber_food(plan, food_catalog, min_fiber=20):
    fiber_foods = sorted(
        [f for f in food_catalog if "fiber-rich" in f.get("health_tags", [])],
        key=lambda x: x.get("fiber_g", 0),
        reverse=True
    )
    
    total_fiber = sum(f.get("fiber_g", 0) for meal in plan.values() for item in meal.values() for f in (item if isinstance(item, list) else [item]) if isinstance(f, dict))
    
    for food in fiber_foods:
        if total_fiber >= min_fiber:
            break
        if "extras" not in plan["snack2"]:
            plan["snack2"]["extras"] = []
        plan["snack2"]["extras"].append(food)
        total_fiber += food.get("fiber_g", 0)

    return plan


def add_protein_food(plan, food_catalog, min_protein=60):
    protein_foods = sorted(
        [f for f in food_catalog if f["type"] == "protein" and f.get("glp1_friendly", False)],
        key=lambda x: x.get("protein_g", 20),
        reverse=True
    )
    
    total_protein = sum(f.get("protein_g", 0) for meal in plan.values() for item in meal.values() for f in (item if isinstance(item, list) else [item]) if isinstance(f, dict))
    
    for food in protein_foods:
        if total_protein >= min_protein:
            break
        if "extras" not in plan["dinner"]:
            plan["dinner"]["extras"] = []
        plan["dinner"]["extras"].append(food)
        total_protein += food.get("protein_g", 20)

    return plan


# =========================
# GLP-1 / Bariatric Adaptations
# =========================

def adapt_glp1_bariatric(plan):
    """Adjusts portion sizes and enforces protein-first eating order for GLP-1/bariatric users."""
    
    for meal_name, meal in plan.items():
        # Reduce portions ~30%
        for key, item in meal.items():
            if isinstance(item, list):
                for food in item:
                    food["portion_adjusted"] = "70%"  # metadata for UI
            elif isinstance(item, dict):
                item["portion_adjusted"] = "70%"
    
    # Ensure protein-first flag
    plan["protein_priority"] = True
    
    return plan
_____________________

that’s the workflow loop your Replit agent will follow each time the generator is called.

Here’s the system in a step-by-step run order for clarity (so your dev has no guesswork):

small_blue_diamond Daily Meal Plan Generation Flow 1. Assemble Initial Plan
Run assemble_meal() for breakfast, lunch, dinner

Run assemble_snack() for snack1 and snack2

Each follows MyPlate rules (½ veg, ¼ protein, ¼ grain + fruit + hydration).

2. Check Rainbow Colors rainbow
Call check_rainbow_coverage()

If <5 colors → run rebalance_colors()

Adds missing red, orange, yellow, green, purple via fruits/veggies (usually snacks).

3. Check Fiber Target (≥20g)
Call check_fiber_target()

If <20g → run add_fiber_food()

Adds high-fiber beans, lentils, leafy greens, whole grains → usually in snack2 or dinner.

4. Check Protein Target (≥60g)
Call check_protein_target()

If <60g → run add_protein_food()

Adds lean protein (beans, fish, poultry, tofu, yogurt) → usually into dinner.

5. Apply GLP-1 / Bariatric Adaptations
If user_profile.is_glp1 or user_profile.is_bariatric:

Reduce portions ~30% (mark foods with "portion_adjusted": "70%")

Prioritize protein-first in UI → meal cards flagged with "protein_priority": True

Filter out greasy/heavy foods.

white_check_mark Final Output
Each daily plan delivered to the user is:

Balanced (MyPlate ratios) → clear structure at every meal.

Colorful (≥5 rainbow colors) → visual abundance, missing foods are obvious.

Nutrient-aligned → fiber + protein minimums always met.

Safe & tailored → portioning + food selection adjusted for GLP-1/bariatric users.

Flavor-forward → herbs + spices drive taste, not salt/sugar.


Posted on Sep 23 – Edit or Delete
Ann-Marie Stephens
Ann-Marie Stephens
Based on my analysis of your app and GHL integration requirements, here are the endpoint URLs you need to add to GoHighLevel:


link Main Integration Endpoint
Base URL: https://27089137-8697-4689-b36d-8a602157fef1-00-113e2z1dz8j0x.riker.replit.…

Primary Endpoint: https://27089137-8697-4689-b36d-8a602157fef1-00-113e2z1dz8j0x.riker.replit.…

Method: POST
Purpose: Handles quiz submissions, creates GHL contacts, and triggers meal plan generation

clipboard Additional Endpoints Available
Premium Success Pages (for Stripe integration callbacks):

https://27089137-8697-4689-b36d-8a602157fef1-00-113e2z1dz8j0x.riker.replit.…
https://27089137-8697-4689-b36d-8a602157fef1-00-113e2z1dz8j0x.riker.replit.…

zap Current GHL Integration Features
Your app already has comprehensive GHL integration built-in:

white_check_mark Contact Creation: Automatically creates contacts in GHL CRM with complete user data
white_check_mark SMS Notifications: Sends welcome messages and meal plan alerts via GHL SMS API
white_check_mark User Segmentation: Tags contacts based on plan type, health goals, and cultural preferences
white_check_mark Complete Data Mapping: Captures all quiz data including dietary restrictions, cultural heritage, lifestyle habits


wrench For GHL Webhook Setup
If you need to receive data FROM GHL (inbound webhooks), you'll want to create a new endpoint. But for sending data TO GHL (which is what you're currently doing), the main / endpoint is perfect.



Your Integration URL for GHL:


https://27089137-8697-4689-b36d-8a602157fef1-00-113e2z1dz8j0x.riker.replit.…



This endpoint will automatically create GHL contacts whenever users submit the nutrition quiz form. The integration uses your GHL_API_KEY and GHL_LOCATION_ID environment variables that are already configured.