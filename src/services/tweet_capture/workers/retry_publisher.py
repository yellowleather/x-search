"""Retry queued tweets publishing."""
import asyncio
import logging

from app.config import settings
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def retry_queued_tweets(limit: int = 100):
    """Retry queued tweets."""
    firestore_service = FirestoreService(settings.gcp_project_id, settings.firestore_database)
    pubsub_service = PubSubService(settings.gcp_project_id, settings.pubsub_topic)
    queue_items = await firestore_service.get_pending_queue_items(limit=limit)
    logger.info("Processing %s queued tweets", len(queue_items))
    for item in queue_items:
        queue_id = item["id"]
        tweet_data = item["tweetData"]
        attempts = item.get("attempts", 0)
        user_id = item["userId"]
        if attempts >= 5:
            await firestore_service.update_queue_item_status(queue_id, "failed", attempts, "Max attempts reached")
            continue
        try:
            message_id = await pubsub_service.publish_tweet(tweet_data, user_id)
            await firestore_service.update_tweet_message_id(user_id, tweet_data["tweetId"], message_id)
            await firestore_service.delete_queue_item(queue_id)
            logger.info("Published queued tweet %s", tweet_data["tweetId"])
        except Exception as exc:  # pylint: disable=broad-except
            await firestore_service.update_queue_item_status(queue_id, "retrying", attempts + 1, str(exc))
            logger.error("Failed to publish queued tweet %s: %s", queue_id, exc)


if __name__ == "__main__":
    asyncio.run(retry_queued_tweets())
