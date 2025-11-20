"""Google Cloud Pub/Sub helper service."""
import json
from datetime import datetime, timezone
from typing import Any, Dict

from google.cloud import pubsub_v1


class PubSubService:
    """Publish messages to Pub/Sub."""

    def __init__(self, project_id: str, topic: str) -> None:
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic)

    async def publish_tweet(self, tweet_data: Dict[str, Any], user_id: str) -> str:
        """Publish tweet payload."""
        payload = {
            "data": tweet_data,
            "attributes": {
                "userId": user_id,
                "source": "chrome-extension",
                "capturedAt": datetime.now(timezone.utc).isoformat(),
            },
        }
        data = json.dumps(payload).encode("utf-8")
        future = self.publisher.publish(self.topic_path, data, **payload["attributes"])
        message_id = future.result(timeout=10)
        return message_id

    def check_health(self) -> bool:
        """Best-effort health check."""
        try:
            self.publisher.get_topic(request={"topic": self.topic_path})
            return True
        except Exception:
            return False
