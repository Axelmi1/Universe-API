from fastapi import FastAPI
from app.routers import fit, nutri, tips

app = FastAPI(
    title="Universe API – Fit & Nutri",
    description="Your ultra-pro virtual coach, powered by AI",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Bienvenue sur Universe API - Votre coach virtuel IA", "version": "0.1.0"}

app.include_router(fit.router, prefix="/fit", tags=["Fit"])
app.include_router(nutri.router, prefix="/nutri", tags=["Nutri"])
app.include_router(tips.router, prefix="/tips", tags=["Tips"])
