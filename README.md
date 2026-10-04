# ActivationLab â€” Cloud-Native Distributed Platform

ActivationLab is a distributed backend platform for reliable asynchronous job execution using **Python, Django REST Framework, PostgreSQL, Celery, RabbitMQ, Redis, Docker, Terraform, and GitHub Actions**.

Clients submit idempotent jobs through a REST API. Jobs are persisted in PostgreSQL, dispatched through RabbitMQ, executed asynchronously by Celery workers, and exposed through a polling API with explicit execution states, results, attempt counts, and failure details.

## Architecture

```text
                         +------------------+
                         |      Client      |
                         +--------+---------+
                                  |
                    POST /api/jobs/
                    Idempotency-Key
                                  |
                                  v
                    +-------------+-------------+
                    |       Django REST API     |
                    +-------------+-------------+
                                  |
                     persist job  |  enqueue task
                         +--------+--------+
                         |                 |
                         v                 v
                 +---------------+   +------------+
                 |  PostgreSQL   |   | RabbitMQ   |
                 | Durable State |   |   Broker   |
                 +-------+-------+   +------+-----+
                         ^                  |
                         |                  v
                         |           +------+------+
                         +-----------+   Celery    |
                         |           |   Worker    |
                         |           +------+------+
                         |                  |
                         |             execute job
                         |                  |
                         |           +------+------+
                         |           |  Service    |
                         |           |   Layer     |
                         |           +-------------+
                         |
                  status / result /
                  attempts / error

                 +---------------+
                 |     Redis     |
                 | Result Backend|
                 +---------------+
```

The API, durable state, message broker, worker execution, and result backend are separated into independent services. This makes asynchronous execution, duplicate-request protection, failure handling, retries, and operational state easier to reason about and test.

## Features

- REST API for asynchronous job submission and status retrieval
- PostgreSQL-backed durable execution state
- Idempotency keys with database-level uniqueness
- RabbitMQ-backed Celery task queue
- Redis Celery result backend
- Asynchronous background workers
- Persistent job status, results, attempt counts, and errors
- Explicit `queued`, `running`, `succeeded`, and `failed` states
- Bounded retry configuration with backoff and jitter for transient failures
- Permanent validation-failure handling
- Structured application logging
- Health endpoint for service monitoring
- Dockerized multi-service development environment
- Automated pytest coverage
- GitHub Actions CI configuration
- Terraform starter infrastructure for AWS
- Database migrations isolated to the API startup process

## Local Stack

Docker Compose runs five services:

```text
api         Django REST API
worker      Celery asynchronous worker
postgres    PostgreSQL durable database
rabbitmq    Message broker
redis       Celery result backend
```

## Quick Start

Copy the example environment configuration:

```bash
cp .env.example .env
```

Build and start the platform:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

Check the API:

```bash
curl http://localhost:8000/api/health/
```

Expected response:

```json
{
  "status": "ok",
  "service": "activationlab-api"
}
```

RabbitMQ management UI is available at:

```text
http://localhost:15672
```

Default local development credentials:

```text
guest / guest
```

## API

### Submit a Job

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: demo-001' \
  -d '{"operation":"sum","payload":{"values":[10,20,30]}}'
