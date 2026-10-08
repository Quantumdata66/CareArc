# CareArc Clinical Intelligence Backend

High-performance, asynchronous REST API for the **CareArc Clinical Intelligence & Longitudinal Patient Trajectory Platform**.

---

## 🛠 Technology Stack

* **Language:** Python 3.12+
* **Framework:** FastAPI 0.115+
* **ORM:** SQLAlchemy 2.0 (Async with `asyncpg`)
* **Database:** PostgreSQL 16+ (or SQLite via `aiosqlite` for tests)
* **Migrations:** Alembic 1.13+
* **Validation & Serialization:** Pydantic v2
* **Testing:** Pytest & Pytest-Asyncio with HTTPX

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate     # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set your PostgreSQL connection string:

```bash
cp .env.example .env
```

Example `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/carearc
DEBUG=True
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Seed Clinical Audit Dataset

Populate the database with the 5 clinical audit patients (`PT-001` through `PT-005`), longitudinal time-series vitals (worsening, fluctuating, improving, stable), notes, and appointments:

```bash
python -m app.core.seed
```

### 5. Launch Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

* **API Base Path:** `http://localhost:8000/api/v1`
* **Interactive Swagger UI:** `http://localhost:8000/docs`
* **ReDoc Documentation:** `http://localhost:8000/redoc`
* **Health Probe:** `http://localhost:8000/health`

---

## 🧪 Running Automated Tests

Run the complete 32-test async suite with SQLite in-memory fixtures:

```bash
pytest -v
```

---

## 🐳 Docker Deployment

To launch both PostgreSQL and FastAPI in Docker containers:

```bash
docker-compose up --build -d
```

---

## 📂 Core API Endpoints

| Resource | Method | Path | Description |
| :--- | :--- | :--- | :--- |
| **Patients** | `GET` | `/api/v1/patients` | List patients with search, pagination, and derived acuity status |
| | `POST` | `/api/v1/patients` | Register patient (supports atomic `initialVitals`) |
| | `GET` | `/api/v1/patients/{id}` | Get patient record and latest vital |
| | `PUT` / `PATCH` | `/api/v1/patients/{id}` | Update patient demographics |
| | `DELETE` | `/api/v1/patients/{id}` | Delete patient (cascades vitals, notes, appointments) |
| **Vitals** | `GET` | `/api/v1/patients/{id}/vitals` | Chronological vitals trajectory (`ASC`) |
| | `POST` | `/api/v1/patients/{id}/vitals` | Record timestamped vital sign reading |
| | `GET` | `/api/v1/patients/{id}/vitals/latest` | Retrieve single latest vital reading |
| | `GET` | `/api/v1/patients/{id}/deltas` | Computed rate-of-change deltas & acuity status |
| **Notes** | `GET` | `/api/v1/patients/{id}/notes` | Patient clinical notes (`DESC`) |
| | `POST` | `/api/v1/patients/{id}/notes` | Create observation, treatment, or review note |
| | `DELETE` | `/api/v1/notes/{id}` | Delete clinical note |
| **Appointments** | `GET` | `/api/v1/appointments` | List appointments with `?date=`, `?patientId=`, `?isCompleted=` |
| | `POST` | `/api/v1/appointments` | Book appointment |
| | `PATCH` | `/api/v1/appointments/{id}/complete` | Flag appointment as completed |
| | `PATCH` / `DELETE`| `/api/v1/appointments/{id}` | Reschedule or cancel appointment |
| **Settings** | `GET` / `PUT` | `/api/v1/settings/thresholds` | Normal vital reference ranges |
| | `GET` / `PUT` | `/api/v1/settings/profile` | Facility profile & ward configurations |
| **Timeline** | `GET` | `/api/v1/patients/{id}/timeline` | Unified interleaved event stream (vitals + notes) |
