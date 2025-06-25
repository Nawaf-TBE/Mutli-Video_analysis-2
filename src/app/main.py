# FastAPI app entrypoint 
import os
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .api.main_routes import router as api_router
from .db import init_db, check_db_health, close_db_connections, get_db_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Multi-Video Analysis API...")
    try:
        # Initialize database
        init_db()
        
        # Verify database health
        if not check_db_health():
            logger.error("Database health check failed during startup")
            raise Exception("Database initialization failed")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Video Analysis API...")
    try:
        # Close database connections
        close_db_connections()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")

app = FastAPI(
    title="Multi-Video Analysis API",
    description="API for analyzing and processing multiple videos with transcript and visual search capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Multi-Video Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    """
    try:
        # Check database health
        db_healthy = check_db_health()
        
        # Get database info
        db_info = get_db_info()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": {
                "healthy": db_healthy,
                "type": db_info.get("database_type", "unknown"),
                "engine": db_info.get("engine_name", "unknown")
            },
            "api": {
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            }
        }
        
        if not db_healthy:
            return JSONResponse(
                status_code=503,
                content=health_status
            )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/db/info")
async def database_info():
    """
    Get detailed database information.
    """
    try:
        return get_db_info()
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("ENVIRONMENT") == "development" else "An unexpected error occurred"
        }
    )