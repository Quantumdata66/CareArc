# CareArc Backend Architecture Decision Document (ADD)

**Document Version:** 1.0.0  
**Status:** Approved for Implementation Planning  
**Target System:** CareArc Clinical Intelligence & Longitudinal Patient Trajectory Backend  
**Source of Truth:** Frontend Architecture & Backend Contract Audit  

---

## 1. Executive Summary

CareArc is a clinical intelligence platform designed to track longitudinal patient trajectories, detect physiological trends across time-series vitals, maintain clinical notes, and manage clinic appointments. 

This document defines the architectural blueprints, design standards, database schemas, and API contracts for the CareArc backend. The primary objective is to deliver a robust, type-safe, maintainable Python/FastAPI backend that is **100% drop-in compatible** with the existing React frontend, resolving client-side data anomalies while establishing clean architectural boundaries.

---

## 2. Backend Technology Stack

The CareArc backend is built on a modern, high-performance, asynchronous Python ecosystem:

| Layer / Component | Technology | Rationale & Selection Criteria |
| :--- | :--- | :--- |
| **Runtime Language** | **Python 3.11+** | Native typing support, high performance, robust mathematical/statistical ecosystem for future clinical calculations and AI integration. |
| **Web Framework** | **FastAPI** | High-throughput asynchronous REST framework with native OpenAPI/Swagger generation, automatic request validation via Pydantic, and dependency injection. |
| **Relational Database** | **PostgreSQL 16+** | ACID-compliant relational storage, native JSONB support, robust time-series indexing (`btree` on `(patient_id, timestamp DESC)`), and rock-solid relational integrity. |
| **Object-Relational Mapper (ORM)** | **SQLAlchemy 2.0 (Async)** | Industry-standard ORM with full async support (`asyncpg` driver), explicit query semantics, unit-of-work patterns, and type annotations. |
| **Database Migrations** | **Alembic** | Version-controlled, reproducible schema migrations integrated with SQLAlchemy model definitions. |
| **Validation & Serialization** | **Pydantic v2** | High-speed Rust-core validation, automated bidirectional case translation (`snake_case` DB $\leftrightarrow$ `camelCase` API), and strict schema enforcement. |

---

## 3. System Architecture & Data Flow

The CareArc backend adopts a strict **Layered Architecture (Separation of Concerns)** to isolate HTTP transport, business logic, data persistence, and external services.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 19 Frontend SPA                           │
│     (Vite + React Router v7 + Recharts + Tailored Clinical UI)         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / HTTPS (JSON, camelCase)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API Layer                          │
│               - Routing (`/api/v1/...`)                                │
│               - CORS & Request Middleware                              │
│               - Request Parsing & Pydantic Validation                  │
│               - Response Serialization (camelCase)                     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Validated DTOs / Domain Objects
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             Service Layer                              │
│               - Patient Management & Admission Logic                   │
│               - Vitals Recording & Chronological Ingestion             │
│               - Clinical Delta Engine & Acuity Derivation              │
│               - Appointment Scheduling & Status Evaluation             │
│               - Clinical Notes Orchestration                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Domain Entities / Transactions
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Data Access Layer (SQLAlchemy 2.0)                 │
│               - Async Sessions & Unit of Work                          │
│               - Relational Repositories & Query Construction           │
│               - Identity Generation & Mapping                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Async SQL (`asyncpg`)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Database                             │
│     - `patients`          - `vitals`            - `clinical_notes`     │
│     - `appointments`      - `clinical_thresholds`                     │
│     - `facility_profiles`                                              │
└────────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities:
1. **API Layer (`app/api/`):** Handles HTTP route definitions, dependency injection (database sessions), query/path parameters, and status codes. Contains zero business logic.
2. **Schema Layer (`app/schemas/`):** Defines request validation models and response serializers with automated `camelCase` aliases for frontend compatibility.
3. **Service Layer (`app/services/`):** Houses pure business logic, clinical calculations (Delta Engine), composite transactions, and cross-entity joins.
4. **Model / Data Access Layer (`app/models/`):** Defines SQLAlchemy ORM mapped entities with relational constraints, table indexes, and foreign key cascades.

---

## 4. Core MVP Entities & Database Schema

The MVP focuses on four core clinical resources plus supporting configuration tables.