```

A newly accepted job initially returns an execution state such as:

```json
{
  "operation": "sum",
  "status": "queued",
  "attempts": 0
}
```

### Retrieve Job State

Use the returned job ID:

```bash
curl http://localhost:8000/api/jobs/<JOB_ID>/
```

After successful worker execution, the persisted job contains its result and execution metadata.

### Idempotency

Every submission requires an `Idempotency-Key`.

Submitting another request with an existing key returns the existing job instead of creating duplicate work. The uniqueness constraint is enforced by PostgreSQL.

This protects the execution pipeline from duplicate client submissions and request retries.

## Supported Operations

ActivationLab currently provides three deterministic operations for exercising the distributed execution system.

### `sum`

```json
{
  "operation": "sum",
  "payload": {
    "values": [10, 20, 30]
  }
}
```

### `normalize`

```json
{
  "operation": "normalize",
  "payload": {
    "text": "  HELLO   ActivationLab  "
  }
}
```

### `echo`

```json
{
  "operation": "echo",
  "payload": {
    "message": "hello"
  }
}
```

These operations intentionally keep the business logic simple so the repository can focus on distributed-system behavior.

## Reliability Design

### Durable State

PostgreSQL stores job state independently from RabbitMQ and the worker process.

Each job records:

- execution status
- operation and payload
- result
- attempt count
- error details
- creation timestamp
- update timestamp

Clients can therefore distinguish between queued, running, succeeded, and failed work.

### Idempotent Submission

The database enforces uniqueness on `idempotency_key`.

Concurrent or repeated submissions using the same key resolve to the existing job instead of producing duplicate jobs.

### Failure Handling

Expected validation errors become terminal `failed` jobs with persisted error information.

Unexpected execution failures return the job to `queued` state and raise a retryable exception for Celery.

### Retry Strategy

Celery tasks are configured with:

- retryable transient exceptions
- bounded retries
- exponential backoff
- retry jitter
- maximum retry count

The automated suite verifies the retry-triggering transient-failure path.

A full broker-level multi-attempt recovery test is not currently part of the automated test suite.

### Observability

Operational signals include:

- health endpoint
- job execution states
- attempt counters
- persisted errors
- timestamps
- worker logs
- structured logging hooks

The architecture can be extended with OpenTelemetry, Prometheus, or CloudWatch for production telemetry.

## Testing

Run the test suite inside the API container:

```bash
docker compose exec api pytest -v
```

The current automated suite contains **9 passing tests** covering:

- API health
- idempotent job creation
- duplicate-request protection
- echo execution
- sum execution
- text normalization
- invalid input handling
- successful task state transitions
- permanent failure state transitions
- transient-failure retry triggering

The distributed pipeline has also been exercised end-to-end through:

```text
Django REST API
      |
      v
 PostgreSQL
      |
      v
  RabbitMQ
      |
      v
Celery Worker
      |
      v
Service Layer
      |
      v
 PostgreSQL
      |
      v
API Retrieval
```

## Repository Layout

```text
activationlab/
â”œâ”€â”€ .github/
â”‚   â””â”€â”€ workflows/       CI configuration
â”œâ”€â”€ activationlab/       Django project configuration
â”œâ”€â”€ infra/               Terraform infrastructure
â”œâ”€â”€ jobs/                API, models, tasks, services, and tests
â”œâ”€â”€ scripts/             Container entrypoint
â”œâ”€â”€ Dockerfile
â”œâ”€â”€ docker-compose.yml
â”œâ”€â”€ manage.py
â”œâ”€â”€ pytest.ini
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env.example
â””â”€â”€ README.md
```

## Infrastructure

Terraform configuration under `infra/` provides starter AWS infrastructure resources.

The repository intentionally does not claim to provide a complete production AWS deployment.

A production environment could extend the infrastructure with:

- managed PostgreSQL / Amazon RDS
- managed Redis
- Amazon MQ or another managed broker
- ECS or EKS
- load balancing
- autoscaling
- centralized secrets management
- distributed tracing and metrics
- least-privilege IAM

## CI/CD

The repository includes GitHub Actions configuration for automated validation.

Before pushing changes, the local test suite can be run with:

```bash
docker compose exec api pytest -v
```

## Security

Runtime secrets belong in `.env`, which is excluded from version control.

`.env.example` contains development-only configuration and can safely be committed as a configuration template.

Production deployments should use dedicated secret management, non-default credentials, restricted network access, TLS, and least-privilege service identities.

## Technology Stack

**Backend:** Python, Django, Django REST Framework
**Database:** PostgreSQL
**Async Processing:** Celery
**Messaging:** RabbitMQ
**Result Backend:** Redis
**Containers:** Docker, Docker Compose
**Infrastructure as Code:** Terraform
**Testing:** pytest, pytest-django
**CI:** GitHub Actions
**Cloud Infrastructure:** AWS-oriented Terraform starter configuration

## License

MIT
