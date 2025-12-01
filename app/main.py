from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.session import engine
from app.db.base import Base
from app.api.v1.customers import router as customers_router
from app.api.v1.orders import router as orders_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.ai_recommendations import router as ai_recommendations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: Close database connection
    await engine.dispose()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Customer Orders & Recommendation Engine (CORE)",
    description="FastAPI backend for customer orders and recommendation engine",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Register API routers
app.include_router(customers_router)
app.include_router(orders_router)
app.include_router(recommendations_router)
app.include_router(ai_recommendations_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