```
┌───────────────────────────┐                ┌───────────────────────────┐
│         Patient           │ 1            * │           Vital           │
├───────────────────────────┤────────────────┤───────────────────────────┤
│ id: VARCHAR(32) [PK]      │                │ id: VARCHAR(32) [PK]      │
│ name: VARCHAR(255)        │                │ patient_id: VARCHAR(32)FK │
│ age: INTEGER              │                │ timestamp: TIMESTAMPTZ    │
│ gender: VARCHAR(32)       │                │ heart_rate: INTEGER       │
│ room: VARCHAR(64)         │                │ systolic_bp: INTEGER      │
│ condition: VARCHAR(255)   │                │ diastolic_bp: INTEGER     │
│ admitted: DATE            │                │ oxygen: NUMERIC(5,2)      │
│ weight: VARCHAR(64)       │                │ temperature: NUMERIC(4,2) │
│ phone: VARCHAR(64)        │                │ respiratory_rate: INTEGER │
│ email: VARCHAR(255)       │                │ recorded_by: VARCHAR(128) │
│ emergency_contact: TEXT   │                │ created_at: TIMESTAMPTZ   │
│ created_at: TIMESTAMPTZ   │                └───────────────────────────┘
│ updated_at: TIMESTAMPTZ   │
└─────────────┬─────────────┘
              │ 1
              ├──────────────────────────────┐ 1
              │ *                            │ *
              ▼                              ▼
┌───────────────────────────┐  ┌───────────────────────────┐
│       Clinical Note       │  │        Appointment        │
├───────────────────────────┤  ├───────────────────────────┤
│ id: VARCHAR(32) [PK]      │  │ id: VARCHAR(32) [PK]      │
│ patient_id: VARCHAR(32)FK │  │ patient_id: VARCHAR(32)FK │
│ timestamp: TIMESTAMPTZ    │  │ appointment_type: VARCHAR │
│ content: TEXT             │  │ appointment_date: DATE    │
│ type: VARCHAR(64)         │  │ appointment_time: VARCHAR │
│ author: VARCHAR(128)      │  │ duration_minutes: INTEGER │
│ created_at: TIMESTAMPTZ   │  │ is_completed: BOOLEAN     │
└───────────────────────────┘  │ created_at: TIMESTAMPTZ   │
                               │ updated_at: TIMESTAMPTZ   │
                               └───────────────────────────┘
```

---

## 5. Entity Relationships & Integrity Rules

1. **Patient $\rightarrow$ Vitals (1-to-Many):**
   - A Patient owns zero or more timestamped Vital records.
   - Deleting a patient triggers `ON DELETE CASCADE` to maintain referential hygiene.
   - Time-series query optimization: Composite index on `(patient_id, timestamp DESC)`.

2. **Patient $\rightarrow$ Clinical Notes (1-to-Many):**
   - A Patient owns zero or more clinical notes.
   - Deleting a patient triggers `ON DELETE CASCADE`.
   - Index on `(patient_id, timestamp DESC)` for fast timeline retrieval.

3. **Patient $\rightarrow$ Appointments (1-to-Many):**
   - A Patient can have multiple scheduled, completed, or missed appointments.
   - Deleting a patient cascades to remove associated appointments.
   - Indexes on `(appointment_date, is_completed)` and `patient_id`.

4. **Clinical Thresholds & Facility Profile (Singletons / Global Config):**
   - Clinical reference ranges and facility profile settings are stored in dedicated configuration tables.

---

## 6. API Conventions & Standards

All endpoints adhere to strict RESTful conventions:

1. **Base Path:** `/api/v1` (with `/api` rewrite / backwards-compatible routing).
2. **Media Type:** `application/json; charset=utf-8`.
3. **Casing Conventions:**
   - **Database Layer:** `snake_case` for all table names, columns, and foreign keys.
   - **API Layer (External):** `camelCase` for all JSON keys in both request payloads and response bodies.
   - **Translation Mechanism:** Automatic Pydantic `alias_generator = to_camel` with `populate_by_name = True`.
4. **Timestamp & Date Formats:**
   - **Timestamps:** ISO 8601 strings with timezone offset: `YYYY-MM-DDTHH:mm:ssZ` or `YYYY-MM-DDTHH:mm:ss+00:00`.
   - **Calendar Dates:** `YYYY-MM-DD` strings.
   - **Clock Times:** `HH:mm` (24-hour format).
