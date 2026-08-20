Task 5 — Scaling Plan for 5,000 Workers

1. Objective

The current ConsultBae application is a local prototype built with FastAPI, SQLite, and local audio-file storage.

The goal of this task is to describe how the system should be changed before handling approximately 5,000 workers over a single weekend.

The current implementation is intentionally simple for the take-home assignment. The recommendations below describe the production architecture I would use rather than claiming that these production components are already implemented.

2. Current Architecture

Worker
  |
  v
Browser Frontend
  |
  v
FastAPI
  |
  +------> SQLite
  |
  +------> Local audio/submissions/

The current architecture is suitable for local development and demonstration, but several components would become bottlenecks or reliability risks at higher concurrency.

3. What Would Break First?

3.1 Local Audio Storage

Audio recordings are currently stored on the application machine under audio/submissions/.

This becomes a problem when multiple API instances are deployed because local disks are not a reliable shared storage layer.

Production change: move recordings to object storage such as Amazon S3, Google Cloud Storage, or Azure Blob Storage. The database should store the object key/URL and metadata rather than depending on a local file path.

3.2 SQLite

SQLite is appropriate for the current local prototype, but it is not the database I would use for thousands of concurrent workers and production writes.

Production change: move to PostgreSQL with connection pooling, indexes, transactions, backups, and monitoring.

3.3 Synchronous Audio Processing

At 5,000 workers, making every request wait for audio processing can increase response times and API load.

Production change:

Upload
   |
   v
Object Storage
   |
   v
Message Queue
   |
   v
Audio Processing Worker
   |
   v
Metadata Database

The API can return a submission ID and status such as pending; workers can later update it to processing, completed, or failed.

4. Handling Upload Failures

With thousands of uploads, transient failures are expected.

The production system should include:

File-size limits

Request timeouts

Retry handling

Upload validation

Failed-job tracking

Appropriate HTTP error responses

Resumable/multipart uploads where useful

Retries should not accidentally create duplicate submissions.

5. Idempotency and Duplicate Submissions

A worker may submit the same recording twice or retry after a timeout.

The API should support an idempotency key for submission requests.

Worker
   |
   | submission + idempotency key
   v
API
   |
   +---- existing key? ---- yes ---> return existing submission
   |
   no
   |
   v
Create submission

A SHA-256 content hash can also be used as an additional signal for detecting duplicate audio files.

6. Horizontal API Scaling

Instead of relying on a single FastAPI process, multiple stateless API instances can run behind a load balancer.

                  Load Balancer
                       |
          +------------+------------+
          |            |            |
          v            v            v
      FastAPI #1   FastAPI #2   FastAPI #3
          |            |            |
          +------------+------------+
                       |
              Shared PostgreSQL
                       |
                Object Storage

Because audio files and persistent metadata are stored outside the API instance, API servers can be added or removed without losing application data.

7. Audio Processing Workers

Audio processing should be separated from the request-serving layer.

FastAPI
   |
   v
Queue
   |
   +----> Worker 1
   +----> Worker 2
   +----> Worker 3
   +----> Worker N

Workers can scale horizontally according to the number of pending audio-processing jobs. This prevents a slow processing job from blocking normal API traffic.

8. Submission Listing

A production system should not return thousands of records in one API response.

Instead:

GET /api/audio/submissions?page=1&limit=50

Useful features include:

Pagination

Filtering

Sorting

Database indexes

Search where required

9. Proposed Production Architecture

                         Workers
                            |
                            v
                     Load Balancer
                            |
                 +----------+----------+
                 |          |          |
                 v          v          v
              FastAPI    FastAPI    FastAPI
                 |          |          |
                 +----------+----------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
       PostgreSQL                    Object Storage
       Application data              Audio recordings
             |                             |
             +--------------+--------------+
                            |
                            v
                         Queue
                            |
                            v
                  Audio Processing Workers
                            |
                            v
                     Metadata Updates

10. Reliability Strategy

API reliability

Load balancing

Horizontal scaling

Timeouts

Rate limiting where appropriate

Health checks

Upload reliability

File validation

Size limits

Retry handling

Idempotency keys

Object-storage based uploads

Database reliability

PostgreSQL

Connection pooling

Indexes

Automated backups

Recovery testing

Processing reliability

Queue-based processing

Retry policy

Dead-letter/failed-job handling

Processing status tracking

Observability

Structured application logs

Error tracking

Request latency metrics

Queue-depth monitoring

Upload success/failure metrics

Alerts for elevated error rates

11. Cost Considerations

The main production cost drivers would be:

Audio storage

Audio download/bandwidth

API compute

Audio-processing compute

Managed PostgreSQL

Queue operations

Logging and monitoring

Because the workload is concentrated over a weekend, autoscaling is preferable to permanently running a large amount of compute.

Object storage is also preferable to keeping large audio collections on application-server disks.

12. Launch Checklist

Before accepting approximately 5,000 workers, I would verify:

PostgreSQL is configured

Object storage is configured

Queue-based audio processing is deployed

API instances can scale horizontally

Upload size limits are configured

Retry and idempotency behavior is tested

Database indexes are in place

Submission pagination is implemented

Monitoring and alerts are configured

Load testing has been performed

Database backups are configured

Recovery procedures have been tested

13. What I Would Keep Simple

Not every part needs to become complex immediately.

For a first production launch, I would prioritize:

Reliable object storage

PostgreSQL

Queue-based audio processing

Horizontal API scaling

Upload retry/idempotency

Monitoring and backups

I would avoid introducing unnecessary microservices until actual traffic patterns justify them.

The goal is to remove the obvious single points of failure while keeping the architecture operationally manageable.

14. Summary

The current FastAPI + SQLite + local-file architecture is appropriate for the take-home prototype.

For approximately 5,000 workers over a weekend, the main changes would be:

SQLite
   -> PostgreSQL

Local audio files
   -> Object storage

Synchronous processing
   -> Queue + worker processing

Single API instance
   -> Load-balanced FastAPI instances

Unbounded submission listing
   -> Paginated API

Simple requests
   -> Retries + idempotency

Basic local debugging
   -> Logging + monitoring + alerts

These changes would make the system more resilient to burst traffic, upload failures, concurrent database operations, and increased audio-processing workload.