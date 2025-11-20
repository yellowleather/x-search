# FEATURE SPECIFICATION: Tweet Capture Backend API Service (Google Cloud Native)

## PROJECT OVERVIEW
Build a secure, serverless backend API service on Google Cloud that receives liked tweet data from a Chrome extension, authenticates users via JWT, stores tweets in Firestore for audit/resilience, and publishes to Google Cloud Pub/Sub for downstream processing. Optimized for personal single-user use with minimal cost (target: $0/month).

## SERVICE PURPOSE

**Core Responsibilities:**
1. User authentication and session management (JWT-based)
2. Receive tweet capture requests from Chrome extension
3. Store tweets in Firestore (deduplication + resilience)
4. Publish tweets to Google Cloud Pub/Sub topic
5. Handle Pub/Sub failures gracefully with retry queue

**Non-Responsibilities (Out of Scope):**
- Tweet enrichment (handled by downstream workers)
- Embedding generation (handled by downstream workers)
- Semantic search (separate service)
- Multi-user management UI (single user focus)

## ARCHITECTURE OVERVIEW
```
┌─────────────────────┐
│ Chrome Extension    │
│ (HTTPS requests)    │
└──────────┬──────────┘
           │ POST /api/tweets/capture
           │ Authorization: Bearer <JWT>
           ▼
┌─────────────────────────────────────┐
│  Google Cloud Run (Serverless)      │
│  FastAPI Backend                    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Auth Middleware             │   │
│  │ • Validate JWT              │   │
│  │ • Extract user_id           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Tweet Capture Handler       │   │
│  │ • Validate tweet data       │   │
│  │ • Check duplicates          │   │
│  │ • Store in Firestore        │   │
│  │ • Publish to Pub/Sub        │   │
│  └─────────────────────────────┘   │
└───┬─────────────────────┬───────────┘
    │                     │
    ▼                     ▼
┌─────────────┐    ┌──────────────────┐
│  Firestore  │    │ Google Pub/Sub   │
│  (NoSQL)    │    │ tweet-likes-raw  │
│             │    │                  │
│ • users     │    │ (31-day retain)  │
│ • tweets    │    └──────────────────┘
│ • sessions  │
│ • queue     │
└─────────────┘
```

**Key Architectural Decisions:**
- **All Serverless**: Everything scales to zero when not in use
- **All Google Cloud**: Native GCP services only
- **NoSQL**: Firestore instead of relational database
- **Cost Target**: $0/month (stay within free tiers)

## TECHNOLOGY STACK

### Core Services
- **Compute**: Google Cloud Run (serverless container platform)
- **Database**: Firestore in Datastore mode (serverless NoSQL)
- **Queue**: Google Cloud Pub/Sub (message queue)
- **Secrets**: Cloud Run environment variables
- **Logging**: Cloud Logging (built-in)
- **Monitoring**: Cloud Monitoring (built-in)

### Application Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI (async web framework)
- **Database Client**: google-cloud-firestore
- **Queue Client**: google-cloud-pubsub
- **Authentication**: python-jose (JWT), passlib (password hashing)

### Why This Stack?
- **FastAPI**: Modern, fast, type-safe, auto-generated docs
- **Firestore**: Serverless, scalable, free tier generous
- **Cloud Run**: Serverless, scales to zero, simple deployment
- **All GCP**: Single platform, integrated services, unified billing

### Dependencies (requirements.txt)
```txt
fastapi==0.104.0
uvicorn[standard]==0.24.0
google-cloud-firestore==2.13.1
google-cloud-pubsub==2.18.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
```

## API ENDPOINTS SPECIFICATION

### 1. POST /api/auth/register

**Purpose**: Create new user account

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Validation:**
- Email: Valid email format, unique
- Password: Min 8 chars, at least 1 uppercase, 1 lowercase, 1 number

**Response: 201 Created**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "refresh_abc123xyz...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**Error Responses:**
- 400 Bad Request: Invalid email/password format
- 409 Conflict: Email already exists

**Firestore Operations:**
```python
# Create user document
db.collection('users').document(user_id).set({
    'email': email,
    'passwordHash': hashed_password,
    'isActive': True,
    'createdAt': firestore.SERVER_TIMESTAMP
})

# Create session document
db.collection('sessions').document(session_id).set({
    'userId': user_id,
    'refreshToken': refresh_token,
    'expiresAt': expiry_datetime,
    'createdAt': firestore.SERVER_TIMESTAMP
})
```

### 2. POST /api/auth/login

