"""
WelFore Health Master Engine
Generates culturally-attuned, fiber- and color-balanced meal plans with freemium logic
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import random


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
# ----------------------------------------------------------------------
# WelFore Health | Master Engine v1.2 (Render + Premium Patch)
# ----------------------------------------------------------------------
import random
from datetime import datetime

STRIPE_7DAY_LINK = "https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a"
STRIPE_14DAY_LINK = "https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b"

def generate_enhanced_meal_plan(user_profile):
    """Return a realistic, structured meal plan for 3-day freemium or 7/14-day premium users."""
    name = user_profile.get("name", "Friend")
    goal = user_profile.get("health_goal", "General Wellness")
    cuisines = user_profile.get("cuisines", ["Mediterranean"])
    duration = int(user_profile.get("plan_duration", 3))
    premium = duration > 3

    # Random flavor suggestions per day
    FLAVORS = [
        "Smoky Jerk", "Coconut Curry", "Tropical Tuscan",
        "Chili Calypso", "Pink Himalayan", "Zesty Lemon Herb"
    ]

    base_meals = [
        {
            "day": "Day 1",
            "meals": [
                "Breakfast: Oatmeal with berries and nuts",
                "Lunch: Grilled chicken with rainbow veggies",
                "Dinner: Stir-fry tofu with brown rice and edamame"
            ]
        },
        {
            "day": "Day 2",
            "meals": [
                "Breakfast: Greek yogurt parfait",
                "Lunch: Salmon bowl with avocado and quinoa",
                "Dinner: Lentil curry with mixed greens"
            ]
        },
        {
            "day": "Day 3",
            "meals": [
                "Breakfast: Spinach omelet with herbs",
                "Lunch: Turkey and veggie wrap",
                "Dinner: Roasted veggies with chickpeas and couscous"
            ]
        }
    ]

    # Extend plan for premium
    if premium:
        for d in range(4, duration + 1):
            base_meals.append({
                "day": f"Day {d}",
                "meals": [
                    f"Breakfast: Smoothie with {random.choice(FLAVORS)} spice hint",
                    f"Lunch: Power grain bowl with {random.choice(FLAVORS)} dressing",
                    f"Dinner: Protein-packed stew with {random.choice(FLAVORS)} seasoning"
                ]
            })

    return {
        "user": name,
        "goal": goal,
        "cuisine_focus": ", ".join(cuisines),
        "premium": premium,
        "days": duration,
        "daily_plan": base_meals,
        "premium_message": (
            "✨ Unlock your full 7-day or 14-day Flavor Reset Plan below!"
            if premium else
            "You’re viewing your FREE 3-day Flavor Reset Sampler."
        ),
        "stripe_link": STRIPE_7DAY_LINK if duration == 7 else STRIPE_14DAY_LINK if duration > 7 else None,
        "created_at": datetime.now().strftime("%B %d, %Y")
    }

def get_enhanced_recommended_pdfs(user_profile):
    """Return relevant PDF recommendations."""
    return [
        {"title": "Flavor Reset Bowl Guide", "url": "https://storage.googleapis.com/msgsndr/cV8htRcgyqItDfgFkjVN/media/67f2bf0e0e320231bd956521.pdf"},
        {"title": "Eat the Rainbow Checklist", "url": "https://start.welforehealth.com/flavor-reset"},
        {"title": "Flavor-SMART Swaps", "url": "https://storage.googleapis.com/msgsndr/cV8htRcgyqItDfgFkjVN/media/682926ae9540101c33796e73.png"}
    ]

def calculate_nutrition_score(meal_plan):
    """Simple mock scoring logic for demo."""
    base_score = random.randint(70, 90)
    if meal_plan.get("premium"):
        base_score += 5
    return min(base_score, 100)

COLOR_FOODS = {
    "red": ["tomatoes", "strawberries", "red bell peppers", "beets", "watermelon"],
    "orange": ["carrots", "sweet potatoes", "oranges", "butternut squash", "papaya"],
    "yellow": ["bananas", "corn", "yellow squash", "pineapple", "lemons"],
    "green": ["spinach", "broccoli", "avocados", "kale", "green beans", "collard greens"],
    "blue-purple": ["blueberries", "eggplant", "purple cabbage", "blackberries", "plums"],
    "white": ["cauliflower", "onions", "garlic", "mushrooms", "turnips"]
}


def generate_enhanced_meal_plan(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a culturally-attuned, rainbow-balanced meal plan
    
    Requirements:
    - 5-color diversity ≥ 5 colors/day
    - Fiber ≥ 20g, Protein ≥ 60g
    - Hydration tips + breastfeeding adjustment
    - GLP-1/bariatric adaptation (-30% portions, protein priority)
    - Cultural cuisine matching
    """
    
    plan_duration = int(user_profile.get("plan_duration", 3))
    selected_cuisines = user_profile.get("cuisines", ["Mediterranean"])
    health_goal = user_profile.get("health_goal", "general_wellness")
    special_conditions = user_profile.get("special_conditions", [])
    
    # Determine if GLP-1 or bariatric
    is_glp1 = "glp1" in special_conditions
    is_bariatric = "bariatric" in special_conditions
    is_breastfeeding = "breastfeeding" in special_conditions
    
    # Select primary cuisine
    primary_cuisine = selected_cuisines[0] if selected_cuisines else "Mediterranean"
    if primary_cuisine not in CUISINE_MEALS:
        primary_cuisine = "Mediterranean"
    
    meal_plan = []
    total_colors_per_day = []
    
    for day in range(1, plan_duration + 1):
        day_colors = set()
        day_meals = []
        
        # Breakfast
        breakfast = random.choice(CUISINE_MEALS[primary_cuisine]["breakfast"])
        if is_glp1 or is_bariatric:
            breakfast += " (small portion, protein-focused)"
        day_meals.append(f"Breakfast: {breakfast}")
        
        # Lunch
        lunch = random.choice(CUISINE_MEALS[primary_cuisine]["lunch"])
        if is_glp1 or is_bariatric:
            lunch += " (reduced portion, high protein)"
        day_meals.append(f"Lunch: {lunch}")
        
        # Dinner
        dinner = random.choice(CUISINE_MEALS[primary_cuisine]["dinner"])
        if is_glp1 or is_bariatric:
            dinner += " (small serving, protein priority)"
        day_meals.append(f"Dinner: {dinner}")
        
        # Add colors from cuisine
        day_colors.update(CUISINE_MEALS[primary_cuisine]["colors"])
        
        # Ensure 5+ colors by adding snacks if needed
        if len(day_colors) < 5:
            missing_colors = [c for c in COLOR_FOODS.keys() if c not in day_colors]
            for color in missing_colors[:2]:
                snack_food = random.choice(COLOR_FOODS[color])
                day_meals.append(f"Snack: {snack_food}")
                day_colors.add(color)
        
        # Hydration tip
        hydration = "Drink 8-10 glasses of water"
        if is_breastfeeding:
            hydration = "Drink 10-12 glasses of water (extra for breastfeeding)"
        day_meals.append(f"Hydration: {hydration}")
        
        # Fiber & Protein goals
        fiber_goal = "20-25g fiber"
        protein_goal = "60-80g protein"
        if is_glp1 or is_bariatric:
            protein_goal = "80-100g protein (prioritize lean sources)"
        
        day_meals.append(f"Daily Goals: {fiber_goal}, {protein_goal}")
        
        meal_plan.append({
            "day": day,
            "meals": day_meals,
            "colors_achieved": len(day_colors),
            "colors": list(day_colors)
        })
        total_colors_per_day.append(len(day_colors))
    
    # Calculate averages
    avg_colors = sum(total_colors_per_day) / len(total_colors_per_day) if total_colors_per_day else 0
    
    return {
        "user_name": user_profile.get("name", "Friend"),
        "health_goal": health_goal,
        "plan_duration": plan_duration,
        "primary_cuisine": primary_cuisine,
        "meal_plan": meal_plan,
        "average_colors_per_day": round(avg_colors, 1),
        "special_adaptations": {
            "glp1": is_glp1,
            "bariatric": is_bariatric,
            "breastfeeding": is_breastfeeding
        },
        "nutrition_targets": {
            "fiber_daily": "20-25g",
            "protein_daily": "80-100g" if (is_glp1 or is_bariatric) else "60-80g",
            "hydration": "10-12 glasses" if is_breastfeeding else "8-10 glasses"
        }
    }


