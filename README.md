# Ant Colony & Metaheuristics FastAPI Backend

A high-performance Python FastAPI service for optimizing offshore wind farm turbine maintenance routing. The service computes optimal maintenance navigation routes using bio-inspired metaheuristic algorithms—balancing travel distance against turbine fault downtime costs.

---

## ✨ Features

- 🛸 **Bio-Inspired Metaheuristics**: Includes **Ant Colony Optimization (ACO)**, **Genetic Algorithm (GA)**, and **Memetic Algorithm (GA + 2-opt local search)** for maintenance route planning.
- 🗺️ **Geographical Route Normalization**: Computes optimal navigation cycles starting and ending at the dock (`Doca`), taking turbine locations and failure rate downtime costs into account.
- 🗄️ **Dual Database & Auto Fallback**: Native support for **PostgreSQL** with automatic fallback and auto-seeding to local **SQLite** (`sql_app.db`) if PostgreSQL is unavailable, plus interchangeable ANSI SQL generation ([`database/database.sql`](database/database.sql)).
- ⚡ **FastAPI REST API**: Interactive OpenAPI / Swagger interface for easy integration with frontend dashboards (React, Vite, Next.js).
- 🧪 **Comprehensive Test Suite**: Automated unit and integration tests covering metaheuristic algorithms, API endpoints, SQL generation, and grid search benchmarking.
- 📦 **Modern Packaging**: Supports both [`uv`](https://docs.astral.sh/uv/) and standard `pip` / `venv` workflows.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/), Starlette, Uvicorn
- **Database & ORM**: PostgreSQL, SQLite, [SQLAlchemy](https://www.sqlalchemy.org/)
- **Data & Algorithms**: NumPy, Pandas, SciPy, Matplotlib
- **Package & Environment Management**: [uv](https://docs.astral.sh/uv/), `pyproject.toml`, `pip`, `requirements.txt`
- **Testing**: `pytest`, `httpx`, `TestClient`

---

## 🚀 Quick Start

### 1. Prerequisites & Installation

Clone the repository:

```bash
git clone https://github.com/Klebiano/ant_colony_fast_api_backend.git
cd ant_colony_fast_api_backend
```

#### Option A: Using `uv` (Recommended)

```bash
# Install dependencies with uv
uv sync
```

#### Option B: Using standard `pip` & `venv`

```bash
# Create virtual environment and install packages
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root directory (optional for SQLite, required for PostgreSQL):

```env
# Optional: force SQLite mode directly
DB_ENGINE=sqlite

# Or configure PostgreSQL connection:
DB_user=postgres
DB_password=your_password
DB_name=wind_maintenance
```

> [!NOTE]
> If PostgreSQL is unreachable or not configured, the application automatically falls back to SQLite (`sql_app.db`) and seeds it from `database/database.sql`.

### 3. Database Seeding & SQL Generation

Generate the interchangeable SQL database script from the [`database/`](database/) CSV files:

```bash
# Using uv
uv run python tests/generate_sql.py

# Or with activated venv
python tests/generate_sql.py
```

Import `database/database.sql` manually if desired:

```bash
# For PostgreSQL
psql -U postgres -d wind_maintenance -f database/database.sql

# For SQLite (local test database)
sqlite3 sql_app.db < database/database.sql
```

### 4. Running the Development Server

Start the FastAPI server:

```bash
# Using uv
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or with activated venv
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests

Run the complete automated test suite (26+ unit and integration tests):

```bash
# Using uv
uv run pytest

# Or with activated venv
pytest
```

Run specific test modules:

```bash
# Heuristics & routing tests (ACO, GA, Memetic, elitism, 2-opt, scaling)
uv run pytest tests/test_heuristics.py

# API endpoint tests
uv run pytest tests/test_api_endpoints.py

# Database SQL generation & CRUD tests
uv run pytest tests/test_database_sql.py
```

Run hyperparameter grid search and benchmark scripts:

```bash
uv run python tests/ant_colony_tests.py
uv run python tests/genetic_algo_tests.py
```

---

## 📡 Main API Endpoints

| Method | Endpoint | Query Params | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/ant-colony/run-route-optimizer` | `algorithm` (`Ant Colony`, `Genetic`, `Memetic`) | Runs route optimization algorithm balancing distance and downtime cost |
| `GET` | `/ant-colony/get-turbines-map` | — | Fetches geographical coordinates for wind farm turbines and dock |
| `GET` | `/ant-colony/get-subsystems` | — | Retrieves turbine subsystem definitions and failure parameters |

### Example Optimization Request

`POST /ant-colony/run-route-optimizer?algorithm=Memetic`

```json
[
  {
    "turbine_id": 2,
    "subsystem_name": "Electrical System",
    "fault_type": "Minor"
  },
  {
    "turbine_id": 3,
    "subsystem_name": "Rotor Hub",
    "fault_type": "Major"
  }
]
```

### Example Response

```json
{
  "turbine_order": ["Doca", "Turbine_2", "Turbine_3", "Doca"],
  "turbine_order_to_show": ["Doca", "Turbine_2", "Turbine_3", "Doca"],
  "best_path": [0, 1, 2, 0],
  "best_path_length": 1.4142,
  "best_downtime_days": 2.5,
  "best_path_len_downtime": 3.9142,
  "time_to_run_sec": 0.045
}
```

---

## 📄 License

Distributed under the MIT License.
