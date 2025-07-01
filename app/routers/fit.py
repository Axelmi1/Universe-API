from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_fitness_info():
    return {"message": "Bienvenue dans la section Fitness de Universe API"}

@router.get("/workout")
async def get_workout():
    return {"message": "Voici votre programme d'entraînement personnalisé"}