**Purpose**: Authenticate existing user

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response: 200 OK**
```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "refresh_abc123xyz...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid email or password
- 403 Forbidden: Account disabled

**Firestore Operations:**
```python
# Find user by email
users = db.collection('users').where('email', '==', email).limit(1).stream()
user = next(users, None)

# Verify password
if not verify_password(password, user.get('passwordHash')):
    raise AuthError

# Create new session
db.collection('sessions').document(session_id).set({...})
```

### 3. POST /api/auth/refresh

**Purpose**: Get new access token using refresh token

**Request:**
```json
{
  "refreshToken": "refresh_abc123xyz..."
}
```

**Response: 200 OK**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid or expired refresh token

**Firestore Operations:**
```python
# Find session by refresh token
sessions = db.collection('sessions').where('refreshToken', '==', refresh_token).limit(1).stream()
session = next(sessions, None)

# Check expiry
if datetime.now() > session.get('expiresAt'):
    raise TokenExpired

# Generate new access token
```

### 4. POST /api/tweets/capture

**Purpose**: Receive and process captured tweet from Chrome extension

**Authentication**: Required (JWT Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

**Request Body:**
```json
{
  "tweetId": "1234567890123456789",
  "tweetUrl": "https://x.com/username/status/1234567890123456789",
  "tweetText": "This is the tweet content...",
  "authorUsername": "username",
  "authorDisplayName": "Display Name",
  "timestamp": "2024-11-19T10:30:00Z",
  "capturedAt": 1700395800000,
  "isReply": false,
  "isRetweet": false,
  "isQuoteTweet": false,
  "isThread": false,
  "threadId": "1234567890123456789",
  "parentTweetId": null,
  "conversationId": "1234567890123456789",
  "hasImage": false,
  "hasVideo": false,
  "hasLink": false
}
```

**Validation:**
- tweetId: Required, string, 15-20 digits
- tweetText: Required, string, max 5000 chars
- authorUsername: Required, string
- All boolean fields: default to false if missing

**Response: 200 OK (Success - Published)**
```json
{
  "status": "published",
  "tweetId": "1234567890123456789",
  "messageId": "projects/my-project/topics/tweet-likes-raw/messages/1234567890"
}
```

**Response: 200 OK (Pub/Sub Down - Queued)**
```json
{
  "status": "queued",
  "tweetId": "1234567890123456789",
  "message": "Queued for retry - will publish when service recovers"
}
```

**Response: 200 OK (Duplicate)**
```json
{
  "status": "duplicate",
  "tweetId": "1234567890123456789",
  "message": "Tweet already captured"
}
```

**Error Responses:**
- 401 Unauthorized: Missing or invalid JWT token
- 400 Bad Request: Invalid tweet data
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Critical failure

**Processing Flow:**
1. Validate JWT token → Extract user_id
2. Validate tweet data schema
3. Check if tweet exists in Firestore (userId + tweetId)
4. If exists: Return "duplicate" status
5. Try to publish to Pub/Sub:
   - Success: Store in Firestore with messageId, return "published"
   - Failure: Store in Firestore + queue collection, return "queued"

**Firestore Operations:**
```python
# Check for duplicate
tweet_ref = db.collection('tweets').document(f"{user_id}_{tweet_id}")
if tweet_ref.get().exists:
    return {"status": "duplicate"}

# Try to publish to Pub/Sub
try:
    message_id = pubsub_service.publish(tweet_data)
    
    # Store with message_id
    tweet_ref.set({
        'userId': user_id,
        'tweetId': tweet_id,
        'pubsubMessageId': message_id,
        'rawData': tweet_data,
        'publishedAt': firestore.SERVER_TIMESTAMP
    })
    
    return {"status": "published", "messageId": message_id}
    
except Exception:
    # Pub/Sub failed - store and queue
    tweet_ref.set({
        'userId': user_id,
        'tweetId': tweet_id,
        'pubsubMessageId': None,
        'rawData': tweet_data,
        'publishedAt': firestore.SERVER_TIMESTAMP
    })
    
    # Add to retry queue
    db.collection('queue').add({
        'userId': user_id,
        'tweetData': tweet_data,
        'status': 'pending',
        'attempts': 0,
        'createdAt': firestore.SERVER_TIMESTAMP
    })
    
    return {"status": "queued"}
```

### 5. GET /api/health

**Purpose**: Health check endpoint for monitoring

**Authentication**: Not required

**Response: 200 OK**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-19T10:30:00Z",
  "services": {
    "firestore": "connected",
    "pubsub": "connected"
  },
  "version": "1.0.0"
}
```

