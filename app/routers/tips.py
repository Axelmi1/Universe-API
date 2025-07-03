from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from app.services.ia_client import ask_llm
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter()


class DomainEnum(str, Enum):
    FITNESS = "fitness"
    NUTRITION = "nutrition"
    MENTAL_HEALTH = "mental_health"
    SLEEP = "sleep"
    HYDRATION = "hydration"
    RECOVERY = "recovery"
    MOTIVATION = "motivation"
    LIFESTYLE = "lifestyle"


class ExperienceLevelEnum(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class TipFormatEnum(str, Enum):
    QUICK_TIPS = "quick_tips"
    DETAILED_GUIDE = "detailed_guide"
    STEP_BY_STEP = "step_by_step"
    SCIENCE_BASED = "science_based"
    PRACTICAL_HACKS = "practical_hacks"


class TipsRequest(BaseModel):
    # Core request parameters
    domain: DomainEnum = Field(..., description="Primary domain for tips")
    secondary_domains: List[DomainEnum] = Field(
        default=[], max_items=2, description="Additional related domains"
    )

    # User context
    experience_level: ExperienceLevelEnum = Field(
        ..., description="User experience level"
    )
    format_preference: TipFormatEnum = Field(..., description="Preferred tip format")

    # Personalization
    current_challenges: List[str] = Field(
        default=[], max_items=5, description="Current challenges or obstacles"
    )
    specific_goals: List[str] = Field(
        default=[], max_items=3, description="Specific goals to address"
    )
    time_constraints: Optional[int] = Field(
        None, ge=5, le=120, description="Available time per day (minutes)"
    )

    # Contextual information
    lifestyle_factors: List[str] = Field(
        default=[],
        max_items=5,
        description="Lifestyle factors (busy schedule, travel, etc.)",
    )
    preferred_complexity: Literal["simple", "moderate", "complex"] = Field(
        default="moderate", description="Preferred complexity level"
    )

    # Optional targeting
    age_range: Optional[Literal["teen", "young_adult", "adult", "senior"]] = Field(
        None, description="Age range for age-appropriate tips"
    )
    equipment_access: Optional[List[str]] = Field(
        default=None, max_items=10, description="Available equipment or resources"
    )

    @validator("secondary_domains")
    def validate_secondary_domains(cls, v, values):
        if "domain" in values and values["domain"] in v:
            raise ValueError("Secondary domain cannot be the same as primary domain")
        return v


class Tip(BaseModel):
    title: str = Field(..., description="Tip title")
    category: str = Field(..., description="Tip category")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ..., description="Implementation difficulty"
    )
    time_required: str = Field(..., description="Time required to implement")
    description: str = Field(..., description="Detailed description")
    action_steps: List[str] = Field(..., description="Step-by-step action items")
    benefits: List[str] = Field(..., description="Expected benefits")
    common_mistakes: List[str] = Field(
        default=[], description="Common mistakes to avoid"
    )
    scientific_rationale: Optional[str] = Field(None, description="Scientific backing")
    progression_tips: List[str] = Field(
        default=[], description="How to progress or advance"
    )


class TipsResponse(BaseModel):
    # Core tips
    tips: List[Tip] = Field(..., description="Personalized tips")

    # Implementation guidance
    implementation_strategy: Dict[str, Any] = Field(
        ..., description="How to implement tips effectively"
    )
    priority_order: List[str] = Field(
        ..., description="Recommended order of implementation"
    )

    # Progress tracking
    tracking_methods: List[str] = Field(..., description="Ways to track progress")
    success_indicators: List[str] = Field(
        ..., description="Signs of successful implementation"
    )

    # Additional resources
    related_concepts: List[str] = Field(..., description="Related concepts to explore")
    advanced_techniques: List[str] = Field(
        default=[], description="Advanced techniques for later"
    )

    # Troubleshooting
    common_obstacles: List[str] = Field(
        ..., description="Common obstacles and solutions"
    )
    motivation_strategies: List[str] = Field(
        ..., description="Strategies to stay motivated"
    )


