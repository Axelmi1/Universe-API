import logging
import os
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import fit, nutri, tips

# Load environment variables only once at startup
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

# Logging configuration with file handling based on environment
log_handlers = [logging.StreamHandler(sys.stdout)]

# Add file handler only if explicitly enabled
if os.getenv("LOG_TO_FILE", "false").lower() == "true" and not os.getenv("PRODUCTION"):
    try:
        log_handlers.append(logging.FileHandler("api.log"))
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")

logging.basicConfig(
    level=logging.DEBUG if not os.getenv("PRODUCTION") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)

logger = logging.getLogger(__name__)


# API Key authentication
async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")):
    """Verify API key for request authentication"""
    master_key = os.getenv("MASTER_API_KEY")

    # Check if API key header is missing
    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Missing API key",
                "message": "Please provide an X-API-Key header",
            },
        )

    if not master_key:
        # Development mode - log warning but allow access
        if not os.getenv("PRODUCTION"):
            logger.warning("⚠️ No MASTER_API_KEY set - API running in development mode")
            return True
        else:
            raise HTTPException(
                status_code=500, detail="API authentication not configured"
            )

    if x_api_key != master_key:
        logger.warning(f"🔐 Invalid API key attempt from {x_api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid API key",
                "message": "Please provide a valid X-API-Key header",
            },
        )

    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Universe API starting up...")

    # Verify critical environment variables
    required_env_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise RuntimeError(f"Missing environment variables: {missing_vars}")

    # Security check
    if os.getenv("PRODUCTION") and not os.getenv("MASTER_API_KEY"):
        logger.error("🔒 MASTER_API_KEY required in production mode")
        raise RuntimeError("MASTER_API_KEY required in production")

    logger.info("✅ Environment variables validated")
    logger.info("✅ Universe API started successfully")

    yield

    # Shutdown
    logger.info("🛑 Universe API shutting down...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Universe API",
    description="""
    🌟 **Universe API** - Your Ultimate Health & Wellness Platform
    
    Advanced AI-powered API providing personalized fitness, nutrition, and wellness guidance.
    Built with cutting-edge technology to deliver scientifically-backed recommendations.
    
    ## Features
    
    🏋️ **Fitness & Workouts**
    - Personalized workout generation based on your profile
    - Exercise selection optimized for your equipment and goals
    - Progressive training programs with detailed instructions
    
    🥗 **Nutrition & Diet Planning**
    - Custom meal plans with precise macro calculations
    - Dietary restriction and allergy management
    - Shopping lists and meal prep optimization
    
    💡 **Health Tips & Advice**
    - Evidence-based wellness tips tailored to your needs
    - Multi-domain expertise (fitness, nutrition, mental health, sleep)
    - Implementation strategies and progress tracking
    
    ## Authentication
    All endpoints require an `X-API-Key` header with a valid API key.
    
    ## Technology Stack
    - **AI Engine**: GPT-4 powered recommendations with function calling
    - **Framework**: FastAPI with Pydantic validation
    - **Security**: API key authentication and input validation
    - **Documentation**: Auto-generated OpenAPI specs
    
    ## Getting Started
    1. Obtain your API key
    2. Choose your domain (fitness, nutrition, or tips)
    3. Provide your personal profile and goals
    4. Receive personalized, actionable recommendations
    
    Perfect for fitness apps, health platforms, or personal wellness tools.
    """,
    version="2.0.0",
    contact={
        "name": "Universe API Support",
        "email": "support@universe-api.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

# CORS configuration - more restrictive for production
allowed_origins = ["*"]  # Default for development
if os.getenv("PRODUCTION"):
    # In production, only allow specific domains
    allowed_origins = [
        "https://rapidapi.com",
        "https://app.rapidapi.com",
        "https://marketplace.rapidapi.com",
    ]
    # Add custom domains from environment
    if os.getenv("ALLOWED_ORIGINS"):
        allowed_origins.extend(os.getenv("ALLOWED_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to needed methods
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()

    # Log request (avoid logging sensitive data in production)
    if not os.getenv("PRODUCTION"):
        logger.info(
            f"📨 {request.method} {request.url.path} - Client: {request.client.host}"
        )
    else:
        logger.info(f"📨 {request.method} {request.url.path}")

    response = await call_next(request)

    # Log response time
    process_time = time.time() - start_time
    logger.info(
        f"⏱️ Request processed in {process_time:.3f}s - Status: {response.status_code}"
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors gracefully"""
    logger.error(
        f"❌ Unexpected error on {request.method} {request.url.path}: {str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": f"{int(time.time())}-{hash(str(request.url))}",
        },
    )


# Create public metadata routers
fitness_metadata_router = APIRouter(
    prefix="/api/v1/metadata/fitness", tags=["Fitness Metadata"]
)
nutrition_metadata_router = APIRouter(
    prefix="/api/v1/metadata/nutrition", tags=["Nutrition Metadata"]
)
tips_metadata_router = APIRouter(prefix="/api/v1/metadata/tips", tags=["Tips Metadata"])


# Fitness metadata routes
@fitness_metadata_router.get("/fitness-levels")
async def public_get_fitness_levels():
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


@fitness_metadata_router.get("/equipment")
async def public_get_equipment_options():
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


@fitness_metadata_router.get("/goals")
async def public_get_fitness_goals():
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


# Nutrition metadata routes
@nutrition_metadata_router.get("/dietary-preferences")
async def public_get_dietary_preferences():
    return {
        "dietary_preferences": [
            {
                "id": "no_restrictions",
                "name": "No Restrictions",
                "description": "No dietary restrictions",
            },
            {
                "id": "vegetarian",
                "name": "Vegetarian",
                "description": "No meat or fish",
            },
            {"id": "vegan", "name": "Vegan", "description": "No animal products"},
            {
                "id": "pescatarian",
                "name": "Pescatarian",
                "description": "Fish allowed, no other meat",
            },
            {
                "id": "keto",
                "name": "Ketogenic",
                "description": "Very low carb, high fat",
            },
            {
                "id": "paleo",
                "name": "Paleo",
                "description": "Whole foods, no processed",
            },
            {
                "id": "mediterranean",
                "name": "Mediterranean",
                "description": "Mediterranean diet pattern",
            },
            {
                "id": "gluten_free",
                "name": "Gluten Free",
                "description": "No gluten-containing foods",
            },
            {
                "id": "dairy_free",
                "name": "Dairy Free",
                "description": "No dairy products",
            },
            {
                "id": "low_sodium",
                "name": "Low Sodium",
                "description": "Reduced sodium intake",
            },
            {
                "id": "high_protein",
                "name": "High Protein",
                "description": "Increased protein focus",
            },
        ]
    }


@nutrition_metadata_router.get("/activity-levels")
async def public_get_activity_levels():
    return {
        "activity_levels": [
            {
                "id": "sedentary",
                "name": "Sedentary",
                "description": "Little to no exercise",
            },
            {
                "id": "lightly_active",
                "name": "Lightly Active",
                "description": "Light exercise 1-3 days/week",
            },
            {
                "id": "moderately_active",
                "name": "Moderately Active",
                "description": "Moderate exercise 3-5 days/week",
            },
            {
                "id": "very_active",
                "name": "Very Active",
                "description": "Hard exercise 6-7 days/week",
            },
            {
                "id": "extra_active",
                "name": "Extra Active",
                "description": "Very hard exercise, physical job",
            },
        ]
    }


@nutrition_metadata_router.get("/goals")
async def public_get_nutrition_goals():
    return {
        "goals": [
            {
                "id": "weight_loss",
                "name": "Weight Loss",
                "description": "Lose body weight",
            },
            {
                "id": "weight_gain",
                "name": "Weight Gain",
                "description": "Gain healthy weight",
            },
            {
                "id": "muscle_gain",
                "name": "Muscle Gain",
                "description": "Build muscle mass",
            },
            {
                "id": "maintenance",
                "name": "Maintenance",
                "description": "Maintain current weight",
            },
            {
                "id": "general_health",
                "name": "General Health",
                "description": "Overall health improvement",
            },
            {
                "id": "athletic_performance",
                "name": "Athletic Performance",
                "description": "Optimize performance",
            },
        ]
    }


# Tips metadata routes
@tips_metadata_router.get("/fitness-levels")
async def public_get_experience_levels():
    return {
        "fitness_levels": [
            {
                "id": "beginner",
                "name": "Beginner",
                "description": "New to the domain, needs foundational guidance",
            },
            {
                "id": "intermediate",
                "name": "Intermediate",
                "description": "Some experience, ready for structured approaches",
            },
            {
                "id": "advanced",
                "name": "Advanced",
                "description": "Significant experience, seeking optimization",
            },
            {
                "id": "expert",
                "name": "Expert",
                "description": "Extensive knowledge, interested in cutting-edge techniques",
            },
        ]
    }


@tips_metadata_router.get("/challenges")
async def public_get_challenges():
    return {
        "challenges": [
            {
                "id": "lack_of_motivation",
                "name": "Lack of Motivation",
                "description": "Struggling to stay motivated",
            },
            {
                "id": "time_constraints",
                "name": "Time Constraints",
                "description": "Limited time for health activities",
            },
            {
                "id": "budget_limitations",
                "name": "Budget Limitations",
                "description": "Financial constraints",
            },
            {
                "id": "lack_of_knowledge",
                "name": "Lack of Knowledge",
                "description": "Insufficient understanding",
            },
            {"id": "plateau", "name": "Plateau", "description": "Progress has stalled"},
            {
                "id": "lack_of_energy",
                "name": "Lack of Energy",
                "description": "Feeling tired or fatigued",
            },
            {
                "id": "social_support",
                "name": "Social Support",
                "description": "Lack of support from others",
            },
            {
                "id": "consistency",
                "name": "Consistency",
                "description": "Difficulty maintaining routine",
            },
        ]
    }


@tips_metadata_router.get("/activities")
async def public_get_preferred_activities():
    return {
        "activities": [
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
    }


@tips_metadata_router.get("/health-conditions")
async def public_get_health_conditions():
    return {
        "health_conditions": [
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
    }


# Include public metadata routers FIRST (these will be processed before authenticated routes)
app.include_router(fitness_metadata_router)
app.include_router(nutrition_metadata_router)
app.include_router(tips_metadata_router)

# Include routers with API key dependency (these come after public routes)
app.include_router(
    fit.router,
    prefix="/api/v1/fitness",
    tags=["Fitness & Workouts"],
    dependencies=[Depends(verify_api_key)],
)

app.include_router(
    nutri.router,
    prefix="/api/v1/nutrition",
    tags=["Nutrition & Diet"],
    dependencies=[Depends(verify_api_key)],
)

app.include_router(
    tips.router,
    prefix="/api/v1/tips",
    tags=["Health Tips & Advice"],
    dependencies=[Depends(verify_api_key)],
)


# Root endpoint (no auth required)
@app.get("/", tags=["System"])
async def root():
    """
    🏠 Welcome to Universe API

    Your gateway to personalized health and wellness recommendations.
    """
    return {
        "message": "Welcome to Universe API",
        "status": "operational",
        "version": "2.0.0",
        "description": "AI-powered health and wellness platform",
        "features": [
            "Personalized fitness programs",
            "Custom nutrition plans",
            "Evidence-based health tips",
        ],
        "authentication": "API key required (X-API-Key header)",
        "endpoints": {
            "fitness": "/api/v1/fitness",
            "nutrition": "/api/v1/nutrition",
            "tips": "/api/v1/tips",
        },
        "documentation": {"interactive": "/docs", "openapi": "/openapi.json"},
    }


# Health check endpoint (no auth required)
@app.get("/health", tags=["System"])
async def health_check():
    """
    🏥 API Health Check

    Returns the current health status of the API and its dependencies.
    """
    try:
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "version": "2.0.0",
            "checks": {
                "api": "ok",
                "environment": (
                    "ok" if os.getenv("OPENAI_API_KEY") else "missing_config"
                ),
                "authentication": (
                    "ok"
                    if os.getenv("MASTER_API_KEY") or not os.getenv("PRODUCTION")
                    else "missing_config"
                ),
            },
        }

        # Additional checks could be added here (database, external APIs, etc.)

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


# API information endpoint
@app.get("/api/v1/info", tags=["System"])
async def api_info():
    """
    ℹ️ API Information

    Provides detailed information about API capabilities and usage.
    """
    return {
        "api_name": "Universe API",
        "version": "2.0.0",
        "description": "Comprehensive health and wellness AI platform",
        "capabilities": {
            "fitness": {
                "description": "Personalized workout generation",
                "features": [
                    "Custom training programs",
                    "Exercise selection and progression",
                    "Equipment-based optimization",
                    "Injury consideration",
                ],
            },
            "nutrition": {
                "description": "Personalized nutrition planning",
                "features": [
                    "Macro and calorie calculation",
                    "Meal plan generation",
                    "Dietary restriction support",
                    "Shopping list optimization",
                ],
            },
            "tips": {
                "description": "Evidence-based health advice",
                "features": [
                    "Multi-domain expertise",
                    "Personalized recommendations",
                    "Implementation guidance",
                    "Progress tracking",
                ],
            },
        },
        "supported_formats": ["JSON"],
        "authentication": "API Key (if configured)",
        "rate_limits": "Dynamic based on usage",
        "support": {
            "documentation": "/docs",
            "openapi_spec": "/openapi.json",
            "contact": "support@universe-api.com",
        },
    }


# Run the application
if __name__ == "__main__":
    logger.info("🚀 Starting Universe API server...")
    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
