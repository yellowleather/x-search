# Next Steps for Tweet Capture Backend

This document tracks the most impactful follow-ups now that the FastAPI service skeleton is in place.

## 1. Cloud Infrastructure & Deployment
- [ ] Provision GCP project resources (Firestore, Pub/Sub topic, IAM service account)
- [ ] Configure CI/CD (e.g., Cloud Build or GitHub Actions) to build and deploy to Cloud Run automatically
- [ ] Set up infrastructure-as-code (Terraform or gcloud scripts) for reproducible setup
- [ ] Harden IAM policies: restrict Cloud Run service account to minimum necessary roles

## 2. Observability & Operations
- [ ] Add structured logging with request IDs throughout services
- [ ] Export metrics (queue depth, publish success rate) to Cloud Monitoring
- [ ] Configure alerting on /api/health failures, Pub/Sub publish errors, and queue backlog size
- [ ] Add tracing (OpenTelemetry) if deeper observability is required

## 3. Background Processing
- [ ] Deploy `workers/retry_publisher.py` as a Cloud Run Job
- [ ] Schedule via Cloud Scheduler (e.g., every 5 minutes) and monitor execution results
- [ ] Add dead-letter handling for queue items exceeding retry limits (notify via email/Slack)

## 4. Security Enhancements
- [ ] Rotate JWT secret using Secret Manager; update FastAPI service to load secret at runtime
- [ ] Implement rate limiting per user/IP at the API layer (FastAPI middleware or Cloud Armor)
- [ ] Enforce HTTPS-only requests and stricter CORS (whitelist extension origin)
- [ ] Add audit logging for auth events and tweet captures

## 5. API & UX Improvements
- [ ] Implement logout endpoint to revoke refresh tokens
- [ ] Add endpoint for users to list captured tweets and queue status for debugging
- [ ] Provide admin endpoint to purge queue or reprocess specific tweet IDs
- [ ] Flesh out error responses with codes so the extension can handle them more gracefully

## 6. Testing & Tooling
- [ ] Expand test suite with Firestore emulator integration tests
- [ ] Add contract tests for Pub/Sub publisher logic
- [ ] Configure linting/formatting (Black, isort, Ruff) in CI
- [ ] Load-test the Cloud Run service to validate scaling behavior

## 7. Extension Integration
- [ ] Wire the Chrome extension’s backend URL to the deployed Cloud Run endpoint
- [ ] Validate end-to-end flow (register → login → capture → Pub/Sub message)
- [ ] Document extension configuration (backend URL, expected responses)
- [ ] Gather feedback from initial usage and iterate on UX/perf

Tracking progress against this checklist will ensure the service evolves from MVP to production-ready, observable, and secure infrastructure.