def build_professional_tips_prompt(request: TipsRequest) -> str:
    """Build ultra-professional prompt for personalized tips generation"""

    # Handle secondary domains properly (fix enum issue)
    secondary_domains_str = (
        ", ".join(d.value for d in request.secondary_domains)
        if request.secondary_domains
        else "none"
    )

    # Context building
    challenges_text = (
        f"Current challenges: {', '.join(request.current_challenges)}. "
        if request.current_challenges
        else ""
    )
    goals_text = (
        f"Specific goals: {', '.join(request.specific_goals)}. "
        if request.specific_goals
        else ""
    )
    lifestyle_text = (
        f"Lifestyle factors: {', '.join(request.lifestyle_factors)}. "
        if request.lifestyle_factors
        else ""
    )
    equipment_text = (
        f"Available equipment: {', '.join(request.equipment_access)}. "
        if request.equipment_access
        else ""
    )
    time_text = (
        f"Time available: {request.time_constraints} min/day. "
        if request.time_constraints
        else ""
    )
    age_text = f"Age group: {request.age_range}. " if request.age_range else ""

    return f"""
You are a certified health and wellness coach with expertise across fitness, nutrition, mental health, and lifestyle optimization.

CLIENT PROFILE:
- Primary focus: {request.domain.value}
- Secondary interests: {secondary_domains_str}
- Experience level: {request.experience_level.value}
- Preferred format: {request.format_preference.value}
- Complexity preference: {request.preferred_complexity}
{challenges_text}{goals_text}{time_text}{age_text}{lifestyle_text}{equipment_text}

REQUIREMENTS:
1. Generate 4-5 highly actionable tips specifically for {request.domain.value}
2. Each string field ≤ 120 characters, arrays ≤ 6 items
3. Tips must be appropriate for {request.experience_level.value} level
4. Format according to {request.format_preference.value} style
5. Include scientific rationale where relevant
6. Provide implementation strategy and priority order
7. Address stated challenges and goals specifically

TIP COMPLEXITY GUIDELINES:
- Simple: Basic, foundational practices requiring minimal setup
- Moderate: Structured approaches with multiple components
- Complex: Advanced strategies requiring significant commitment

FORMAT REQUIREMENTS:
- Quick tips: Concise, immediately actionable advice
- Detailed guide: Comprehensive explanations with context
- Step-by-step: Clear sequential instructions
- Science-based: Research-backed recommendations with citations
- Practical hacks: Clever shortcuts and efficiency techniques

CRITICAL CONSTRAINTS:
- All tips must be safe and evidence-based
- Consider time constraints and lifestyle factors
- Provide realistic expectations for implementation
- Include troubleshooting for common obstacles
- Address motivation and adherence strategies

OUTPUT FORMAT (exact JSON structure):
{{
  "tips": [{{
    "title": "string",
    "category": "string",
    "difficulty": "easy|medium|hard",
    "time_required": "string",
    "description": "string",
    "action_steps": ["string"],
    "benefits": ["string"],
    "common_mistakes": ["string"],
    "scientific_rationale": "string",
    "progression_tips": ["string"]
  }}],
  "implementation_strategy": {{
    "start_with": "string",
    "timeline": "string",
    "key_principles": ["string"]
  }},
  "priority_order": ["string"],
  "tracking_methods": ["string"],
  "success_indicators": ["string"],
  "related_concepts": ["string"],
  "advanced_techniques": ["string"],
  "common_obstacles": ["string"],
  "motivation_strategies": ["string"]
}}

Focus on practical application, scientific accuracy, and personalized relevance.
"""


@router.post("/generate", response_model=TipsResponse, tags=["Tips & Advice"])
async def generate_personalized_tips(
    request: TipsRequest = Body(..., description="Personalized tips parameters")
):
    """
    💡 Generate ultra-personalized health and wellness tips

    This API uses AI to create evidence-based, actionable tips
    tailored to your specific needs, experience level, and lifestyle.

    **Features:**
    - Domain-specific expertise
    - Experience-level appropriate content
    - Implementation strategies
    - Progress tracking guidance
    - Troubleshooting support
    """
    try:
        # Log without PII in production
        if os.getenv("PRODUCTION"):
            logger.info(
                f"Generating tips for domain: {request.domain.value}, level: {request.experience_level.value}"
            )
        else:
            logger.debug(
                f"Generating tips for user: {request.domain.value}, level: {request.experience_level.value}"
            )

        prompt = build_professional_tips_prompt(request)
        response = ask_llm(
            prompt,
            max_tokens=2000,  # Increased to 2000 tokens for complete responses
            force_json=True,  # Native JSON mode for guaranteed valid output
        )

        # Additional response validation
        if not all(
            key in response
            for key in ["tips", "implementation_strategy", "priority_order"]
        ):
            raise HTTPException(
                status_code=500, detail="Incomplete tips response received from AI"
            )

        # Validate tips structure
        if not response.get("tips") or len(response["tips"]) < 3:
            raise HTTPException(
                status_code=500, detail="Insufficient number of tips generated"
            )

        logger.info("Tips generated successfully")
        return response

    except Exception as e:
        logger.error(f"Error generating tips: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Tips generation failed",
                "message": "Unable to generate personalized tips. Please try again.",
                "support": "Contact support if the issue persists",
            },
        )


