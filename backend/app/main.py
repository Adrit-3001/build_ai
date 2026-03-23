from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.study import router as study_router

app = FastAPI(title="Study Buddy Backend")

app.include_router(health_router)
app.include_router(study_router)


@app.get("/")
def root():
    return {
        "message": "Study Buddy backend is running.",
        "docs": "/docs"
    }