**Response: 503 Service Unavailable**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-11-19T10:30:00Z",
  "services": {
    "firestore": "disconnected",
    "pubsub": "connected"
  },
  "version": "1.0.0"
}
```

## FIRESTORE DATA MODEL

### Collection: users
```javascript
// Document ID: {user_id} (UUID)
{
  "email": "user@example.com",
  "passwordHash": "$2b$12$...",
  "isActive": true,
  "createdAt": Timestamp,
  "updatedAt": Timestamp
}

// Indexes:
// - email (for login lookups)
```

### Collection: sessions
```javascript
// Document ID: {session_id} (UUID)
{
  "userId": "user-uuid",
  "refreshToken": "refresh_abc123...",
  "expiresAt": Timestamp,
  "createdAt": Timestamp,
  "lastUsedAt": Timestamp
}

// Indexes:
// - refreshToken (for token validation)
// - userId (for user session management)
// - expiresAt (for cleanup queries)
```

### Collection: tweets
```javascript
// Document ID: {user_id}_{tweet_id} (composite key for uniqueness)
{
  "userId": "user-uuid",
  "tweetId": "1234567890123456789",
  "pubsubMessageId": "projects/.../messages/123",
  "rawData": {
    "tweetText": "...",
    "authorUsername": "...",
    // ... all tweet fields
  },
  "publishedAt": Timestamp,
  "createdAt": Timestamp
}

// Indexes:
// - userId (for querying user's tweets)
// - publishedAt (for time-based queries)
```

### Collection: queue
```javascript
// Document ID: auto-generated
{
  "userId": "user-uuid",
  "tweetData": {
    // Full tweet object
  },
  "status": "pending",  // pending, retrying, failed
  "attempts": 0,
  "lastAttemptAt": Timestamp,
  "errorMessage": null,
  "createdAt": Timestamp,
  "updatedAt": Timestamp
}

// Indexes:
// - status (for retry queries)
// - createdAt (for FIFO processing)
```

## PROJECT STRUCTURE
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration (env vars)
│   │
│   ├── models/                 # Pydantic models (not database)
│   │   ├── __init__.py
│   │   ├── auth.py            # Auth request/response models
│   │   └── tweet.py           # Tweet request/response models
│   │
│   ├── routers/                # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py            # Auth endpoints
│   │   ├── tweets.py          # Tweet endpoints
│   │   └── health.py          # Health check
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── tweet_service.py   # Tweet capture logic
│   │   ├── firestore_service.py  # Firestore operations
│   │   └── pubsub_service.py  # Pub/Sub operations
│   │
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── jwt.py             # JWT utilities
│   │   └── password.py        # Password hashing
│   │
│   └── dependencies.py         # FastAPI dependencies
│
├── workers/                    # Background jobs (optional)
│   └── retry_publisher.py      # Retry queued tweets
│
├── tests/                      # Tests
│   ├── test_auth.py
│   └── test_tweets.py
│
├── .env.example                # Environment variables template
├── .gitignore
├── .dockerignore
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── cloudbuild.yaml            # Cloud Build config (optional)
└── README.md                   # Documentation
```

## CORE IMPLEMENTATION FILES

### app/main.py
```python
"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tweets, health
from app.config import settings

app = FastAPI(
    title="Tweet Capture API",
    description="Backend service for capturing liked tweets",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Chrome extensions
        "http://localhost:3000"  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["Tweets"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # Firestore client initializes automatically via Application Default Credentials
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass
```

