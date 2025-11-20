"""Health check route."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService

router = APIRouter()

firestore_service = FirestoreService(settings.gcp_project_id, settings.firestore_database)
pubsub_service = PubSubService(settings.gcp_project_id, settings.pubsub_topic)


@router.get("/health")
async def health_check():
    """Report dependency status."""
    firestore_status = "connected"
    pubsub_status = "connected"
    try:
        firestore_service.db.collection("users").limit(1).stream()
    except Exception:
        firestore_status = "disconnected"
    if not pubsub_service.check_health():
        pubsub_status = "disconnected"

    status_value = "healthy" if firestore_status == "connected" and pubsub_status == "connected" else "unhealthy"
    payload = {
        "status": status_value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {"firestore": firestore_status, "pubsub": pubsub_status},
        "version": settings.app_version,
    }
    if status_value == "healthy":
        return payload
    raise HTTPException(status_code=503, detail=payload)
