"""Firestore service wrapper."""
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter


class FirestoreService:
    """Encapsulates Firestore operations."""

    def __init__(self, project_id: str, database: str = "(default)") -> None:
        client = firestore.Client(project=project_id, database=database)
        self.db = client

    # User operations
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        users_ref = self.db.collection("users")
        query = users_ref.where(filter=FieldFilter("email", "==", email)).limit(1)
        docs = query.stream()
        doc = next(docs, None)
        if doc:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    async def create_user(self, user_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("users").document(user_id).set(data)

    # Session operations
    async def create_session(self, session_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("sessions").document(session_id).set(data)

    async def get_session_by_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        sessions_ref = self.db.collection("sessions")
        query = sessions_ref.where(filter=FieldFilter("refreshToken", "==", refresh_token)).limit(1)
        docs = query.stream()
        doc = next(docs, None)
        if doc:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None

    async def delete_session(self, session_id: str) -> None:
        self.db.collection("sessions").document(session_id).delete()

    # Tweet operations
    async def tweet_exists(self, user_id: str, tweet_id: str) -> bool:
        doc_id = f"{user_id}_{tweet_id}"
        return self.db.collection("tweets").document(doc_id).get().exists

    async def save_tweet(
        self,
        user_id: str,
        tweet_id: str,
        tweet_data: Dict[str, Any],
        pubsub_message_id: Optional[str] = None,
    ) -> None:
        doc_id = f"{user_id}_{tweet_id}"
        self.db.collection("tweets").document(doc_id).set(
            {
                "userId": user_id,
                "tweetId": tweet_id,
                "pubsubMessageId": pubsub_message_id,
                "rawData": tweet_data,
                "publishedAt": firestore.SERVER_TIMESTAMP,
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
        )

    async def update_tweet_message_id(self, user_id: str, tweet_id: str, message_id: str) -> None:
        doc_id = f"{user_id}_{tweet_id}"
        self.db.collection("tweets").document(doc_id).update({"pubsubMessageId": message_id})

    # Queue operations
    async def queue_tweet_for_retry(self, user_id: str, tweet_data: Dict[str, Any]) -> str:
        queue_ref = self.db.collection("queue").document()
        queue_ref.set(
            {
                "userId": user_id,
                "tweetData": tweet_data,
                "status": "pending",
                "attempts": 0,
                "lastAttemptAt": None,
                "errorMessage": None,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )
        return queue_ref.id

    async def get_pending_queue_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        queue_ref = self.db.collection("queue")
        query = queue_ref.where(filter=FieldFilter("status", "==", "pending")).limit(limit)
        items: List[Dict[str, Any]] = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            items.append(data)
        return items

    async def update_queue_item_status(
        self, queue_id: str, status: str, attempts: int, error_message: Optional[str] = None
    ) -> None:
        self.db.collection("queue").document(queue_id).update(
            {
                "status": status,
                "attempts": attempts,
                "lastAttemptAt": firestore.SERVER_TIMESTAMP,
                "errorMessage": error_message,
                "updatedAt": firestore.SERVER_TIMESTAMP,
            }
        )

    async def delete_queue_item(self, queue_id: str) -> None:
        self.db.collection("queue").document(queue_id).delete()
