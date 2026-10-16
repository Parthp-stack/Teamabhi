from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from backend.config import settings
from backend.database import engine, Base, SessionLocal
import backend.models # Ensure all models are loaded
from backend.utils.seed_data import seed_database

# Import routers
from backend.routes.auth import router as auth_router
from backend.routes.courses import router as courses_router
from backend.routes.concepts import router as concepts_router
from backend.routes.mastery import router as mastery_router
from backend.routes.learning import router as learning_router
from backend.routes.coding import router as coding_router
from backend.routes.sessions import router as sessions_router
from backend.routes.integrity import router as integrity_router
from backend.routes.explanation import router as explanation_router
from backend.routes.trainer import router as trainer_router
from backend.routes.ai import router as ai_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adaptive_portal")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    try:
        from backend.utils.migrate_phase3 import migrate_database
        migrate_database()
    except Exception as e:
        logger.warning(f"Migration notice: {e}")
    
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("Application shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Adaptive Learning & Assessment Portal with Evidence-Based Integrity Signals & Sandbox Execution",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe error handler to protect against leaking internal stack traces
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Our engineering team has been notified."}
    )

# Health check
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected",
        "sandbox_mode": settings.SANDBOX_MODE
    }

# Register API routers
app.include_router(auth_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(concepts_router, prefix="/api")
app.include_router(mastery_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(coding_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(integrity_router, prefix="/api")
app.include_router(explanation_router, prefix="/api")
app.include_router(trainer_router, prefix="/api")
app.include_router(ai_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
