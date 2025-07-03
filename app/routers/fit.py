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


class FitnessLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class FitnessGoalEnum(str, Enum):
    MUSCLE_GAIN = "muscle_gain"
    WEIGHT_LOSS = "weight_loss"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    ATHLETIC_PERFORMANCE = "athletic_performance"
    GENERAL_FITNESS = "general_fitness"
    REHABILITATION = "rehabilitation"


class EquipmentEnum(str, Enum):
    NONE = "bodyweight"
    HOME_BASIC = "home_basic"
    FULL_GYM = "full_gym"
    MINIMAL = "minimal"


class WorkoutRequest(BaseModel):
    # Personal data
    age: int = Field(..., ge=13, le=100, description="User age (13-100 years)")
    gender: GenderEnum = Field(..., description="Biological sex")
    weight: float = Field(..., gt=20, lt=300, description="Weight in kg")
    height: int = Field(..., ge=100, le=250, description="Height in cm")

    # Level and goals
    fitness_level: FitnessLevelEnum = Field(..., description="Current fitness level")
    primary_goal: FitnessGoalEnum = Field(..., description="Primary goal")
    secondary_goals: List[FitnessGoalEnum] = Field(
        default=[], max_items=2, description="Secondary goals (max 2)"
    )

    # Training parameters
    sessions_per_week: int = Field(
        ..., ge=1, le=7, description="Number of sessions per week"
    )
    session_duration: int = Field(
        default=60, ge=15, le=180, description="Desired session duration (minutes)"
    )
    available_equipment: EquipmentEnum = Field(..., description="Available equipment")

    # Constraints and preferences
    injuries_limitations: List[str] = Field(
        default=[], max_items=5, description="Injuries or physical limitations"
    )
    preferred_workout_time: Optional[Literal["morning", "afternoon", "evening"]] = (
        Field(default=None, description="Preferred workout time")
    )
    experience_years: int = Field(
        default=0, ge=0, le=50, description="Years of training experience"
    )

    @validator("secondary_goals")
    def validate_secondary_goals(cls, v, values):
        if "primary_goal" in values and values["primary_goal"] in v:
            raise ValueError("Secondary goal cannot be the same as primary goal")
        return v


class Exercise(BaseModel):
    name: str = Field(..., description="Exercise name")
    muscle_groups: List[str] = Field(..., description="Target muscle groups")
    sets: int = Field(..., ge=1, le=10, description="Number of sets")
    reps: str = Field(..., description="Repetitions (e.g., '8-12', '30s', 'max')")
    rest_time: str = Field(..., description="Rest time (e.g., '60s', '2min')")
    intensity: str = Field(..., description="Recommended intensity/load")
    technique_tips: List[str] = Field(..., description="Execution tips")
    modifications: Optional[Dict[str, str]] = Field(
        default=None, description="Modifications for different levels"
    )


class WorkoutPhase(BaseModel):
    duration: str = Field(..., description="Phase duration")
    exercises: List[Exercise] = Field(..., description="Phase exercises")
    instructions: List[str] = Field(..., description="General instructions")


class NutritionTip(BaseModel):
    category: str = Field(..., description="Category (pre/post workout, etc.)")
    recommendation: str = Field(..., description="Nutritional recommendation")
    timing: str = Field(..., description="Optimal timing")


class WorkoutResponse(BaseModel):
    # Workout structure
    warmup: WorkoutPhase = Field(..., description="Warm-up phase")
    main_workout: WorkoutPhase = Field(..., description="Main workout")
    cooldown: WorkoutPhase = Field(..., description="Cool-down phase")

    # Metadata
    workout_summary: Dict[str, Any] = Field(..., description="Workout summary")
    progression_notes: List[str] = Field(..., description="Progression notes")
    nutrition_tips: List[NutritionTip] = Field(..., description="Nutrition tips")
    recovery_recommendations: List[str] = Field(
        ..., description="Recovery recommendations"
    )

    # Planning
    weekly_schedule_suggestion: Dict[str, str] = Field(
        ..., description="Weekly schedule suggestion"
    )


