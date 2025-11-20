# Tweet Capture Backend Service

FastAPI backend for securely receiving liked tweets from the Chrome extension, persisting them to Firestore, and publishing to Google Cloud Pub/Sub. Designed for Cloud Run deployment with serverless, low-cost components.

## Features

- JWT-based authentication (register/login/refresh).
- Tweet capture endpoint with deduplication and Pub/Sub publishing.
- Firestore persistence for users, sessions, tweets, and retry queue.
- Health check endpoint for monitoring.
- Background worker to retry queued tweets.

## Prerequisites

- Python 3.11+
- Google Cloud project with Firestore (Datastore mode) and Pub/Sub enabled.
- Service account credentials configured via Application Default Credentials when running locally.

## Setup

```bash
cd services/tweet_capture
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your project details and JWT secret
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080/docs for interactive API documentation.

## Key Environment Variables

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `FIRESTORE_DATABASE` | Firestore database name (`(default)` for most setups) |
| `PUBSUB_TOPIC` | Pub/Sub topic name (e.g., `tweet-likes-raw`) |
| `JWT_SECRET_KEY` | Secret used for signing JWTs |
| `ACCESS_TOKEN_EXPIRE_SECONDS` | Access token lifetime (default 3600s) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime (default 30 days) |

## Deployment (Cloud Run)

```bash
gcloud run deploy tweet-capture-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=your-project,JWT_SECRET_KEY=secret,PUBSUB_TOPIC=tweet-likes-raw"
```

Ensure Firestore and Pub/Sub APIs are enabled and the Pub/Sub topic exists:

```bash
gcloud services enable run.googleapis.com firestore.googleapis.com pubsub.googleapis.com
gcloud pubsub topics create tweet-likes-raw
```

## Background Worker

Run the retry worker manually or as a Cloud Run job:

```bash
python workers/retry_publisher.py
```

## Testing

Basic tests live under `tests/`. Run with:

```bash
pytest
```

Configure the Firestore emulator if you want isolated testing.

## API Surface

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/tweets/capture`
- `GET /api/health`

Refer to `src/services/tweet_capture/FEATURE_SPEC.md` for full behavior details.
