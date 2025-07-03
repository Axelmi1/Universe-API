from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from app.services.ia_client import ask_llm
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()

class GenderEnum(str, Enum):
    MALE = "M"
    FEMALE = "F"

class ActivityLevelEnum(str, Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

class NutritionGoalEnum(str, Enum):
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    GENERAL_HEALTH = "general_health"

class DietaryRestrictionsEnum(str, Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    KETO = "keto"
    MEDITERRANEAN = "mediterranean"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    LOW_CARB = "low_carb"

class NutritionRequest(BaseModel):
    # Personal data
    age: int = Field(
        ..., 
        ge=13, 
        le=100, 
        description="User age (13-100 years)"
    )
    gender: GenderEnum = Field(..., description="Biological sex")
    weight: float = Field(
        ..., 
        gt=20, 
        lt=300, 
        description="Current weight in kg"
    )
    height: int = Field(
        ..., 
        ge=100, 
        le=250, 
        description="Height in cm"
    )
    target_weight: Optional[float] = Field(
        None, 
        gt=20, 
        lt=300, 
        description="Target weight in kg (if applicable)"
    )
    
    # Activity and goals
    activity_level: ActivityLevelEnum = Field(..., description="Physical activity level")
    nutrition_goal: NutritionGoalEnum = Field(..., description="Primary nutrition goal")
    timeline_weeks: int = Field(
        default=12,
        ge=1,
        le=52,
        description="Timeline to achieve goal (weeks)"
    )
    
    # Dietary preferences
    dietary_restrictions: List[DietaryRestrictionsEnum] = Field(
        default=[], 
        max_items=3,
        description="Dietary restrictions or preferences"
    )
    allergies: List[str] = Field(
        default=[], 
        max_items=10,
        description="Food allergies or intolerances"
    )
    disliked_foods: List[str] = Field(
        default=[], 
        max_items=15,
        description="Foods to avoid"
    )
    preferred_foods: List[str] = Field(
        default=[], 
        max_items=15,
        description="Preferred foods"
    )
    
    # Lifestyle factors
    cooking_time_available: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Average cooking time available per meal (minutes)"
    )
    meals_per_day: int = Field(
        default=3,
        ge=2,
        le=6,
        description="Preferred number of meals per day"
    )
    budget_per_week: Optional[float] = Field(
        None,
        gt=0,
        description="Weekly food budget (optional)"
    )
    
    # Health considerations
    health_conditions: List[str] = Field(
        default=[],
        max_items=5,
        description="Health conditions affecting nutrition"
    )
    medications: List[str] = Field(
        default=[],
        max_items=5,
        description="Medications that may affect nutrition"
    )

    @validator('target_weight')
    def validate_target_weight(cls, v, values):
        if v is not None and 'weight' in values:
            if 'nutrition_goal' in values:
                goal = values['nutrition_goal']
                current = values['weight']
                if goal == NutritionGoalEnum.WEIGHT_LOSS and v >= current:
                    raise ValueError("Target weight must be lower than current weight for weight loss")
                elif goal == NutritionGoalEnum.WEIGHT_GAIN and v <= current:
                    raise ValueError("Target weight must be higher than current weight for weight gain")
        return v

class Macros(BaseModel):
    calories: int = Field(..., description="Calories in this portion")
    protein_g: float = Field(..., description="Protein in grams")
    carbs_g: float = Field(..., description="Carbohydrates in grams")
    fat_g: float = Field(..., description="Fat in grams")
    fiber_g: Optional[float] = Field(None, description="Fiber in grams (optional)")
    sugar_g: Optional[float] = Field(None, description="Sugar in grams (optional)")

class Meal(BaseModel):
    name: str = Field(..., description="Meal name")
    time: str = Field(..., description="Recommended time")
    calories: int = Field(..., description="Approximate calories")
    macros: Macros = Field(..., description="Detailed macronutrients")
    ingredients: List[str] = Field(..., description="Required ingredients")
    preparation_time: int = Field(..., description="Preparation time in minutes")
    instructions: List[str] = Field(..., description="Cooking instructions")
    tips: List[str] = Field(default=[], description="Preparation tips")

class NutritionalSupplement(BaseModel):
    name: str = Field(..., description="Supplement name")
    dosage: str = Field(..., description="Recommended dosage")
    timing: str = Field(..., description="When to take")
    purpose: str = Field(..., description="Why it's recommended")
    interactions: List[str] = Field(default=[], description="Potential interactions")

class Micronutrients(BaseModel):
    vitamin_d_mcg: float = Field(..., description="Daily vitamin D requirement in micrograms")
    vitamin_b12_mcg: float = Field(..., description="Daily vitamin B12 requirement in micrograms")
    iron_mg: float = Field(..., description="Daily iron requirement in milligrams")
    calcium_mg: float = Field(..., description="Daily calcium requirement in milligrams")
    omega3_g: float = Field(..., description="Daily omega-3 requirement in grams")

class ElectrolyteNeeds(BaseModel):
    sodium: str = Field(..., description="Sodium intake recommendations")
    potassium: str = Field(..., description="Potassium intake recommendations")

class HydrationGuidelines(BaseModel):
    daily_water_liters: float = Field(..., description="Recommended daily water intake in liters")
    electrolyte_needs: ElectrolyteNeeds = Field(..., description="Electrolyte requirements")
    timing_recommendations: List[str] = Field(..., description="When to drink water throughout the day")

class NutritionResponse(BaseModel):
    daily_calories: int = Field(..., description="Total daily caloric target")
    daily_macros: Macros = Field(..., description="Daily macronutrient targets")
    meals: List[Meal] = Field(..., description="Detailed meal plan")
    weekly_meal_prep: Dict[str, List[str]] = Field(..., description="Meal preparation schedule")
    shopping_list: List[str] = Field(..., description="Ingredient shopping list")
    recommended_supplements: List[NutritionalSupplement] = Field(..., description="Supplement recommendations")
    key_micronutrients: Micronutrients = Field(..., description="Important micronutrient targets")
    nutrition_education: List[str] = Field(..., description="Educational tips")
    hydration_guidelines: HydrationGuidelines = Field(..., description="Hydration recommendations")
    progress_metrics: List[str] = Field(..., description="Key metrics to track")
    adjustment_guidelines: List[str] = Field(..., description="How to adjust the plan")

def build_professional_nutrition_prompt(request: NutritionRequest) -> str:
    """Build ultra-professional prompt for personalized nutrition plan generation"""
    
    # BMR calculation using Mifflin-St Jeor equation
    if request.gender == GenderEnum.MALE:
        bmr = 10 * request.weight + 6.25 * request.height - 5 * request.age + 5
    else:
        bmr = 10 * request.weight + 6.25 * request.height - 5 * request.age - 161
    
    # Activity multipliers
    activity_multipliers = {
        ActivityLevelEnum.SEDENTARY: 1.2,
        ActivityLevelEnum.LIGHTLY_ACTIVE: 1.375,
        ActivityLevelEnum.MODERATELY_ACTIVE: 1.55,
        ActivityLevelEnum.VERY_ACTIVE: 1.725,
        ActivityLevelEnum.EXTREMELY_ACTIVE: 1.9
    }
    
    tdee = round(bmr * activity_multipliers[request.activity_level])
    
    # Handle restrictions and allergies
    restrictions_text = ""
    if request.dietary_restrictions:
        restrictions_str = ', '.join(r.value for r in request.dietary_restrictions)
        restrictions_text += f"Diet: {restrictions_str}. "
    
    if request.allergies:
        restrictions_text += f"ALLERGIES: {', '.join(request.allergies)}. "
    
    if request.disliked_foods:
        restrictions_text += f"Avoid: {', '.join(request.disliked_foods)}. "
    
    # Budget context
    budget_text = f"Budget: {request.budget_per_week}€/week. " if request.budget_per_week else ""
    
    return f"""
You are a certified nutritionist creating a nutrition plan.

CLIENT: {request.age}yo {request.gender.value}, {request.weight}kg, {request.height}cm
ACTIVITY: {request.activity_level.value}, BMR: {bmr:.0f} cal, TDEE: {tdee} cal
GOAL: {request.nutrition_goal.value}, Timeline: {request.timeline_weeks}w
TARGET: {request.target_weight or 'maintain current'}kg
MEALS: {request.meals_per_day}/day, Cooking: {request.cooking_time_available}min
{restrictions_text}{budget_text}

OUTPUT FORMAT (exact JSON):
{{
  "daily_calories": number,
  "daily_macros": {{"calories": number, "protein_g": number, "carbs_g": number, "fat_g": number}},
  "meals": [{{
    "name": "string",
    "time": "string", 
    "calories": number,
    "macros": {{"calories": number, "protein_g": number, "carbs_g": number, "fat_g": number}},
    "ingredients": ["string"],
    "preparation_time": number,
    "instructions": ["string"],
    "tips": ["string"]
  }}],
  "weekly_meal_prep": {{"sunday": ["string"], "wednesday": ["string"]}},
  "shopping_list": ["string"],
  "recommended_supplements": [{{
    "name": "string",
    "dosage": "string", 
    "timing": "string",
    "purpose": "string",
    "interactions": ["string"]
  }}],
  "key_micronutrients": {{
    "vitamin_d_mcg": number,
    "vitamin_b12_mcg": number,
    "iron_mg": number,
    "calcium_mg": number,
    "omega3_g": number
  }},
  "nutrition_education": ["string"],
  "hydration_guidelines": {{
    "daily_water_liters": number,
    "electrolyte_needs": {{"sodium": "string", "potassium": "string"}},
    "timing_recommendations": ["string"]
  }},
  "progress_metrics": ["string"],
  "adjustment_guidelines": ["string"]
}}

REQUIREMENTS:
- Calculate precise calories based on goal (deficit/surplus from TDEE)
- Create {request.meals_per_day} balanced meals with exact macros
- Cooking time ≤ {request.cooking_time_available}min per meal
- Include weekly prep strategy and shopping list
- Account for all restrictions and allergies

KEEP RESPONSES CONCISE:
- Meal names ≤ 12 characters
- Instructions ≤ 8 words each
- Tips ≤ 6 words each
- No line breaks in JSON strings
- Use simple ingredient names
"""

@router.post("/plan", response_model=NutritionResponse, tags=["Nutrition"])
async def generate_nutrition_plan(
    request: NutritionRequest = Body(..., description="Personalized nutrition parameters")
):
    """
    🥗 Generate ultra-personalized nutrition plan
    
    This API uses AI to create scientifically-backed nutrition plans 
    adapted to your unique metabolic profile and lifestyle.
    
    **Features:**
    - Precise caloric and macro calculations
    - Dietary restriction compliance
    - Meal prep optimization
    - Supplement recommendations
    - Progress tracking guidelines
    """
    try:
        # Log without PII in production
        if os.getenv("PRODUCTION"):
            logger.info(f"Generating nutrition plan for goal: {request.nutrition_goal.value}")
        else:
            logger.debug(f"Generating nutrition plan for user: {request.age}yo {request.gender.value}, goal: {request.nutrition_goal.value}")
        
        prompt = build_professional_nutrition_prompt(request)
        response = ask_llm(
            prompt, 
            max_tokens=1200  # Increased for complete nutrition plans
        )
        
        # Additional response validation
        if not all(key in response for key in ['daily_calories', 'daily_macros', 'meals']):
            raise HTTPException(
                status_code=500,
                detail="Incomplete nutrition plan received from AI"
            )
        
        logger.info("Nutrition plan generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error generating nutrition plan: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Nutrition plan generation failed",
                "message": "Unable to generate personalized nutrition plan. Please try again.",
                "support": "Contact support if the issue persists"
            }
        )