def build_professional_prompt(req: WorkoutRequest) -> str:
    """Build ultra-professional prompt for personalized workout generation"""

    # BMI calculation for context
    height_m = req.height / 100
    bmi = round(req.weight / (height_m**2), 1)

    # Handle limitations
    limitations_text = ""
    if req.injuries_limitations:
        limitations_text = f"CRITICAL: Account for these limitations/injuries: {', '.join(req.injuries_limitations)}. "

    # Handle secondary goals properly (fix enum issue)
    secondary_goals_str = (
        ", ".join(g.value for g in req.secondary_goals)
        if req.secondary_goals
        else "none"
    )

    return f"""
You are an elite certified personal trainer creating a workout program.

CLIENT: {req.age}yo {req.gender.value}, {req.weight}kg, {req.height}cm (BMI: {bmi})
EXPERIENCE: {req.experience_years}yr, Level: {req.fitness_level.value}
GOALS: Primary={req.primary_goal.value}, Secondary={secondary_goals_str}
SCHEDULE: {req.sessions_per_week}x/week, {req.session_duration}min sessions
EQUIPMENT: {req.available_equipment.value}
{limitations_text}

OUTPUT FORMAT (exact JSON structure):
{{
  "warmup": {{
    "duration": "X minutes",
    "exercises": [{{
      "name": "string",
      "muscle_groups": ["string"],
      "sets": number,
      "reps": "string", 
      "rest_time": "string",
      "intensity": "string",
      "technique_tips": ["string"]
    }}],
    "instructions": ["string"]
  }},
  "main_workout": {{
    "duration": "X minutes", 
    "exercises": [{{
      "name": "string",
      "muscle_groups": ["string"],
      "sets": number,
      "reps": "string",
      "rest_time": "string", 
      "intensity": "string",
      "technique_tips": ["string"],
      "modifications": {{"beginner": "string", "advanced": "string"}}
    }}],
    "instructions": ["string"]
  }},
  "cooldown": {{
    "duration": "X minutes",
    "exercises": [{{
      "name": "string",
      "muscle_groups": ["string"], 
      "sets": number,
      "reps": "string",
      "rest_time": "string",
      "intensity": "string",
      "technique_tips": ["string"]
    }}],
    "instructions": ["string"]
  }},
  "workout_summary": {{
    "total_time": "X minutes",
    "difficulty": "string",
    "focus": "string"
  }},
  "progression_notes": ["string"],
  "nutrition_tips": [{{
    "category": "string",
    "recommendation": "string", 
    "timing": "string"
  }}],
  "recovery_recommendations": ["string"],
  "weekly_schedule_suggestion": {{
    "monday": "string",
    "wednesday": "string", 
    "friday": "string"
  }}
}}

REQUIREMENTS:
- Create warmup (8-10min), main workout, cooldown (5-8min)
- 4-6 exercises per phase maximum
- Rep ranges match goal: strength(1-6), hypertrophy(6-12), endurance(12+)
- Include compound and isolation exercises
- Account for equipment and limitations

KEEP RESPONSES CONCISE:
- Exercise names ≤ 15 characters when possible
- Tips ≤ 8 words each
- Instructions ≤ 10 words each  
- No line breaks in JSON strings
- No markdown formatting
"""


