import pytest
from pydantic import ValidationError

from app.models.tweet import TweetCaptureRequest


def test_tweet_model_validates_required_fields():
    payload = {
        "tweetId": "1234567890",
        "tweetText": "hello",
        "authorUsername": "user",
    }
    model = TweetCaptureRequest(**payload)
    assert model.tweetId == "1234567890"


def test_tweet_model_requires_text():
    payload = {
        "tweetId": "123",
        "authorUsername": "user",
    }
    with pytest.raises(ValidationError):
        TweetCaptureRequest(**payload)