@router.get("/goals", tags=["Nutrition"])
async def get_nutrition_goals():
    """📊 Get available nutrition goals"""
    return {
        "goals": [
            {
                "id": goal.value,
                "name": goal.value.replace("_", " ").title(),
                "description": _get_nutrition_goal_description(goal.value)
            }
            for goal in NutritionGoalEnum
        ]
    }

@router.get("/restrictions", tags=["Nutrition"])
async def get_dietary_restrictions():
    """🚫 Get available dietary restrictions"""
    return {
        "restrictions": [
            {
                "id": restriction.value,
                "name": restriction.value.replace("_", " ").title(),
                "description": _get_restriction_description(restriction.value)
            }
            for restriction in DietaryRestrictionsEnum
        ]
    }

@router.get("/activity-levels", tags=["Nutrition"])
async def get_activity_levels():
    """🏃 Get activity level options"""
    return {
        "activity_levels": [
            {
                "id": level.value,
                "name": level.value.replace("_", " ").title(),
                "description": _get_activity_description(level.value)
            }
            for level in ActivityLevelEnum
        ]
    }

@router.get("/dietary-preferences")
async def get_dietary_preferences():
    """Get available dietary preferences."""
    return {
        "dietary_preferences": [
            {"id": "no_restrictions", "name": "No Restrictions", "description": "No dietary restrictions"},
            {"id": "vegetarian", "name": "Vegetarian", "description": "No meat or fish"},
            {"id": "vegan", "name": "Vegan", "description": "No animal products"},
            {"id": "pescatarian", "name": "Pescatarian", "description": "Fish allowed, no other meat"},
            {"id": "keto", "name": "Ketogenic", "description": "Very low carb, high fat"},
            {"id": "paleo", "name": "Paleo", "description": "Whole foods, no processed"},
            {"id": "mediterranean", "name": "Mediterranean", "description": "Mediterranean diet pattern"},
            {"id": "gluten_free", "name": "Gluten Free", "description": "No gluten-containing foods"},
            {"id": "dairy_free", "name": "Dairy Free", "description": "No dairy products"},
            {"id": "low_sodium", "name": "Low Sodium", "description": "Reduced sodium intake"},
            {"id": "high_protein", "name": "High Protein", "description": "Increased protein focus"}
        ]
    }

