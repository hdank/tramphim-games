from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager

from .database import engine, Base
from .routers import game, admin
from .scheduler import start_scheduler, stop_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

# Create static directory if it doesn't exist
STATIC_DIR = Path("app/static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Lifespan context for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title="Memory Card Game API",
    description="Backend API for Memory Card Game with admin features",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - crucial for iframe embedding and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tramphim.com",
        "http://localhost:3000",      # Game frontend (dev)
        "http://localhost:5173",      # Game frontend (Vite dev)
        "http://localhost:4321",      # Tramphim frontend (dev)
        "http://localhost:4555",      # Tramphim frontend (dev - actual port)
        "http://localhost:8003",      # Tramphim backend (dev)
        "http://localhost:4446",      # Tramphim admin (dev)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(game.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {
        "message": "Memory Card Game API",
        "docs": "/docs",
        "game_endpoints": "/game",
        "admin_endpoints": "/admin"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