### app/config.py
```python
"""
Configuration management using environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "production"  # development, production
    
    # JWT Configuration
    JWT_SECRET_KEY: str  # REQUIRED: Set via environment variable
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Google Cloud Configuration
    GCP_PROJECT_ID: str  # REQUIRED: Your GCP project ID
    PUBSUB_TOPIC: str = "tweet-likes-raw"
    
    # Firestore Configuration
    FIRESTORE_DATABASE: str = "(default)"  # Default database
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### app/services/firestore_service.py
```python
"""
Firestore database operations
"""
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class FirestoreService:
    def __init__(self, project_id: str, database: str = "(default)"):
        self.db = firestore.Client(project=project_id, database=database)
    
    # User operations
    async def create_user(self, email: str, password_hash: str) -> str:
        """Create a new user and return user_id"""
        user_id = str(uuid.uuid4())
        user_ref = self.db.collection('users').document(user_id)
        
        user_ref.set({
            'email': email,
            'passwordHash': password_hash,
            'isActive': True,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return user_id
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        users_ref = self.db.collection('users')
        query = users_ref.where(filter=FieldFilter('email', '==', email)).limit(1)
        
        docs = query.stream()
        user_doc = next(docs, None)
        
        if user_doc:
            user_data = user_doc.to_dict()
            user_data['id'] = user_doc.id
            return user_data
        return None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        user = await self.get_user_by_email(email)
        return user is not None
    
    # Session operations
    async def create_session(self, user_id: str, refresh_token: str, expires_at: datetime) -> str:
        """Create a new session and return session_id"""
        session_id = str(uuid.uuid4())
        session_ref = self.db.collection('sessions').document(session_id)
        
        session_ref.set({
            'userId': user_id,
            'refreshToken': refresh_token,
            'expiresAt': expires_at,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastUsedAt': firestore.SERVER_TIMESTAMP
        })
        
        return session_id
    
    async def get_session_by_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Find session by refresh token"""
        sessions_ref = self.db.collection('sessions')
        query = sessions_ref.where(filter=FieldFilter('refreshToken', '==', refresh_token)).limit(1)
        
        docs = query.stream()
        session_doc = next(docs, None)
        
        if session_doc:
            session_data = session_doc.to_dict()
            session_data['id'] = session_doc.id
            return session_data
        return None
    
    # Tweet operations
    async def tweet_exists(self, user_id: str, tweet_id: str) -> bool:
        """Check if tweet already captured"""
        doc_id = f"{user_id}_{tweet_id}"
        tweet_ref = self.db.collection('tweets').document(doc_id)
        return tweet_ref.get().exists
    
    async def save_tweet(
        self, 
        user_id: str, 
        tweet_id: str, 
        tweet_data: Dict[str, Any],
        pubsub_message_id: Optional[str] = None
    ) -> None:
        """Save tweet to Firestore"""
        doc_id = f"{user_id}_{tweet_id}"
        tweet_ref = self.db.collection('tweets').document(doc_id)
        
        tweet_ref.set({
            'userId': user_id,
            'tweetId': tweet_id,
            'pubsubMessageId': pubsub_message_id,
            'rawData': tweet_data,
            'publishedAt': firestore.SERVER_TIMESTAMP,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
    
    async def update_tweet_message_id(
        self, 
        user_id: str, 
        tweet_id: str, 
        message_id: str
    ) -> None:
        """Update tweet with Pub/Sub message ID after successful publish"""
        doc_id = f"{user_id}_{tweet_id}"
        tweet_ref = self.db.collection('tweets').document(doc_id)
        tweet_ref.update({'pubsubMessageId': message_id})
    
    # Queue operations
    async def queue_tweet_for_retry(self, user_id: str, tweet_data: Dict[str, Any]) -> str:
        """Add tweet to retry queue"""
        queue_ref = self.db.collection('queue').document()
        
        queue_ref.set({
            'userId': user_id,
            'tweetData': tweet_data,
            'status': 'pending',
            'attempts': 0,
            'lastAttemptAt': None,
            'errorMessage': None,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return queue_ref.id
    
    async def get_pending_queue_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending items from retry queue"""
        queue_ref = self.db.collection('queue')
        query = queue_ref.where(filter=FieldFilter('status', '==', 'pending')).limit(limit)
        
        items = []
        for doc in query.stream():
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        return items
    
    async def update_queue_item_status(
        self, 
        queue_id: str, 
        status: str, 
        attempts: int,
        error_message: Optional[str] = None
    ) -> None:
        """Update queue item status after retry attempt"""
        queue_ref = self.db.collection('queue').document(queue_id)
        
        queue_ref.update({
            'status': status,
            'attempts': attempts,
            'lastAttemptAt': firestore.SERVER_TIMESTAMP,
            'errorMessage': error_message,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
    
    async def delete_queue_item(self, queue_id: str) -> None:
        """Delete item from queue after successful processing"""
        queue_ref = self.db.collection('queue').document(queue_id)
        queue_ref.delete()
```

### app/services/pubsub_service.py
```python
"""
Google Cloud Pub/Sub operations
"""
from google.cloud import pubsub_v1
import json
from datetime import datetime
from typing import Dict, Any

class PubSubService:
    def __init__(self, project_id: str, topic_name: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
    
    async def publish_tweet(self, tweet_data: Dict[str, Any], user_id: str) -> str:
        """
        Publish tweet to Pub/Sub topic
        Returns: message_id if successful
        Raises: Exception if publish fails
        """
        message_payload = {
            "data": tweet_data,
            "attributes": {
                "userId": user_id,
                "captureDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "source": "chrome-extension",
                "version": "1.0.0"
            }
        }
        
        # Encode message as JSON bytes
        message_bytes = json.dumps(message_payload).encode('utf-8')
        
        # Publish with attributes
        future = self.publisher.publish(
            self.topic_path,
            message_bytes,
            **message_payload["attributes"]
        )
        
        # Wait for result with timeout
        try:
            message_id = future.result(timeout=10)
            return message_id
        except Exception as e:
            raise Exception(f"Failed to publish to Pub/Sub: {str(e)}")
    
    def check_health(self) -> bool:
        """Check if Pub/Sub service is accessible"""
        try:
            # Try to get topic metadata
            self.publisher.get_topic(request={"topic": self.topic_path})
            return True
        except Exception:
            return False
```

### app/services/tweet_service.py
```python
"""
Tweet capture business logic
"""
from typing import Dict, Any
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService

class TweetService:
    def __init__(self, firestore: FirestoreService, pubsub: PubSubService):
        self.firestore = firestore
        self.pubsub = pubsub
    
    async def capture_tweet(
        self, 
        tweet_data: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Main tweet capture logic:
        1. Check for duplicates
        2. Try to publish to Pub/Sub
        3. Store in Firestore
        4. Handle failures with queue
        """
        tweet_id = tweet_data['tweetId']
        
        # 1. Check if already exists
        if await self.firestore.tweet_exists(user_id, tweet_id):
            return {
                "status": "duplicate",
                "tweetId": tweet_id,
                "message": "Tweet already captured"
            }
        
        # 2. Try to publish to Pub/Sub first
        try:
            message_id = await self.pubsub.publish_tweet(tweet_data, user_id)
            
            # 3. Success - store in Firestore with message_id
            await self.firestore.save_tweet(
                user_id=user_id,
                tweet_id=tweet_id,
                tweet_data=tweet_data,
                pubsub_message_id=message_id
            )
            
            return {
                "status": "published",
                "tweetId": tweet_id,
                "messageId": message_id
            }
            
        except Exception as e:
            # 4. Pub/Sub failed - store in Firestore and queue for retry
            await self.firestore.save_tweet(
                user_id=user_id,
                tweet_id=tweet_id,
                tweet_data=tweet_data,
                pubsub_message_id=None
            )
            
            # Add to retry queue
            await self.firestore.queue_tweet_for_retry(user_id, tweet_data)
            
            return {
                "status": "queued",
                "tweetId": tweet_id,
                "message": "Queued for retry - will publish when service recovers"
            }
```

### app/services/auth_service.py
```python
"""
Authentication business logic
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from app.services.firestore_service import FirestoreService
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token
from app.config import settings
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, firestore: FirestoreService):
        self.firestore = firestore
    
    async def register(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        # Check if email already exists
        if await self.firestore.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user_id = await self.firestore.create_user(email, password_hash)
        
        # Create tokens
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.firestore.create_session(user_id, refresh_token, expires_at)
        
        return {
            "userId": user_id,
            "email": email,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "tokenType": "Bearer"
        }
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user"""
        # Find user
        user = await self.firestore.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(password, user['passwordHash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if not user.get('isActive', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled"
            )
        
        user_id = user['id']
        
        # Create tokens
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.firestore.create_session(user_id, refresh_token, expires_at)
        
        return {
            "userId": user_id,
            "email": email,
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "tokenType": "Bearer"
        }
    
    async def refresh(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        # Find session
        session = await self.firestore.get_session_by_refresh_token(refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check expiry
        if datetime.utcnow() > session['expiresAt']:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        user_id = session['userId']
        
        # Create new access token
        access_token = create_access_token({"sub": user_id})
        
        return {
            "accessToken": access_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "tokenType": "Bearer"
        }
```

### app/routers/tweets.py
```python
"""
Tweet capture API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.tweet import TweetCaptureRequest, TweetCaptureResponse
from app.services.tweet_service import TweetService
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter()

def get_tweet_service() -> TweetService:
    """Dependency to create TweetService instance"""
    firestore = FirestoreService(settings.GCP_PROJECT_ID, settings.FIRESTORE_DATABASE)
    pubsub = PubSubService(settings.GCP_PROJECT_ID, settings.PUBSUB_TOPIC)
    return TweetService(firestore, pubsub)

@router.post("/capture", response_model=TweetCaptureResponse)
async def capture_tweet(
    request: TweetCaptureRequest,
    user_id: str = Depends(get_current_user),
    tweet_service: TweetService = Depends(get_tweet_service)
):
    """
    Capture a liked tweet from Chrome extension
    
    Requires authentication via JWT token in Authorization header
    """
    try:
        result = await tweet_service.capture_tweet(
            tweet_data=request.dict(),
            user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to capture tweet: {str(e)}"
        )
```

### app/dependencies.py
```python
"""
FastAPI dependencies for authentication and services
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt import verify_access_token
from jose import JWTError

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency to extract and validate JWT token
    Returns user_id if valid, raises 401 if invalid
    """
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

## BACKGROUND WORKER: Retry Publisher

### workers/retry_publisher.py
```python
"""
Background job to retry publishing queued tweets to Pub/Sub

Deploy as:
- Cloud Run Job (scheduled)
- Cloud Scheduler (calls Cloud Run endpoint)
- Local cron job
"""
import asyncio
from google.cloud import firestore
from app.services.firestore_service import FirestoreService
from app.services.pubsub_service import PubSubService
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def retry_queued_tweets():
    """Retry publishing tweets that failed previously"""
    firestore_service = FirestoreService(
        settings.GCP_PROJECT_ID,
        settings.FIRESTORE_DATABASE
    )
    pubsub_service = PubSubService(
        settings.GCP_PROJECT_ID,
        settings.PUBSUB_TOPIC
    )
    
    # Get pending items
    queue_items = await firestore_service.get_pending_queue_items(limit=100)
    
    logger.info(f"Processing {len(queue_items)} queued tweets")
    
    for item in queue_items:
        queue_id = item['id']
        user_id = item['userId']
        tweet_data = item['tweetData']
        attempts = item['attempts']
        
        # Skip if too many attempts
        if attempts >= 5:
            logger.warning(f"Queue item {queue_id} exceeded max attempts")
            await firestore_service.update_queue_item_status(
                queue_id, 'failed', attempts, 'Max retry attempts exceeded'
            )
            continue
        
        try:
            # Try to publish
            message_id = await pubsub_service.publish_tweet(tweet_data, user_id)
            
            # Success - update tweet record
            await firestore_service.update_tweet_message_id(
                user_id,
                tweet_data['tweetId'],
                message_id
            )
            
            # Delete from queue
            await firestore_service.delete_queue_item(queue_id)
            
            logger.info(f"Successfully published queued tweet {tweet_data['tweetId']}")
            
        except Exception as e:
            # Failed - increment attempts
            await firestore_service.update_queue_item_status(
                queue_id, 'retrying', attempts + 1, str(e)
            )
            
            logger.error(f"Failed to publish queued tweet {queue_id}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(retry_queued_tweets())
```

## DEPLOYMENT TO GOOGLE CLOUD RUN

### Dockerfile
```dockerfile
# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Expose port (Cloud Run uses $PORT environment variable)
EXPOSE 8080

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

### .dockerignore
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.git
.gitignore
README.md
tests/
*.md
.DS_Store
```

### Deployment Commands

**Prerequisites:**
```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable pubsub.googleapis.com
```

**Deploy to Cloud Run:**
```bash
# Deploy from source (easiest)
gcloud run deploy tweet-capture-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID,JWT_SECRET_KEY=your-secret-key-here,PUBSUB_TOPIC=tweet-likes-raw"

# Cloud Run will:
# 1. Build your Docker container
# 2. Push to Container Registry
# 3. Deploy to Cloud Run
# 4. Return a URL like: https://tweet-capture-api-abc123-uc.a.run.app
```

**Alternative: Build and deploy manually:**
```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/tweet-capture-api

# Deploy container
gcloud run deploy tweet-capture-api \
  --image gcr.io/YOUR_PROJECT_ID/tweet-capture-api \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID,JWT_SECRET_KEY=your-secret-key-here"
```

### Environment Variables in Cloud Run

**Set via command line:**
```bash
gcloud run services update tweet-capture-api \
  --set-env-vars="GCP_PROJECT_ID=your-project-id,JWT_SECRET_KEY=your-secret-key,PUBSUB_TOPIC=tweet-likes-raw"
```

**Or via Cloud Console:**
1. Go to Cloud Run → tweet-capture-api → Edit & Deploy New Revision
2. Add environment variables:
   - `GCP_PROJECT_ID`: your-project-id
   - `JWT_SECRET_KEY`: generate-strong-random-key
   - `PUBSUB_TOPIC`: tweet-likes-raw

### Create Pub/Sub Topic
```bash
# Create topic
gcloud pubsub topics create tweet-likes-raw

# Set message retention
gcloud pubsub topics update tweet-likes-raw \
  --message-retention-duration=31d
```

### Initialize Firestore
```bash
# Enable Firestore in Datastore mode
gcloud firestore databases create \
  --location=us-central1 \
  --type=datastore-mode

# Or use Cloud Console:
# 1. Go to Firestore
# 2. Select "Datastore mode"
# 3. Choose location: us-central1
```

### Deploy Background Worker (Optional)

**Option 1: Cloud Run Job**
```bash
# Deploy as job
gcloud run jobs create retry-publisher \
  --source ./workers \
  --region us-central1 \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT_ID"

# Schedule with Cloud Scheduler
gcloud scheduler jobs create http retry-publisher-schedule \
  --location us-central1 \
  --schedule="*/10 * * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/retry-publisher:run" \
  --http-method POST
```

**Option 2: Cloud Scheduler calling endpoint**
```bash
# Add retry endpoint to your API
# Then schedule it:
gcloud scheduler jobs create http retry-publisher \
  --location us-central1 \
  --schedule="*/10 * * * *" \
  --uri="https://your-cloud-run-url.run.app/api/admin/retry-queue" \
  --http-method POST \
  --oidc-service-account-email="YOUR_PROJECT_ID@appspot.gserviceaccount.com"
```

## COST ANALYSIS

### Free Tier Limits (Per Month)
```
Cloud Run:
  - 2 million requests
  - 360,000 GB-seconds memory
  - 180,000 vCPU-seconds
  - Free egress: 1 GB to North America

Firestore (Datastore mode):
  - 1 GB storage
  - 50,000 reads/day
  - 20,000 writes/day
  - 20,000 deletes/day

Pub/Sub:
  - 10 GB data
  - Unlimited messages (within data limit)

Cloud Logging:
  - 50 GB logs/month
```

### Your Expected Usage (900 tweets/month)
```
Cloud Run:
  - Requests: ~2,000/month (auth + captures)
  - Memory: ~1 GB-second total
  - CPU: ~5 vCPU-seconds total
  - Cost: $0 ✅

Firestore:
  - Storage: ~3 MB
  - Writes: ~30/day (well under limit)
  - Reads: ~100/day (well under limit)
  - Cost: $0 ✅

Pub/Sub:
  - Data: ~2.7 MB/month
  - Cost: $0 ✅

Total: $0/month ✅
```

### At 10x Usage (9,000 tweets/month)
```
Still: $0/month ✅
(All within free tiers)
```

### When You'd Start Paying
```
Would need 100+ users or 100,000+ tweets/month to exceed free tiers
Even then: ~$5-10/month
```

## SECURITY BEST PRACTICES

### Authentication
- JWT tokens with short expiry (1 hour access, 30 day refresh)
- Passwords hashed with bcrypt (cost factor 12)
- Refresh tokens stored in Firestore for revocation
- HTTPS only (enforced by Cloud Run)

### API Security
- CORS restricted to Chrome extensions
- Rate limiting per user (100 requests/minute)
- Input validation with Pydantic models
- Authentication required for sensitive endpoints

### GCP Security
- IAM: Service account with minimal permissions
- Firestore: Security rules (if using Native mode)
- Pub/Sub: Topic access controlled via IAM
- Cloud Run: Private services option available

### Secrets Management
- JWT secret via environment variable (not hardcoded)
- No secrets in code or Docker image
- Use Secret Manager for sensitive configs (optional upgrade)

## MONITORING & LOGGING

### Cloud Run Metrics
- Request count and latency
- Error rates
- Container instances
- CPU and memory usage

### Custom Logging
```python
import logging
from google.cloud import logging as cloud_logging

# Initialize Cloud Logging client
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger(__name__)

# Logs automatically sent to Cloud Logging
logger.info(f"Tweet captured: {tweet_id}")
logger.error(f"Pub/Sub publish failed: {error}")
```

### Alerts (via Cloud Monitoring)
- Error rate > 5%
- Response latency p95 > 1000ms
- Pub/Sub publish failures
- Firestore errors

## TESTING

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID=your-project-id
export JWT_SECRET_KEY=test-secret-key
export PUBSUB_TOPIC=tweet-likes-raw

# Run locally
uvicorn app.main:app --reload --port 8080

# API available at: http://localhost:8080
# Docs at: http://localhost:8080/docs
```

### Testing with Firestore Emulator
```bash
# Install emulator
gcloud components install cloud-firestore-emulator

# Start emulator
gcloud emulators firestore start --host-port=localhost:8080

# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080

# Run tests
pytest tests/
```

### Manual API Testing
```bash
# Register user
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Login
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# Capture tweet (use token from login)
curl -X POST http://localhost:8080/api/tweets/capture \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tweetId":"123","tweetText":"Test","authorUsername":"test",...}'
```

## DELIVERABLES

Generate complete, production-ready code for:

1. **app/main.py** - FastAPI application setup
2. **app/config.py** - Configuration management
3. **app/models/** - Pydantic models for request/response validation
4. **app/routers/auth.py** - Authentication endpoints (register, login, refresh)
5. **app/routers/tweets.py** - Tweet capture endpoint
6. **app/routers/health.py** - Health check endpoint
7. **app/services/auth_service.py** - Authentication business logic
8. **app/services/tweet_service.py** - Tweet capture business logic
9. **app/services/firestore_service.py** - Firestore database operations
10. **app/services/pubsub_service.py** - Pub/Sub client wrapper
11. **app/dependencies.py** - FastAPI dependencies (JWT validation)
12. **app/utils/jwt.py** - JWT token utilities
13. **app/utils/password.py** - Password hashing utilities
14. **workers/retry_publisher.py** - Background worker for retry logic
15. **Dockerfile** - Container definition for Cloud Run
16. **requirements.txt** - Python dependencies
17. **.env.example** - Environment variables template
18. **.dockerignore** - Docker ignore file
19. **README.md** - Complete setup and deployment guide
20. **tests/** - Basic unit and integration tests

## CODE QUALITY STANDARDS

- **Type Hints**: Use Python type hints throughout
- **Async/Await**: Use async functions for all I/O operations
- **Error Handling**: Comprehensive try-except with specific exceptions
- **Validation**: Pydantic models for all request/response schemas
- **Documentation**: Docstrings for all public functions and classes
- **Logging**: Structured logging with appropriate levels
- **Testing**: Basic test coverage for core functionality
- **Formatting**: Black code formatter, isort for imports
- **Linting**: Pylint/Flake8 compliant

## DEPLOYMENT CHECKLIST

**Local Setup:**
- [ ] Install Python 3.11+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set environment variables in `.env`
- [ ] Run locally: `uvicorn app.main:app --reload`
- [ ] Test API at http://localhost:8080/docs

**Google Cloud Setup:**
- [ ] Create GCP project
- [ ] Install gcloud CLI
- [ ] Authenticate: `gcloud auth login`
- [ ] Enable APIs: Cloud Run, Firestore, Pub/Sub
- [ ] Create Firestore database (Datastore mode)
- [ ] Create Pub/Sub topic: `tweet-likes-raw`
- [ ] Generate JWT secret key

**Deploy to Cloud Run:**
- [ ] Deploy: `gcloud run deploy tweet-capture-api --source .`
- [ ] Set environment variables (GCP_PROJECT_ID, JWT_SECRET_KEY)
- [ ] Test health endpoint: `curl https://your-url.run.app/api/health`
- [ ] Test API docs: `https://your-url.run.app/docs`

**Chrome Extension Integration:**
- [ ] Copy Cloud Run URL
- [ ] Update Chrome extension backend URL
- [ ] Test registration and login
- [ ] Test tweet capture flow

**Optional: Background Worker:**
- [ ] Deploy retry_publisher as Cloud Run Job
- [ ] Schedule with Cloud Scheduler (every 10 minutes)
- [ ] Monitor queue size in Firestore

---

**OUTPUT REQUIREMENT**: Generate complete, production-ready FastAPI backend service that:
1. Runs serverless on Google Cloud Run ($0/month for personal use)
2. Uses Firestore for NoSQL storage (serverless, free tier)
3. Publishes to Google Cloud Pub/Sub (free tier)
4. Authenticates users with JWT tokens
5. Handles Pub/Sub failures with retry queue
6. Includes background worker for retries
7. Deploys with single `gcloud` command
8. Provides comprehensive API documentation
9. Follows security best practices
10. Is simple, maintainable, and cost-effective

**Service Name**: Tweet Capture API  
**Expected Backend URL**: Cloud Run URL (e.g., `https://tweet-capture-api-xyz.run.app`)  
**Cost**: $0/month for single-user personal use  
**Deployment Time**: ~5 minutes from code to production