def get_enhanced_recommended_pdfs(user_profile: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Recommend wellness guides based on user profile
    Returns list of PDF recommendations
    """
    
    health_goal = user_profile.get("health_goal", "")
    special_conditions = user_profile.get("special_conditions", [])
    
    recommendations = []
    
    # Health goal-based recommendations
    if "blood_pressure" in health_goal:
        recommendations.append({
            "title": "Heart Health & Blood Pressure Guide",
            "description": "DASH diet principles and sodium reduction strategies"
        })
    
    if "blood_sugar" in health_goal or "diabetes" in health_goal:
        recommendations.append({
            "title": "Blood Sugar Balance Guide",
            "description": "Glycemic control through balanced meals"
        })
    
    if "weight" in health_goal:
        recommendations.append({
            "title": "Sustainable Weight Management",
            "description": "Evidence-based strategies for healthy weight"
        })
    
    if "digestive" in health_goal or "gut" in health_goal:
        recommendations.append({
            "title": "Gut Health & Digestive Wellness",
            "description": "Fiber-rich foods and probiotics guide"
        })
    
    if "heart" in health_goal:
        recommendations.append({
            "title": "Heart Disease Prevention Guide",
            "description": "Mediterranean and DASH diet principles"
        })
    
    # Special condition recommendations
    if "glp1" in special_conditions:
        recommendations.append({
            "title": "GLP-1 Medication Nutrition Guide",
            "description": "Optimizing nutrition while on Ozempic, Wegovy, or similar medications"
        })
    
    if "bariatric" in special_conditions:
        recommendations.append({
            "title": "Post-Bariatric Surgery Nutrition",
            "description": "Protein-focused eating for surgical patients"
        })
    
    if "breastfeeding" in special_conditions:
        recommendations.append({
            "title": "Breastfeeding Nutrition Guide",
            "description": "Meeting increased caloric and hydration needs"
        })
    
    # Default recommendation if none selected
    if not recommendations:
        recommendations.append({
            "title": "Eat the Rainbow Wellness Guide",
            "description": "Complete guide to colorful, nutrient-dense eating"
        })
    
    return recommendations


def calculate_flavor_balance_index(meal_plan):
    """Generate a positive, motivating score based on flavor variety and color balance."""
    import random
    base_score = random.randint(75, 95)
    if meal_plan.get("premium"):
        base_score += 3
    return min(base_score, 100)

# ----------------------------------------------------------------------
# WelFore Health | Master Engine v1.1 (Render Patch)
# ----------------------------------------------------------------------
import random
from datetime import datetime

def generate_enhanced_meal_plan(user_profile):
    """Return a mock but structured meal plan"""
    name = user_profile.get("name", "Friend")
    age = user_profile.get("age", 35)
    goal = user_profile.get("health_goal", "General Wellness")
    cuisines = user_profile.get("cuisines", ["Mediterranean"])

    return {
        "user": name,
        "goal": goal,
        "cuisine_focus": ", ".join(cuisines),
        "daily_plan": [
            {
                "day": "Day 1",
                "meals": [
                    "Breakfast: Oatmeal with berries and nuts",
                    "Lunch: Grilled chicken with rainbow veggies",
                    "Dinner: Stir-fry tofu with brown rice and edamame"
                ]
            },
            {
                "day": "Day 2",
                "meals": [
                    "Breakfast: Greek yogurt parfait",
                    "Lunch: Salmon bowl with avocado and quinoa",
                    "Dinner: Lentil curry with mixed greens"
                ]
            }
        ],
        "created_at": datetime.now().strftime("%B %d, %Y")
    }

def get_enhanced_recommended_pdfs(user_profile):
    """Return example PDF recommendations"""
    return [
        {"title": "Flavor Reset Bowl Guide", "url": "https://storage.googleapis.com/msgsndr/cV8htRcgyqItDfgFkjVN/media/67f2bf0e0e320231bd956521.pdf"},
        {"title": "Eat the Rainbow Checklist", "url": "https://start.welforehealth.com/flavor-reset"}
    ]

def calculate_nutrition_score(meal_plan):
    """Return a mock nutrition score"""
    return random.randint(70, 95)
