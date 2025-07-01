from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_nutrition_info():
    return {"message": "Bienvenue dans la section Nutrition de Universe API"}

@router.get("/meal-plan")
async def get_meal_plan():
    return {"message": "Voici votre plan de repas personnalisé"}
