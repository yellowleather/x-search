"""Pydantic models for tweet capture."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class TweetCaptureRequest(BaseModel):
    tweetId: str = Field(..., min_length=5, max_length=32)
    tweetUrl: Optional[HttpUrl] = None
    tweetText: str = Field(..., max_length=5000)
    authorUsername: str
    authorDisplayName: Optional[str] = None
    timestamp: Optional[datetime] = None
    capturedAt: Optional[int] = None
    isReply: bool = False
    isRetweet: bool = False
    isQuoteTweet: bool = False
    isThread: bool = False
    threadId: Optional[str] = None
    parentTweetId: Optional[str] = None
    conversationId: Optional[str] = None
    hasImage: bool = False
    hasVideo: bool = False
    hasLink: bool = False


class TweetCaptureResponse(BaseModel):
    status: str
    tweetId: str
    message: Optional[str] = None
    messageId: Optional[str] = None
