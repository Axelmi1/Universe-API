import os
import pytest
import respx
import json
from httpx import AsyncClient
from fastapi import status
from app.main import app
import pytest_asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx

TEST_KEY = "unit-test-key"


@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["MASTER_API_KEY"] = "test-key"
    os.environ.pop("PRODUCTION", None)


@pytest_asyncio.fixture
async def async_client():
    """Create async test client."""
    from fastapi import FastAPI
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def openai_mock():
    """Mock OpenAI API responses."""
    with respx.mock(base_url="https://api.openai.com") as respx_mock:
        yield respx_mock


@pytest.fixture
def openai_mock_fitness():
    """Mock OpenAI responses for fitness endpoints."""
    with respx.mock:
        # Mock workout generation response
        workout_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "warmup": {
                                    "duration": "10 minutes",
                                    "exercises": [
                                        {
                                            "name": "Arm Circles",
                                            "muscle_groups": ["shoulders"],
                                            "sets": 1,
                                            "reps": "10 each direction",
                                            "rest_time": "0 seconds",
                                            "intensity": "low",
                                            "technique_tips": [
                                                "Keep arms straight",
                                                "Control the movement",
                                            ],
                                        }
                                    ],
                                    "instructions": [
                                        "Start slowly",
                                        "Increase intensity gradually",
                                    ],
                                },
                                "main_workout": {
                                    "duration": "30 minutes",
                                    "exercises": [
                                        {
                                            "name": "Push-ups",
                                            "muscle_groups": [
                                                "chest",
                                                "shoulders",
                                                "triceps",
                                            ],
                                            "sets": 3,
                                            "reps": "8-12",
                                            "rest_time": "60 seconds",
                                            "intensity": "moderate",
                                            "technique_tips": [
                                                "Keep body straight",
                                                "Full range of motion",
                                            ],
                                            "modifications": {
                                                "beginner": "Knee push-ups",
                                                "advanced": "Diamond push-ups",
                                            },
                                        }
                                    ],
                                    "instructions": [
                                        "Focus on form",
                                        "Control the movement",
                                    ],
                                },
                                "cooldown": {
                                    "duration": "10 minutes",
                                    "exercises": [
                                        {
                                            "name": "Static Stretching",
                                            "muscle_groups": ["full_body"],
                                            "sets": 1,
                                            "reps": "1",
                                            "rest_time": "0 seconds",
                                            "intensity": "low",
                                            "technique_tips": [
                                                "Hold each stretch",
                                                "Breathe deeply",
                                            ],
                                        }
                                    ],
                                    "instructions": ["Breathe deeply", "Relax muscles"],
                                },
                                "workout_summary": {
                                    "total_time": "50 minutes",
                                    "difficulty": "beginner",
                                    "focus": "strength",
                                },
                                "progression_notes": [
                                    "Start with bodyweight",
                                    "Increase reps weekly",
                                ],
                                "nutrition_tips": [
                                    {
                                        "category": "pre_workout",
                                        "recommendation": "Eat a light snack 30 minutes before",
                                        "timing": "30 minutes before",
                                    }
                                ],
                                "recovery_recommendations": [
                                    "Rest 48 hours between sessions",
                                    "Stay hydrated",
                                ],
                                "weekly_schedule_suggestion": {
                                    "monday": "Rest",
                                    "wednesday": "Workout",
                                    "friday": "Workout",
                                },
                            }
                        )
                    }
                }
            ],
            "usage": {"total_tokens": 500},
        }

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=workout_response)
        )

        yield


