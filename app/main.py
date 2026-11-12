from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.rooms import router as rooms_router

app = FastAPI(title="StudyMate API", version="0.1.0")

# Register each route group with the main FastAPI application.
app.include_router(auth_router)
app.include_router(rooms_router)


@app.get("/", tags=["system"])
def home() -> dict[str, str]:
    """Simple route to show that the API process is running."""
    return {"message": "StudyMate API is running"}