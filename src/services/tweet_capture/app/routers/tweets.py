"""Tweet capture routes."""
from fastapi import APIRouter, Depends

from app.config import settings
from app.dependencies import get_current_user
from app.models.tweet import TweetCaptureRequest, TweetCaptureResponse
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService
from app.services.tweet_service import TweetService

router = APIRouter()

firestore_service = FirestoreService(settings.gcp_project_id, settings.firestore_database)
pubsub_service = PubSubService(settings.gcp_project_id, settings.pubsub_topic)
tweet_service = TweetService(firestore_service, pubsub_service)


@router.post("/capture", response_model=TweetCaptureResponse)
async def capture_tweet(
    payload: TweetCaptureRequest, user_id: str = Depends(get_current_user)
) -> TweetCaptureResponse:
    """Capture liked tweet payloads."""
    result = await tweet_service.capture_tweet(payload.model_dump(), user_id)
    return TweetCaptureResponse(**result)
