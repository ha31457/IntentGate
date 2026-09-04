import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.redis import redis_manager
from app.db.session import init_db
from app.db.seed import seed_data
from app.api.v1.intents import router as intents_router
from app.api.v1.agents import router as agents_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.chaos import router as chaos_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.dashboard import router as dashboard_router

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger("intentgate.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing IntentGate Backend Runtime...")
    await redis_manager.init_redis()
    await init_db()
    await seed_data()
    logger.info("IntentGate Backend operational and ready to receive requests.")
    yield
    logger.info("Shutting down IntentGate Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Runtime Trust Layer for Autonomous Commerce Agents",
    lifespan=lifespan
)

# CORS Configuration for Next.js Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Checks
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME, "version": settings.VERSION}

@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    redis_status = "connected" if not redis_manager.is_mock else "mock_fallback"
    return {
        "status": "ready",
        "redis": redis_status,
        "database": "sqlite_aiosqlite",
        "environment": settings.ENVIRONMENT
    }

# Register API Router
api_v1 = FastAPI(title="IntentGate V1 API")
api_v1.include_router(intents_router)
api_v1.include_router(agents_router)
api_v1.include_router(transactions_router)
api_v1.include_router(chaos_router)
api_v1.include_router(webhooks_router)
api_v1.include_router(dashboard_router)

app.mount(settings.API_V1_STR, api_v1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
