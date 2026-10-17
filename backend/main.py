import sys
from pathlib import Path
_repo_root = str(Path(__file__).resolve().parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

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
        from backend.utils.migrate_adaptive import migrate_database as migrate_adaptive
        migrate_adaptive()
        from backend.utils.migrate_assessments import run_assessment_migrations
        run_assessment_migrations()

        # Ensure password_reset_otps columns in PostgreSQL and SQLite
        from sqlalchemy import text
        with engine.connect() as conn:
            if engine.dialect.name == "postgresql":
                conn.execute(text("ALTER TABLE password_reset_otps ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0"))
                conn.execute(text("ALTER TABLE password_reset_otps ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64)"))
                conn.execute(text("ALTER TABLE password_reset_otps ALTER COLUMN otp_code TYPE VARCHAR(64)"))
                conn.commit()
            elif engine.dialect.name == "sqlite":
                res = conn.execute(text("PRAGMA table_info(password_reset_otps)")).fetchall()
                col_names = [r[1] for r in res]
                if "attempts" not in col_names:
                    conn.execute(text("ALTER TABLE password_reset_otps ADD COLUMN attempts INTEGER DEFAULT 0"))
                if "reset_token" not in col_names:
                    conn.execute(text("ALTER TABLE password_reset_otps ADD COLUMN reset_token VARCHAR(64)"))
                conn.commit()
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
    description="AdaptIQ - Adaptive Learning & Assessment Platform with Evidence-Based Integrity Signals & Sandbox Execution",
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
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
app.include_router(auth_router)  # Fallback for direct /auth requests
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
    import os
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False
    )