5. **HTTP Status Codes:**
   - `200 OK`: Successful retrieval or update.
   - `201 Created`: Successful resource creation (returns created entity).
   - `204 No Content`: Successful deletion.
   - `400 Bad Request`: Validation failure or business rule violation.
   - `404 Not Found`: Resource does not exist.
   - `422 Unprocessable Entity`: Schema/type validation error with field-level details.
   - `500 Internal Server Error`: Unhandled server exception.

---

## 7. Frontend Compatibility Specifications

The frontend audit identified critical client-side assumptions. The backend must enforce these requirements to prevent UI runtime crashes:

### 1. Nested Blood Pressure Serialization
- **Frontend Expectation:** The UI directly accesses `vital.bloodPressure.systolic` and `vital.bloodPressure.diastolic` across charts, summary cards, and the Delta Engine.
- **Backend Requirement:** In PostgreSQL, store as separate numeric columns (`systolic_bp INTEGER`, `diastolic_bp INTEGER`). In the Pydantic response schema, serialize into a nested `bloodPressure: { systolic: int, diastolic: int }` object.

### 2. `patientId` CamelCase Property
- **Frontend Expectation:** All child objects (`vital`, `note`, `appointment`) access `item.patientId`.
- **Backend Requirement:** Database column `patient_id` must serialize to `patientId`.

### 3. Chronological Vitals Ordering
- **Frontend Expectation:** `deltaEngine.js` calculates deltas by comparing `sorted[length - 2]` (previous) with `sorted[length - 1]` (latest).
- **Backend Requirement:** `GET /api/v1/patients/{patient_id}/vitals` must always default to ascending chronological order (`ORDER BY timestamp ASC`). A dedicated endpoint `GET /api/v1/patients/{patient_id}/vitals/latest` provides O(1) access to the latest reading.

### 4. Denormalized Patient Name in Appointment Responses
- **Frontend Expectation:** `Individualappointment.jsx` and `UpcomingAppointments.jsx` render `{appointment.name}` directly.
- **Backend Requirement:** The appointment service must perform a SQL join on `patients` and populate `name: patient.name` in every appointment response object.

### 5. Strict Numeric Type Normalization
- **Frontend Bug Identified:** `AddPatientPage.jsx` currently submits string-typed vitals (`"110"`, `"90"`), causing `deltaEngine.js` range checks (`typeof value !== "number"`) to silently fail.
- **Backend Requirement:** Backend schemas strictly coerce and validate all vital sign inputs as `int` or `float`. Output is guaranteed to be numeric.

### 6. Universal Backend-Generated Identifiers
- **Frontend Bug Identified:** `AddPatientPage.jsx` omits generating an `id` for initial vitals, causing React `key` warnings and timeline rendering bugs.
- **Backend Requirement:** The backend generates unique, non-null identifiers for every persisted record upon creation.

---

## 8. Unified Resource ID Strategy

### Current Problem Analysis:
The existing frontend has four competing ID formats:
1. Patients: Seed `PT-001` vs Form `PAT-0001`
2. Vitals: Seed `VIT-001` vs Form `VIT-1741167600000` vs Form Initial `undefined`
3. Notes: Seed `NOTE-001` vs Form `NOTE-1741167600000`
4. Appointments: Seed `1` (integer) vs Form `1741167600000` (timestamp number)

### Evaluated Alternatives:

| Option | Format Example | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **Option 1: Standard UUIDv4** | `d3b07384-d113-46fb-9b24-2b50307e24c3` | Universal, collision-free, native PostgreSQL `UUID` type. | Poor clinical UX; unwieldy in bedside badges and doctor dropdowns (`ID: PT-001`). |
| **Option 2: Plain Auto-Increment Integer** | `1`, `2`, `3` | Simple, lightweight. | Vulnerable to enumeration; lacks entity context; breaks existing `PT-001` frontend routing. |
| **Option 3: Clinical Prefixed Nanoid / Short-UUID (Recommended)** | `PT-001` / `PT-K8F2M9`<br>`VIT-9X4L2A`<br>`NOTE-7M1Q8P`<br>`APT-3V8R6N` | **100% consistent across all 4 entities**; human-readable in hospital UI; collision-free; URL-safe; preserves existing UI badges. | Stored as `VARCHAR(32)` rather than native 16-byte UUID. |

