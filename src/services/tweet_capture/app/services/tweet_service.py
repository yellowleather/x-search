"""Tweet capture business logic."""
from typing import Any, Dict

from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService


class TweetService:
    """Handles capture, deduplication, and publishing."""

    def __init__(self, firestore: FirestoreService, pubsub: PubSubService) -> None:
        self.firestore = firestore
        self.pubsub = pubsub

    async def capture_tweet(self, tweet_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Process tweet capture flow."""
        tweet_id = tweet_data["tweetId"]
        if await self.firestore.tweet_exists(user_id, tweet_id):
            return {"status": "duplicate", "tweetId": tweet_id, "message": "Tweet already captured"}

        try:
            message_id = await self.pubsub.publish_tweet(tweet_data, user_id)
            await self.firestore.save_tweet(user_id, tweet_id, tweet_data, message_id)
            return {"status": "published", "tweetId": tweet_id, "messageId": message_id}
        except Exception:
            await self.firestore.save_tweet(user_id, tweet_id, tweet_data, None)
            await self.firestore.queue_tweet_for_retry(user_id, tweet_data)
            return {
                "status": "queued",
                "tweetId": tweet_id,
                "message": "Queued for retry - will publish when service recovers",
            }
