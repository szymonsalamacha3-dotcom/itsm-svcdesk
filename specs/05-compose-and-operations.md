<!-- ai-generated: 40% - compiled from R-22, R-23, R-24, API.md section 9 and the compose requirements -->
# Compose, runtime environment, and operational characteristics

## 1. Service shape

The service must be built as a Docker Compose project with a service named svcdesk. The compose file is expected to be located at the repository root and discovered using the supported order:

- compose.yaml
- compose.yml
- docker-compose.yml
- docker-compose.yaml

The service must satisfy these properties:

- build from the repository (`build:` key required), not only `image:`
- listen inside the container on port 8080
- set SVCDESK_TEST_CLOCK="1"
- use no host-path bind mounts
- allow service startup and health endpoint checks within 120 seconds
- keep no network access after image build

## 2. Container requirements

The service must:

- run on port 8080,
- answer GET /health within 120 seconds after compose up --wait svcdesk,
- not require runtime network access to install dependencies,
- run with all dependencies installed at build time,
- persist ticket data across restarts, using a named volume or equivalent durable storage.

This is required by R-22, R-23, and R-24.

## 3. Persistence

A SQLite database file or equivalent persistent storage in a named volume is sufficient. The service must maintain ticket state across a restart of the svcdesk container.

The implementation is expected to keep ticket records durable across service restarts without relying on ephemeral in-memory data.

## 4. Test-clock environment

The service must read the environment variable SVCDESK_TEST_CLOCK.

When this variable is set to 1 or true, requests may include X-Test-Clock as a request-only override. The service must ignore that header when the variable is unset or 0.

## 5. Error and status semantics

The service must respond with JSON to any endpoint it knows, and with JSON error bodies for 404 and validation failures. For all valid operations, return application/json payloads only.

## 6. Operational boundary for later implementation

This specification defines the runtime contract and operational assumptions. Any implementation later added under src/ must satisfy these contract obligations without changing the repository Docker wiring or the validation semantics already declared in the earlier specification files.

The goal of this specification is not to implement the service yet, but to capture all behavioral and operational constraints needed for a correct later implementation.
