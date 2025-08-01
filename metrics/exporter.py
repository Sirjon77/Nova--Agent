"""Expose Prometheus metrics."""
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

router = APIRouter()
requests_total = Counter("requests_total", "Total HTTP requests")

@router.middleware("http")
async def count_requests(request, call_next):
    requests_total.inc()
    return await call_next(request)

@router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