### Architectural Decision:
**Adopt Option 3 (Type-Prefixed String Identifiers) across ALL resources.**
- **Patient:** `PT-<alphanumeric>` (e.g., `PT-001`, `PT-8K3F9J`)
- **Vital:** `VIT-<alphanumeric>` (e.g., `VIT-001`, `VIT-4N2L8X`)
- **Clinical Note:** `NOTE-<alphanumeric>` (e.g., `NOTE-001`, `NOTE-9M1Q4P`)
- **Appointment:** `APT-<alphanumeric>` (e.g., `APT-001`, `APT-5X7K2M`)

*Implementation:* The backend uses a dedicated ID generator utility (`app/core/ids.py`) generating cryptographically secure, URL-safe, prefixed identifiers. Existing seed IDs (`PT-001`, etc.) remain fully valid.

---

## 9. Clinical Acuity & Triage Status Strategy

### Critical Finding from Audit:
In `Patients.jsx` and `Dashboard.jsx`, patient triage status (`Review`, `Watch`, `Improving`, `Stable`) is **not a static property**—it is computed on-the-fly by `deltaEngine.derivePatientStatus()` using the rate of change between the last two vital readings and normal reference ranges.

### Architectural Decision:
1. **No Static Status Column in DB:** The `patients` table will **NOT** store a persistent `status` column as the source of truth. Persisting a static status creates immediate data staleness when vitals or threshold ranges change.
2. **Dynamic Service-Layer Derivation:**
   - The backend service layer implements a Python version of the **Delta Engine** (`app/services/delta_engine.py`).
   - When `GET /api/v1/patients` is invoked, the service layer evaluates the latest vitals against current thresholds and includes a derived `status` field in the response DTO.
3. **Frontend Runtime Compatibility:**
   - The frontend can continue using its client-side `deltaEngine.js` or consume the backend-computed `status` seamlessly, as both apply identical clinical rules.

---

## 10. MVP API Scope & Endpoints

### 1. Patients API (`/api/v1/patients`)
- `GET /api/v1/patients`: List all patients with search filter (`?search=`), pagination, and derived status summary.
- `GET /api/v1/patients/{patient_id}`: Retrieve full patient record.
- `POST /api/v1/patients`: Register patient (with optional `initialVitals` in payload for atomic onboarding).
- `PUT /api/v1/patients/{patient_id}`: Full update of patient demographics.
- `PATCH /api/v1/patients/{patient_id}`: Partial update of patient record.
- `DELETE /api/v1/patients/{patient_id}`: Delete patient and cascade associated records.

### 2. Vitals API (`/api/v1/patients/{patient_id}/vitals`)
- `GET /api/v1/patients/{patient_id}/vitals`: List all vitals for a patient in chronological order (`ASC`).
- `POST /api/v1/patients/{patient_id}/vitals`: Record a new timestamped vital entry.
- `GET /api/v1/patients/{patient_id}/vitals/latest`: Retrieve the latest vital reading.
- `GET /api/v1/patients/{patient_id}/deltas`: Retrieve computed rate-of-change deltas and trajectory classifications.

### 3. Clinical Notes API (`/api/v1/patients/{patient_id}/notes`)
- `GET /api/v1/patients/{patient_id}/notes`: List all notes for a patient in reverse-chronological order (`DESC`).
- `POST /api/v1/patients/{patient_id}/notes`: Create a clinical note (`content`, optional `type`, `author`).
- `DELETE /api/v1/notes/{note_id}`: Delete a clinical note.

### 4. Appointments API (`/api/v1/appointments`)
- `GET /api/v1/appointments`: List appointments with filters (`?date=`, `?patientId=`, `?isCompleted=`).
- `POST /api/v1/appointments`: Schedule an appointment.
- `PATCH /api/v1/appointments/{appointment_id}/complete`: Mark visit completed (`isCompleted: true`).
- `PATCH /api/v1/appointments/{appointment_id}`: Reschedule or modify appointment details.
- `DELETE /api/v1/appointments/{appointment_id}`: Cancel an appointment.