@router.get("/domains", tags=["Tips & Advice"])
async def get_available_domains():
    """📚 Get available tip domains"""
    return {
        "domains": [
            {
                "id": domain.value,
                "name": domain.value.replace("_", " ").title(),
                "description": _get_domain_description(domain.value),
            }
            for domain in DomainEnum
        ]
    }


@router.get("/formats", tags=["Tips & Advice"])
async def get_tip_formats():
    """📋 Get available tip formats"""
    return {
        "formats": [
            {
                "id": format_type.value,
                "name": format_type.value.replace("_", " ").title(),
                "description": _get_format_description(format_type.value),
            }
            for format_type in TipFormatEnum
        ]
    }


@router.get("/experience-levels", tags=["Tips & Advice"])
async def get_experience_levels():
    """📈 Get experience level options"""
    return {
        "levels": [
            {
                "id": level.value,
                "name": level.value.title(),
                "description": _get_level_description(level.value),
            }
            for level in ExperienceLevelEnum
        ]
    }


@router.get("/fitness-levels", tags=["Tips & Advice"])
async def get_fitness_levels():
    """📈 Get fitness level options (alias for experience-levels)"""
    return {
        "fitness_levels": [
            {
                "id": level.value,
                "name": level.value.title(),
                "description": _get_level_description(level.value),
            }
            for level in ExperienceLevelEnum
        ]
    }


@router.get("/challenges", tags=["Tips & Advice"])
async def get_challenges():
    """🎯 Get common health and fitness challenges"""
    challenges = [
        {
            "id": "lack_of_motivation",
            "name": "Lack of Motivation",
            "description": "Difficulty staying motivated to exercise",
        },
        {
            "id": "time_constraints",
            "name": "Time Constraints",
            "description": "Not enough time for regular workouts",
        },
        {
            "id": "budget_limitations",
            "name": "Budget Limitations",
            "description": "Limited budget for gym or equipment",
        },
        {
            "id": "lack_of_knowledge",
            "name": "Lack of Knowledge",
            "description": "Unsure about proper exercise techniques",
        },
        {
            "id": "plateau",
            "name": "Fitness Plateau",
            "description": "Progress has stalled or stopped",
        },
        {
            "id": "lack_of_energy",
            "name": "Lack of Energy",
            "description": "Feeling too tired to exercise regularly",
        },
        {
            "id": "injury_recovery",
            "name": "Injury Recovery",
            "description": "Working around or recovering from injury",
        },
        {
            "id": "social_pressure",
            "name": "Social Pressure",
            "description": "Negative social environment or peer pressure",
        },
    ]
    return {"challenges": challenges}


@router.get("/activities", tags=["Tips & Advice"])
async def get_preferred_activities():
    """🏃 Get preferred activity options"""
    activities = [
        {
            "id": "weight_training",
            "name": "Weight Training",
            "description": "Resistance training with weights",
        },
        {
            "id": "cardio",
            "name": "Cardio",
            "description": "Cardiovascular exercises like running, cycling",
        },
        {
            "id": "yoga",
            "name": "Yoga",
            "description": "Mind-body practice combining poses and breathing",
        },
        {
            "id": "walking",
            "name": "Walking",
            "description": "Low-impact aerobic exercise",
        },
        {
            "id": "swimming",
            "name": "Swimming",
            "description": "Full-body water-based exercise",
        },
        {
            "id": "high_intensity_interval_training",
            "name": "HIIT",
            "description": "High-intensity interval training",
        },
        {
            "id": "pilates",
            "name": "Pilates",
            "description": "Core-focused exercise system",
        },
        {
            "id": "dancing",
            "name": "Dancing",
            "description": "Rhythmic movement for fitness and fun",
        },
        {
            "id": "martial_arts",
            "name": "Martial Arts",
            "description": "Combat sports and self-defense training",
        },
        {
            "id": "outdoor_activities",
            "name": "Outdoor Activities",
            "description": "Hiking, rock climbing, outdoor sports",
        },
    ]
    return {"activities": activities}