@pytest.fixture
def openai_mock_nutrition(openai_mock):
    """Mock OpenAI for nutrition responses."""
    nutrition_response = {
        "daily_calories": 2200,
        "daily_macros": {
            "calories": 2200,
            "protein_g": 165,
            "carbs_g": 247,
            "fat_g": 73,
        },
        "meals": [
            {
                "name": "Breakfast",
                "time": "7:00 AM",
                "calories": 450,
                "macros": {
                    "calories": 450,
                    "protein_g": 25,
                    "carbs_g": 55,
                    "fat_g": 12,
                },
                "ingredients": ["oats", "banana", "almond milk", "protein powder"],
                "preparation_time": 10,
                "instructions": [
                    "Mix oats with almond milk",
                    "Add banana and protein powder",
                    "Stir well",
                ],
                "tips": ["Prepare overnight", "Add berries for flavor"],
            },
            {
                "name": "Lunch",
                "time": "12:30 PM",
                "calories": 650,
                "macros": {
                    "calories": 650,
                    "protein_g": 45,
                    "carbs_g": 60,
                    "fat_g": 18,
                },
                "ingredients": ["chicken breast", "quinoa", "vegetables"],
                "preparation_time": 25,
                "instructions": [
                    "Cook chicken breast",
                    "Prepare quinoa",
                    "Steam vegetables",
                ],
                "tips": ["Season well", "Meal prep friendly"],
            },
            {
                "name": "Dinner",
                "time": "7:00 PM",
                "calories": 580,
                "macros": {
                    "calories": 580,
                    "protein_g": 35,
                    "carbs_g": 45,
                    "fat_g": 22,
                },
                "ingredients": ["salmon", "sweet potato", "broccoli"],
                "preparation_time": 30,
                "instructions": ["Bake salmon", "Roast sweet potato", "Steam broccoli"],
                "tips": ["Don't overcook salmon", "Season vegetables"],
            },
        ],
        "weekly_meal_prep": {
            "sunday": ["Prep proteins", "Cook grains"],
            "wednesday": ["Mid-week prep", "Fresh vegetables"],
        },
        "shopping_list": [
            "chicken breast",
            "salmon",
            "quinoa",
            "sweet potato",
            "broccoli",
            "oats",
            "banana",
            "almond milk",
            "protein powder",
        ],
        "recommended_supplements": [
            {
                "name": "Vitamin D3",
                "dosage": "1000 IU daily",
                "timing": "With breakfast",
                "purpose": "Bone health and immune support",
                "interactions": ["Take with fat for absorption"],
            }
        ],
        "key_micronutrients": {
            "vitamin_d_mcg": 15,
            "vitamin_b12_mcg": 2.4,
            "iron_mg": 18,
            "calcium_mg": 1000,
            "omega3_g": 1.6,
        },
        "nutrition_education": [
            "Focus on whole foods",
            "Stay hydrated",
            "Balance macronutrients",
        ],
        "hydration_guidelines": {
            "daily_water_liters": 2.5,
            "electrolyte_needs": {
                "sodium": "2300mg daily",
                "potassium": "3500mg daily",
            },
            "timing_recommendations": [
                "Drink 500ml upon waking",
                "Sip regularly throughout day",
                "Extra 200ml per hour of exercise",
            ],
        },
        "progress_metrics": ["Weight tracking", "Energy levels", "Sleep quality"],
        "adjustment_guidelines": [
            "Adjust portions based on progress",
            "Monitor energy levels",
            "Stay consistent",
        ],
    }

    openai_mock.post("/v1/chat/completions").respond(
        status_code=200,
        json={"choices": [{"message": {"content": json.dumps(nutrition_response)}}]},
    )
    return openai_mock