### 5. Settings & Thresholds API (`/api/v1/settings`)
- `GET /api/v1/settings/thresholds`: Get normal vital sign reference ranges.
- `PUT /api/v1/settings/thresholds`: Update clinical threshold reference ranges.
- `GET /api/v1/settings/profile`: Get clinical facility profile and monitoring protocols.
- `PUT /api/v1/settings/profile`: Update facility profile and ward settings.

### 6. Timeline API (`/api/v1/patients/{patient_id}/timeline`)
- `GET /api/v1/patients/{patient_id}/timeline`: Retrieve unified, chronologically interleaved stream of vitals and notes.

---

## 11. Deferred Features (Post-MVP Roadmap)

To maintain focus on a rock-solid, production-grade core foundation, the following capabilities are explicitly deferred from the MVP:

1. **AI Synthesis & Clinical LLM Integration:**
   - OpenAI / GPT-4o-mini / Gemini summarization pipelines for automated handover notes.
   - Handled via mock/stub endpoints or deferred to Phase 2.
2. **User Authentication & Role-Based Access Control (RBAC):**
   - JWT / OAuth2 multi-user login, staff session tokens, and role permissions.
   - Single clinical staff context is assumed for MVP.
3. **Machine Learning Trajectory Models:**
   - Predictive deterioration algorithms, sepsis scoring, or automated anomaly classification.
4. **MLOps & Pipeline Orchestration:**
   - Feature stores, model registries, automated retraining pipelines.
5. **Multi-Region Distributed Infrastructure:**
   - Complex Kubernetes clustering, Redis caching clusters, or distributed event buses.

---

## 12. Proposed Backend Directory Structure

