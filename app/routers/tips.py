from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_tips_info():
    return {"message": "Bienvenue dans la section Conseils de Universe API"}

@router.get("/daily")
async def get_daily_tips():
    return {"message": "Voici vos conseils du jour"}
