from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_database
from app.api import health, reports, clusters, dashboard, pipeline


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize persistent storage before serving requests."""
    init_database()
    yield


app = FastAPI(
    title="SIH26165 OSHA Safety Incident & Hazard Pattern Analytics Engine",
    description="Backend API for OSHA Incident Cleaning, NLP Precursor Extraction, Vector Similarity, HDBSCAN Clustering, Risk Scoring, and Trend Forecasting.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(reports.router)
app.include_router(clusters.router)
app.include_router(dashboard.router)
app.include_router(pipeline.router)