@router.post("/workout", response_model=WorkoutResponse, tags=["Fitness"])
async def generate_personalized_workout(
    request: WorkoutRequest = Body(..., description="Personalized workout parameters")
):
    """
    🏋️ Generate ultra-personalized workout program

    This API uses AI to create scientifically-backed workout programs
    adapted to your unique profile and specific goals.

    **Features:**
    - Personalized biomechanical analysis
    - Adaptive progression
    - Physical limitations management
    - Nutritional recommendations
    - Optimized weekly planning
    """
    try:
        # Log without PII in production
        if os.getenv("PRODUCTION"):
            logger.info(f"Generating workout for goal: {request.primary_goal.value}")
        else:
            logger.debug(
                f"Generating workout for user: {request.age}yo {request.gender.value}, goal: {request.primary_goal.value}"
            )

        prompt = build_professional_prompt(request)
        response = ask_llm(
            prompt, max_tokens=1600  # Increased for complete workout structure
        )

        # Additional response validation
        if not all(key in response for key in ["warmup", "main_workout", "cooldown"]):
            raise HTTPException(
                status_code=500, detail="Incomplete workout structure received from AI"
            )

        logger.info("Workout generated successfully")
        return response

    except Exception as e:
        logger.error(f"Error generating workout: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Workout generation failed",
                "message": "Unable to generate personalized workout. Please try again.",
                "support": "Contact support if the issue persists",
            },
        )


@router.get("/fitness-levels")
async def get_fitness_levels():
    """Get available fitness levels."""
    return {
        "fitness_levels": [
            {
                "id": "beginner",
                "name": "Beginner",
                "description": "New to exercise or returning after a long break",
            },
            {
                "id": "intermediate",
                "name": "Intermediate",
                "description": "Regular exercise for 3-6 months",
            },
            {
                "id": "advanced",
                "name": "Advanced",
                "description": "Consistent training for 1+ years",
            },
            {
                "id": "expert",
                "name": "Expert",
                "description": "Advanced athlete or trainer level",
            },
        ]
    }


@router.get("/equipment")
async def get_equipment_options():
    """Get available equipment options."""
    return {
        "equipment_options": [
            {
                "id": "bodyweight",
                "name": "Bodyweight Only",
                "description": "No equipment needed",
            },
            {
                "id": "home_basic",
                "name": "Home Basic",
                "description": "Dumbbells, resistance bands",
            },
            {
                "id": "home_gym",
                "name": "Home Gym",
                "description": "Full home gym setup",
            },
            {"id": "gym", "name": "Commercial Gym", "description": "Full gym access"},
        ]
    }


@router.get("/goals")
async def get_goals():
    """Get available fitness goals."""
    return {
        "goals": [
            {
                "id": "weight_loss",
                "name": "Weight Loss",
                "description": "Burn fat and lose weight",
            },
            {
                "id": "muscle_gain",
                "name": "Muscle Gain",
                "description": "Build muscle mass",
            },
            {
                "id": "strength",
                "name": "Strength",
                "description": "Increase overall strength",
            },
            {
                "id": "endurance",
                "name": "Endurance",
                "description": "Improve cardiovascular fitness",
            },
            {
                "id": "general_fitness",
                "name": "General Fitness",
                "description": "Overall health and wellness",
            },
            {
                "id": "athletic_performance",
                "name": "Athletic Performance",
                "description": "Sport-specific performance",
            },
        ]
    }


def _get_goal_description(goal: str) -> str:
    descriptions = {
        "muscle_gain": "Muscle mass development and hypertrophy",
        "weight_loss": "Weight loss and improved body composition",
        "strength": "Maximal strength and power increase",
        "endurance": "Cardiovascular and muscular endurance improvement",
        "athletic_performance": "Sport-specific performance optimization",
        "general_fitness": "Overall fitness improvement",
        "rehabilitation": "Recovery and post-injury strengthening",
    }
    return descriptions.get(goal, "Personalized fitness goal")


def _get_equipment_description(equipment: str) -> str:
    descriptions = {
        "bodyweight": "Bodyweight exercises only",
        "home_basic": "Basic home equipment (dumbbells, resistance bands)",
        "full_gym": "Full gym access with complete equipment",
        "minimal": "Minimal equipment (few weights, mat)",
    }
    return descriptions.get(equipment, "Custom equipment configuration")