@router.get("/health-conditions", tags=["Tips & Advice"])
async def get_health_conditions():
    """🏥 Get common health conditions to consider"""
    conditions = [
        {
            "id": "diabetes",
            "name": "Diabetes",
            "description": "Blood sugar regulation disorder",
        },
        {
            "id": "hypertension",
            "name": "Hypertension",
            "description": "High blood pressure condition",
        },
        {
            "id": "back_pain",
            "name": "Back Pain",
            "description": "Chronic or acute back pain issues",
        },
        {
            "id": "knee_problems",
            "name": "Knee Problems",
            "description": "Knee joint issues or injuries",
        },
        {
            "id": "heart_disease",
            "name": "Heart Disease",
            "description": "Cardiovascular health conditions",
        },
        {
            "id": "arthritis",
            "name": "Arthritis",
            "description": "Joint inflammation and pain",
        },
        {
            "id": "asthma",
            "name": "Asthma",
            "description": "Respiratory condition affecting breathing",
        },
        {
            "id": "osteoporosis",
            "name": "Osteoporosis",
            "description": "Bone density loss condition",
        },
        {
            "id": "fibromyalgia",
            "name": "Fibromyalgia",
            "description": "Chronic pain and fatigue syndrome",
        },
        {
            "id": "depression",
            "name": "Depression",
            "description": "Mental health condition affecting mood",
        },
    ]
    return {"health_conditions": conditions}


@router.post("/quick-tip", tags=["Tips & Advice"])
async def get_quick_tip(
    domain: DomainEnum = Query(..., description="Domain for quick tip"),
    level: ExperienceLevelEnum = Query(
        default=ExperienceLevelEnum.BEGINNER, description="Experience level"
    ),
):
    """⚡ Get a single quick tip for immediate use"""
    try:
        logger.info(f"Generating quick tip for domain: {domain.value}")

        prompt = f"""
You are a health and wellness expert. Provide ONE actionable tip for {domain.value} appropriate for {level.value} level.

Requirements:
- Must be immediately actionable
- Include 2-3 implementation steps
- Mention expected benefits
- Keep it concise but practical

Return a single tip object with: title, description, action_steps (array), benefits (array), time_required.
"""

        response = ask_llm(prompt, max_tokens=300)  # No schema for simple response

        logger.info("Quick tip generated successfully")
        return response

    except Exception as e:
        logger.error(f"Error generating quick tip: {str(e)}")
        raise HTTPException(status_code=500, detail="Unable to generate quick tip")


def _get_domain_description(domain: str) -> str:
    descriptions = {
        "fitness": "Exercise, training, and physical performance optimization",
        "nutrition": "Diet, meal planning, and nutritional strategies",
        "mental_health": "Stress management, mindfulness, and emotional wellbeing",
        "sleep": "Sleep quality, hygiene, and recovery optimization",
        "hydration": "Optimal fluid intake and electrolyte balance",
        "recovery": "Rest, regeneration, and injury prevention",
        "motivation": "Goal setting, habit formation, and adherence strategies",
        "lifestyle": "Daily routines, time management, and life balance",
    }
    return descriptions.get(domain, "Specialized health and wellness guidance")


def _get_format_description(format_type: str) -> str:
    descriptions = {
        "quick_tips": "Concise, immediately actionable advice",
        "detailed_guide": "Comprehensive explanations with full context",
        "step_by_step": "Clear sequential instructions for implementation",
        "science_based": "Research-backed recommendations with evidence",
        "practical_hacks": "Efficient shortcuts and optimization techniques",
    }
    return descriptions.get(format_type, "Custom tip format")


def _get_level_description(level: str) -> str:
    descriptions = {
        "beginner": "New to the domain, needs foundational guidance",
        "intermediate": "Some experience, ready for structured approaches",
        "advanced": "Significant experience, seeking optimization",
        "expert": "Extensive knowledge, interested in cutting-edge techniques",
    }
    return descriptions.get(level, "Custom experience level")
