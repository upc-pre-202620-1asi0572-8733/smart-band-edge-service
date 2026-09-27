# Smart Band Edge Service

`smart_band_edge_service` is a lightweight IoT edge API for ingesting heart-rate
data emitted by smart band devices. The service follows a Domain-Driven Design
(DDD) approach and separates the device-authentication concerns from the health
data ingestion concerns.

At its current stage, the service provides:

- device authentication using `device_id` + `X-API-Key`
- ingestion of heart-rate (`bpm`) measurements
- SQLite persistence through Peewee ORM
- a layered architecture aligned with DDD bounded contexts

## Current Scope

This repository currently implements a focused subset of an IoT-edge solution:

- **Implemented**
  - registration/lookup of a development test device
  - authentication of device-originated requests
  - creation and persistence of health records
  - timestamp normalization to UTC
- **Not implemented yet**
  - activity tracking
  - sleep tracking
  - analytics pipelines
  - cloud synchronization
  - a dedicated health check endpoint such as `GET /status`

Keeping the README aligned with the implemented scope is especially important
in IoT projects, where device contracts and API behavior must remain explicit
and dependable.

## Why DDD for an IoT Edge Service?

In IoT systems, devices, telemetry, authentication, and persistence often grow
quickly and evolve independently. DDD helps keep that complexity manageable by
organizing the code around business capabilities instead of technical concerns.

This service is split into two bounded contexts:

### 1. IAM (Identity and Access Management)

Responsible for identifying devices and validating their credentials.

- **Core concept**: `Device`
- **Primary responsibility**: authenticate incoming requests from smart bands

### 2. Health

Responsible for validating and storing health telemetry.

- **Core concept**: `HealthRecord`
- **Primary responsibility**: accept heart-rate readings and persist them

The Health context delegates device validation through a DDD
anti-corruption layer. It translates IAM's authentication result into Health's
`SubmittingDevice` concept, keeping the telemetry model decoupled from IAM's
repository and credential model.

## Layered Architecture

Each bounded context follows the same DDD-inspired structure:

- **Domain**
  - entities and domain services
  - business rules and invariants
  - no framework or ORM concerns
- **Application**
  - orchestration of use cases
  - coordinates repositories and domain services
- **Infrastructure**
  - Peewee models
  - repository implementations
  - persistence details
- **Interfaces**
  - Flask HTTP endpoints and request handling

### Project Structure

```text
smart_band_edge_service/
├── app.py
├── health/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── integration/
│   └── interfaces/
├── iam/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
├── shared/
│   └── infrastructure/
└── docs/
```

## Technical Stories

Technical stories are part of the official project documentation and describe
the integration contract from the smart-band device maker perspective for
unattended device-to-edge interactions.

- Source of truth: [`docs/user-stories.md`](docs/user-stories.md)
- Story style: `As a ... I want to ... so that ...` with Gherkin acceptance
  criteria (`Given/When/Then`)
- Focus: observable edge-service behavior (authentication, validation,
  persistence, bootstrap), not UI behavior

### Story-to-Context Mapping

- **Health bounded context**: `TS-SBE-001`, `TS-SBE-003`, `TS-SBE-004`,
  `TS-SBE-005`
- **IAM bounded context**: `TS-SBE-002`
- **Application bootstrap / shared infrastructure**: `TS-SBE-006`

Use these stories to drive API evolution, regression validation, and backlog
prioritization as the IoT edge capabilities grow.

## Technology Stack

- Python 3.13+
- Flask
- Peewee
- SQLite

Exact Python dependencies are declared in [`requirements.txt`](requirements.txt).

## Getting Started

### 1. Create a virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Run the service

```sh
APP_ENV=development python app.py
```

The checked-in `.env.development` provides non-secret local defaults.
`APP_ENV=development` selects it, and process environment variables override
values in the file. To seed a test device, enable `SEED_TEST_DEVICE` and set
`TEST_DEVICE_API_KEY` in the process environment; use a unique, local-only key.

For production, set `APP_ENV=production` in the process environment to select
the checked-in `.env.production` defaults. Supply secrets through your
deployment's secret/configuration mechanism, not a committed file. Production
disables debug mode and test-device seeding, and should run behind a
production WSGI server rather than Flask's built-in server.

## Runtime Behavior

The application performs bootstrap work before serving the first request:

- initializes the SQLite database
- creates the `devices` and `health_records` tables if they do not exist
- migrates stored device credentials to salted PBKDF2 verifiers and adds
  revocation state to existing device tables
- migrates existing telemetry tables to support device-scoped idempotency keys
- seeds a development test device only when explicitly enabled in development

Database initialization and migrations run during application creation, before
the service accepts requests. `DATABASE_PATH`, `DEBUG`, `HOST`, `PORT`,
`SEED_TEST_DEVICE`, `TEST_DEVICE_ID`, and `TEST_DEVICE_API_KEY` are loaded from
the selected environment file or process environment.

## Development Test Device

To enable development test-device seeding, set `SEED_TEST_DEVICE=true` and
`TEST_DEVICE_API_KEY` to a unique local-only value in the process environment:

- `device_id`: `smart-band-001`
- `api_key`: value supplied by `TEST_DEVICE_API_KEY`

> [!WARNING]
> This device is intended for local development only. Do not enable test-device
> seeding or reuse development credentials in production or on real IoT
> deployments.

## API Contract

### Create a health record

`POST /api/v1/health-monitoring/data-records`

Creates a new heart-rate record for an authenticated device.

#### Required headers

- `Content-Type: application/json`
- `X-API-Key: <device api key>`

#### Request body

```json
{
  "device_id": "smart-band-001",
  "event_id": "band-001-000042",
  "bpm": 72.5,
  "created_at": "2025-06-04T18:23:00-05:00"
}
```

#### Request fields

- `device_id` (`string`, required): unique device identifier
- `event_id` (`string`, required): stable device-generated event identity,
  reused unchanged when retrying the same reading; unique per device
- `bpm` (`number`, required): heart rate in beats per minute
- `created_at` (`string`, optional): ISO 8601 timestamp; when omitted, the
  service uses the current UTC time

#### Example request

```sh
curl -X POST http://127.0.0.1:5000/api/v1/health-monitoring/data-records \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: test-api-key-123' \
  -d '{
	"device_id": "smart-band-001",
	"event_id": "band-001-000042",
	"bpm": 72.5,
	"created_at": "2025-06-04T18:23:00-05:00"
  }'
```

#### Success response

`201 Created`

The first accepted submission returns `201 Created`. An identical retry
returns `200 OK` with the original record and ID. Reusing the same event ID
with different telemetry returns `409 Conflict`.

```json
{
  "id": 1,
  "device_id": "smart-band-001",
  "event_id": "band-001-000042",
  "bpm": 72.5,
  "created_at": "2025-06-04T23:23:00+00:00Z"
}
```

#### Error responses

- `400 Bad Request`
  - missing required fields
  - invalid BPM value
  - malformed timestamp
- `401 Unauthorized`
  - missing `device_id`
  - missing `X-API-Key`
  - invalid device/API key pair
- `409 Conflict`
  - event ID already used for different telemetry

## Operational Notes for IoT Projects

When adapting this service for a real IoT solution, consider the following:

- **Credential management**: replace hard-coded development credentials with a
  secure enrollment or provisioning flow. IAM stores a salted verifier rather
  than the API key, and its device aggregate supports credential rotation and
  revocation through application services.
- **Persistence**: SQLite is suitable for local development and lightweight
  edge deployments, but not ideal for high-write concurrency.
- **Observability**: add structured logging, trace correlation, and a proper
  health check endpoint before production use.
- **Device contracts**: version telemetry payloads carefully so device firmware
  and server-side ingestion remain compatible. Each device must persist a
  stable event ID and reuse it on retries.
- **Delivery reliability**: persist a stable event ID on the device before
  transmission and reuse it for every retry until the edge service confirms
  acceptance.
- **Startup lifecycle**: move bootstrap logic out of `before_request` if you
  need deterministic initialization during container startup.

## Documentation

Additional documentation is available in [`docs/`](docs):

- [`docs/user-stories.md`](docs/user-stories.md): technical stories and
  acceptance criteria for unattended smart-band to edge-service interactions.
- [`docs/class-diagram.puml`](docs/class-diagram.puml): PlantUML diagram of
  the bounded contexts, layers, and relationships.
- [`docs/adrs.md`](docs/adrs.md): architecture decisions and their
  consequences.

Project history is tracked in [`CHANGELOG.md`](CHANGELOG.md) using the Keep a
Changelog format.

Environment configuration defaults:

- [`.env.development`](.env.development): local development defaults without
  credentials.
- [`.env.production`](.env.production): production defaults without secrets;
  provide real secrets externally.

## License

This project is licensed under the MIT License. See [`LICENSE.md`](LICENSE.md)
for details.

## Improvements Made

The codebase has been modernized with the following improvements:

1.  **Modern Python Features**:
    *   **Immutability**: Domain entities (`Device`, `HealthRecord`) now use `@dataclass(frozen=True)` to ensure state consistency and prevent accidental modification outside domain services.
    *   **Type Hinting**: Consistent use of modern type hints (e.g., `str | None` instead of `Optional[str]`) and `datetime.UTC`.
2.  **Clean Architecture & DDD**:
    *   **Repository Protocols**: Introduced `Protocol` based interfaces for repositories in the domain layer. This decouples the domain from infrastructure (Peewee) and enables easier testing via dependency injection.
    *   **Dependency Injection**: Application services now accept repository interfaces in their constructors, allowing for easier mocking and better testability.
3.  **Robust Data Validation**:
    *   **Pydantic Integration**: Introduced Pydantic for request validation in the interface layer. This provides automatic type checking, range validation (e.g., BPM between 0 and 200), and clearer error messages.
4.  **Dependencies**: Updated `requirements.txt` to include `pydantic` and ensure latest compatible versions of other libraries.
5.  **Refactoring**: Converted repository methods from `@staticmethod` to instance methods to align with modern OOP practices and DI patterns.