```
backend/
├── alembic/
│   ├── versions/
│   │   └── 0001_initial_schema.py
│   ├── env.py
│   ├── script.py.mako
│   └── README
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application factory, CORS, router inclusion
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py                # Aggregated v1 APIRouter
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── patients.py          # /api/v1/patients endpoints
│   │   │       ├── vitals.py            # /api/v1/patients/{id}/vitals endpoints
│   │   │       ├── notes.py             # /api/v1/patients/{id}/notes endpoints
│   │   │       ├── appointments.py      # /api/v1/appointments endpoints
│   │   │       ├── settings.py          # /api/v1/settings endpoints
│   │   │       └── timeline.py          # /api/v1/patients/{id}/timeline endpoints
│   │   └── deps.py                      # Database session injection & common dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic Settings (ENV variables, DB URI, CORS origins)
│   │   ├── database.py                  # SQLAlchemy async engine & sessionmaker
│   │   ├── exceptions.py                # Custom domain exceptions & global exception handlers
│   │   └── ids.py                       # Unified prefixed identifier generator (PT-, VIT-, etc.)
│   ├── models/                          # SQLAlchemy ORM models (Database Tables)
│   │   ├── __init__.py
│   │   ├── base.py                      # DeclarativeBase with timestamp mixins
│   │   ├── patient.py                   # Patient SQL model
│   │   ├── vital.py                     # Vital SQL model
│   │   ├── note.py                      # ClinicalNote SQL model
│   │   ├── appointment.py               # Appointment SQL model
│   │   └── setting.py                   # Threshold & FacilityProfile SQL models
│   ├── schemas/                         # Pydantic DTOs (Request Validation & Response Serializers)
│   │   ├── __init__.py
│   │   ├── base.py                      # BaseSchema with camelCase alias configuration
│   │   ├── patient.py                   # PatientCreate, PatientUpdate, PatientResponse
│   │   ├── vital.py                     # VitalCreate, BloodPressureSchema, VitalResponse
│   │   ├── note.py                      # NoteCreate, NoteResponse
│   │   ├── appointment.py               # AppointmentCreate, AppointmentUpdate, AppointmentResponse
│   │   ├── setting.py                   # ThresholdSchema, FacilityProfileSchema
│   │   └── timeline.py                  # TimelineEventResponse
│   └── services/                        # Business Logic & Clinical Calculations
│       ├── __init__.py
│       ├── patient_service.py           # Patient CRUD & query logic
│       ├── vital_service.py             # Vitals ingestion & latest reading extraction
│       ├── note_service.py              # Clinical notes operations
│       ├── appointment_service.py       # Appointment booking, conflict checks, joins
│       ├── delta_engine_service.py      # Python port of Delta Engine & Acuity classification
│       └── setting_service.py           # Threshold & Profile management
├── docs/
│   └── ARCHITECTURE.md                  # This architecture decision document
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Pytest fixtures & async test client setup
│   ├── test_patients.py
│   ├── test_vitals.py
│   ├── test_delta_engine.py
│   └── test_appointments.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

---

## 13. Architectural Decisions & Trade-Offs (ADR Summary)

### ADR 1: Async SQLAlchemy with `asyncpg`
- **Context:** FastAPI supports asynchronous endpoint handlers. Database I/O is the primary throughput bottleneck.
- **Decision:** Use `asyncpg` with SQLAlchemy 2.0 async sessions (`AsyncSession`).
- **Trade-off:** Slightly steeper learning curve and strict async session lifecycle management vs significant throughput gains under concurrent clinical monitoring loads.

### ADR 2: Centralized CamelCase Pydantic Serialization
- **Context:** Python and PostgreSQL use `snake_case` by convention; JavaScript and React use `camelCase`.
- **Decision:** Base schema inherits Pydantic `model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)`.
- **Trade-off:** Eliminates manual dictionary transformation boilerplate and guarantees 100% frontend property compatibility.

### ADR 3: Compound Primary & Index Keys for Time-Series Vitals
- **Context:** Vitals are queried by patient in time order thousands of times per day.
- **Decision:** Add composite indexes on `(patient_id, timestamp DESC)` and `(patient_id, timestamp ASC)`.
- **Trade-off:** Negligible insert overhead for massive read acceleration in trajectory charts and delta calculations.

---

## 14. Open Architecture Decisions

The following architectural decisions require review and stakeholder approval prior to backend implementation:

| Decision ID | Area | Decision Options | Recommended Option | Trade-off / Impact |
| :--- | :--- | :--- | :--- | :--- |
| **OAD-01** | **Database Seed Strategy** | **A:** Seed PostgreSQL with existing 5 patients (`PT-001` through `PT-005`), vitals trajectories, notes, and appointments via Alembic/seed script on first boot.<br>**B:** Start with an empty database requiring manual user input. | **Option A (Seed with Audit Dataset)** | Ensures the UI immediately populates with realistic clinical trajectories (Worsening, Fluctuating, Improving, Stable) upon launching the backend. |
| **OAD-02** | **Route Parameter Harmonization** | **A:** Support both `/api/v1/patients/{patient_id}` and `/api/v1/patients/{patientsId}` via alias.<br>**B:** Enforce standard singular `/api/v1/patients/{patient_id}` on the backend, and update the frontend router/hook when introducing `api.js`. | **Option B (Singular Standard)** | Enforces clean REST conventions in the backend while updating frontend client service mapping cleanly. |
| **OAD-03** | **Appointment ID Format Transition** | **A:** Maintain numeric IDs for appointments (PostgreSQL `BIGINT` auto-increment).<br>**B:** Standardize appointments on prefixed string IDs (`APT-001`, `APT-8X2M9K`). | **Option B (Prefixed String IDs)** | Achieves 100% uniform string ID architecture across all 4 core entities; frontend seamlessly handles string appointment IDs. |
| **OAD-04** | **Default Oxygen Normal Range Alignment** | **A:** Adopt `ThresholdContext` range (`90% - 95%`).<br>**B:** Adopt `deltaEngine.js` range (`95% - 100%`). | **Option B (`95% - 100%`)** | Clinically accurate normal SpO₂ range; prevents healthy patients (96-99%) from triggering false out-of-range warnings. |
| **OAD-05** | **Atomic Patient Registration Endpoint** | **A:** Two separate API calls: `POST /api/v1/patients` followed by `POST /api/v1/patients/{id}/vitals`.<br>**B:** Single composite endpoint: `POST /api/v1/patients` accepts optional `initialVitals` and executes in a single database transaction. | **Option B (Composite Atomic Post)** | Directly matches `AddPatientPage.jsx` workflow, eliminating orphan patients without baseline vitals if a second call fails. |

---
*End of Architecture Decision Document. Awaiting approval on Open Architecture Decisions before initiating code development.*