@pytest.fixture
def openai_mock_tips(openai_mock):
    """Mock OpenAI for tips responses."""
    tips_response = {
        "tips": [
            {
                "title": "Start Small",
                "category": "fitness",
                "difficulty": "easy",
                "time_required": "5 minutes",
                "description": "Begin with short, manageable workouts",
                "action_steps": [
                    "Start with 10-minute walks",
                    "Add 5 minutes weekly",
                    "Track your progress",
                ],
                "benefits": [
                    "Builds habit",
                    "Reduces overwhelm",
                    "Increases confidence",
                ],
                "common_mistakes": ["Starting too intense", "Skipping rest days"],
                "scientific_rationale": "Progressive overload principle supports gradual improvement",
                "progression_tips": [
                    "Increase duration before intensity",
                    "Listen to your body",
                ],
            },
            {
                "title": "Hydrate First",
                "category": "nutrition",
                "difficulty": "easy",
                "time_required": "1 minute",
                "description": "Drink water before meals",
                "action_steps": [
                    "Drink 500ml upon waking",
                    "Have water before meals",
                    "Carry a water bottle",
                ],
                "benefits": ["Better digestion", "Reduced hunger", "Improved energy"],
                "common_mistakes": [
                    "Waiting until thirsty",
                    "Drinking too much with meals",
                ],
                "scientific_rationale": "Proper hydration supports metabolic function",
                "progression_tips": [
                    "Add electrolytes if active",
                    "Monitor urine color",
                ],
            },
            {
                "title": "Sleep Schedule",
                "category": "lifestyle",
                "difficulty": "medium",
                "time_required": "30 minutes",
                "description": "Establish consistent sleep routine",
                "action_steps": [
                    "Set fixed bedtime",
                    "Create bedtime ritual",
                    "Avoid screens 1 hour before bed",
                ],
                "benefits": [
                    "Better recovery",
                    "Improved mood",
                    "Enhanced performance",
                ],
                "common_mistakes": ["Inconsistent schedule", "Late caffeine intake"],
                "scientific_rationale": "Circadian rhythm regulation improves sleep quality",
                "progression_tips": ["Gradually adjust timing", "Track sleep quality"],
            },
            {
                "title": "Goal Setting",
                "category": "motivation",
                "difficulty": "medium",
                "time_required": "15 minutes",
                "description": "Set SMART fitness goals",
                "action_steps": [
                    "Write specific goals",
                    "Set measurable targets",
                    "Create timeline",
                ],
                "benefits": ["Clear direction", "Better motivation", "Track progress"],
                "common_mistakes": ["Vague goals", "Unrealistic timelines"],
                "scientific_rationale": "Goal-setting theory shows structured goals improve performance",
                "progression_tips": ["Review weekly", "Adjust as needed"],
            },
        ],
        "implementation_strategy": {
            "start_with": "Choose one tip to focus on first",
            "timeline": "Master one tip before adding another",
            "key_principles": [
                "Consistency over perfection",
                "Start small",
                "Track progress",
            ],
        },
        "priority_order": [
            "Start Small",
            "Hydrate First",
            "Sleep Schedule",
            "Goal Setting",
        ],
        "tracking_methods": [
            "Daily habit tracker",
            "Weekly check-ins",
            "Progress photos",
        ],
        "success_indicators": ["Increased energy", "Better mood", "Consistent habits"],
        "related_concepts": [
            "Habit formation",
            "Progressive overload",
            "Recovery optimization",
        ],
        "advanced_techniques": [
            "Periodization",
            "Advanced nutrition timing",
            "Biohacking techniques",
        ],
        "common_obstacles": [
            "Time constraints",
            "Lack of motivation",
            "Social pressure",
        ],
        "motivation_strategies": [
            "Find accountability partner",
            "Celebrate small wins",
            "Focus on how you feel",
        ],
    }

    openai_mock.post("/v1/chat/completions").respond(
        status_code=200,
        json={"choices": [{"message": {"content": json.dumps(tips_response)}}]},
    )
    return openai_mock


@pytest.fixture
def valid_headers():
    """Valid API headers for testing."""
    return {"Content-Type": "application/json", "X-API-Key": "test-key"}


@pytest.fixture
def invalid_headers():
    """Invalid API headers for testing."""
    return {"Content-Type": "application/json", "X-API-Key": "invalid-key"}


@pytest.fixture
def no_auth_headers():
    """Headers without authentication."""
    return {"Content-Type": "application/json"}
