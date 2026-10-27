
from fastapi import FastAPI

from app.matching import find_matches
from app.models import (
    HealthResponse,
    MatchRequest,
    MatchResponse,
)


app = FastAPI(
    title="ChargeShare Matching Service",
    description=(
        "Emergency EV matching for compatible donor vehicles "
        "and charging stations within a 5 km radius."
    ),
    version="0.4.0",
)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to ChargeShare Matching Service",
        "docs": "/docs",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)
def health_check():
    return {
        "status": "healthy",
        "service": "chargeshare-matching",
    }


@app.post(
    "/match",
    response_model=MatchResponse,
    response_model_by_alias=True,
    tags=["Matching"],
)
def match_driver(request: MatchRequest):
    result = find_matches(request)

    return MatchResponse(
        mode=request.mode,
        battery_percent=request.battery_percent,
        status=result["status"],
        message=result["message"],
        matches=result["matches"],
    )
