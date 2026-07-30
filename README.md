# Task Manager Backend API

A production-style **Task Manager REST API** built with FastAPI, SQLAlchemy, and SQLite.

This project is also a hands-on DevOps learning lab covering:
**Git · GitHub · Feature Branches · Pull Requests · pytest · Docker · GitHub Actions CI/CD · Secret Scanning · Dependency Auditing · Trivy Image Scanning**

---

## Architecture

```
HTTP Request
    │
    ▼
API Layer        (app/api/)          — Route handlers, HTTP methods
    │
    ▼
Schema Layer     (app/schemas/)      — Pydantic validation, request/response shapes
    │
    ▼
Service Layer    (app/services/)     — Business logic, rules
    │
    ▼
Repository Layer (app/repositories/) — All database access (SQL lives here only)
    │
    ▼
Database         (SQLite / PostgreSQL via SQLAlchemy async)
```

---

## Folder Structure

```
task-manager-backend/
├── app/
│   ├── main.py                     # FastAPI app factory + health endpoint
│   ├── api/
│   │   ├── deps.py                 # Shared FastAPI dependencies
│   │   └── v1/
│   │       ├── router.py           # Aggregates all v1 routes
│   │       └── tasks.py            # Task route handlers
│   ├── core/
│   │   └── config.py               # Pydantic Settings — reads .env
│   ├── db/
│   │   └── session.py              # Async SQLAlchemy engine + session
│   ├── models/
│   │   └── task.py                 # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── task.py                 # Pydantic schemas (API contract)
│   ├── services/
│   │   └── task_service.py         # Business logic layer
│   └── repositories/
│       └── task_repository.py      # Database queries
├── tests/
│   ├── conftest.py                 # Pytest fixtures (in-memory test DB)
│   ├── test_health.py
│   └── test_tasks.py
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI pipeline
├── .env.example                    # Environment variable template
├── .gitignore
├── .dockerignore
├── Dockerfile                      # Multi-stage, non-root user
├── pyproject.toml                  # pytest + ruff configuration
└── requirements.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| POST | `/api/v1/tasks` | Create a new task |
| GET | `/api/v1/tasks` | List all tasks (filter by status/priority) |
| GET | `/api/v1/tasks/{id}` | Get a specific task |
| PATCH | `/api/v1/tasks/{id}` | Partially update a task |
| DELETE | `/api/v1/tasks/{id}` | Delete a task |

### Task Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Auto-generated unique identifier |
| `title` | string | Required, 1–200 characters |
| `description` | string | Optional detail |
| `status` | enum | `todo` \| `in_progress` \| `done` |
| `priority` | enum | `low` \| `medium` \| `high` |
| `created_at` | datetime | Auto-set on creation |
| `updated_at` | datetime | Auto-updated on every change |

---

## Local Setup

### Prerequisites

- Python 3.12+
- pip
- Docker Desktop (for container steps)

### 1. Clone the repository

```bash
git clone https://github.com/sunkusaiabhinav/task-manager-backend.git
cd task-manager-backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values (defaults work for local dev)
```

### 5. Run the development server

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Task Manager API` | Application name |
| `APP_ENV` | `development` | Environment (`development` \| `staging` \| `production`) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `API_V1_PREFIX` | `/api/v1` | API route prefix |
| `DATABASE_URL` | `sqlite+aiosqlite:///./taskmanager.db` | Database connection string |

> ⚠️ **Never commit your `.env` file.** It is excluded by `.gitignore`.
> Use `.env.example` as the template — it contains no real secrets.

---

## Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_tasks.py -v
```

Current coverage: **84%** (threshold: 70%)

---

## Code Quality

```bash
# Lint check
ruff check .

# Format check
ruff format --check .

# Auto-fix formatting
ruff format .
```

---

## Docker

### Build the image

```bash
docker build -t task-manager-api:local .
```

### Run the container

```bash
docker run --rm -p 8000:8000 task-manager-api:local
```

### With environment variables

```bash
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=WARNING \
  task-manager-api:local
```

---

## Git Workflow

This project uses a **feature branch → Pull Request → CI → merge** workflow:

```
main (protected)
  │
  └── feature/<name>
        ├── make changes
        ├── git add .
        ├── git commit -m "feat: ..."
        └── git push origin feature/<name>
              │
              ▼
          GitHub PR
              │
              ▼
        CI Pipeline runs
        (lint → test → security → docker → trivy)
              │
         ┌───┴───┐
         FAIL   PASS
         │       │
        Fix    Review + Merge → main
```

### Commit message convention

```
feat:     new feature
fix:      bug fix
docs:     documentation only
test:     adding or fixing tests
refactor: code change, no new feature or fix
ci:       CI/CD changes
chore:    tooling, dependencies
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every Pull Request:

| Job | Tool | Purpose |
|-----|------|---------|
| **Lint** | Ruff | Code style + formatting validation |
| **Test** | pytest + pytest-cov | Tests with 70% minimum coverage |
| **Secret Scan** | Gitleaks | Detect accidentally committed secrets |
| **Dependency Audit** | pip-audit | Scan for known CVEs in dependencies |
| **Docker Build** | docker/build-push-action | Build container image |
| **Image Scan** | Trivy | Scan image for HIGH/CRITICAL vulnerabilities |

Each job depends on the previous — if lint fails, tests don't run. If tests fail, security scans don't run.

---

## Security

- **No secrets in code** — all config from environment variables
- **`.env` is gitignored** — never committed
- **`.env.example`** — safe template committed instead
- **GitHub Secrets** — used for CI secrets (DATABASE_URL, tokens)
- **Gitleaks** — scans every PR for accidentally committed credentials
- **pip-audit** — scans Python dependencies for CVEs
- **Trivy** — scans Docker image for OS and package vulnerabilities
- **Non-root Docker user** — container runs as `appuser` (uid 1001)
- **Least-privilege CI permissions** — `contents: read` only

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `greenlet` error in tests | `pip install greenlet==3.1.1` |
| `.env` file not found | Copy `.env.example` to `.env` |
| Port 8000 already in use | `uvicorn app.main:app --port 8001` |
| Tests fail on coverage | Run `pytest --cov=app --cov-report=term-missing` to see missing lines |
| Docker build fails | Ensure `.dockerignore` exists and Docker Desktop is running |

---

## License

MIT