@router.get("/activity-levels")
async def get_activity_levels():
    """Get available activity levels."""
    return {
        "activity_levels": [
            {"id": "sedentary", "name": "Sedentary", "description": "Little to no exercise"},
            {"id": "lightly_active", "name": "Lightly Active", "description": "Light exercise 1-3 days/week"},
            {"id": "moderately_active", "name": "Moderately Active", "description": "Moderate exercise 3-5 days/week"},
            {"id": "very_active", "name": "Very Active", "description": "Hard exercise 6-7 days/week"},
            {"id": "extra_active", "name": "Extra Active", "description": "Very hard exercise, physical job"}
        ]
    }

@router.get("/goals")
async def get_goals():
    """Get available nutrition goals."""
    return {
        "goals": [
            {"id": "weight_loss", "name": "Weight Loss", "description": "Lose body weight"},
            {"id": "weight_gain", "name": "Weight Gain", "description": "Gain healthy weight"},
            {"id": "muscle_gain", "name": "Muscle Gain", "description": "Build muscle mass"},
            {"id": "maintenance", "name": "Maintenance", "description": "Maintain current weight"},
            {"id": "general_health", "name": "General Health", "description": "Overall health improvement"},
            {"id": "athletic_performance", "name": "Athletic Performance", "description": "Optimize performance"}
        ]
    }

def _get_nutrition_goal_description(goal: str) -> str:
    descriptions = {
        "weight_loss": "Sustainable weight loss with preserved muscle mass",
        "weight_gain": "Healthy weight gain with optimal body composition",
        "muscle_gain": "Muscle mass development with strategic nutrition",
        "maintenance": "Weight maintenance with optimal health",
        "athletic_performance": "Performance optimization through nutrition",
        "general_health": "Overall health improvement through balanced nutrition"
    }
    return descriptions.get(goal, "Personalized nutrition goal")

def _get_restriction_description(restriction: str) -> str:
    descriptions = {
        "none": "No dietary restrictions",
        "vegetarian": "Plant-based diet with dairy and eggs",
        "vegan": "Strictly plant-based diet",
        "keto": "Very low carb, high fat ketogenic diet",
        "mediterranean": "Mediterranean-style eating pattern",
        "paleo": "Paleolithic diet principles",
        "gluten_free": "Gluten-free diet for celiac or sensitivity",
        "dairy_free": "Lactose-free and dairy-free options",
        "low_carb": "Reduced carbohydrate intake"
    }
    return descriptions.get(restriction, "Custom dietary approach")

def _get_activity_description(activity: str) -> str:
    descriptions = {
        "sedentary": "Little to no exercise (desk job)",
        "lightly_active": "Light exercise 1-3 days/week",
        "moderately_active": "Moderate exercise 3-5 days/week",
        "very_active": "Heavy exercise 6-7 days/week",
        "extremely_active": "Very heavy exercise, 2x/day or physical job"
    }
    return descriptions.get(activity, "Custom activity level")
