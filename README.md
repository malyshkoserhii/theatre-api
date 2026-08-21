# Theatre API Service

A scalable RESTful API service built with Django REST Framework for managing theatre plays, performance schedules, theatre halls, actors, ticket reservations, and user authentication.

---

## 🚀 Key Features

* **JWT Authentication:** Secure token-based authentication (Access & Refresh tokens) via `djangorestframework-simplejwt`.
* **Custom User Model:** Authentication powered by `email` instead of traditional usernames.
* **Role-Based Access Control:**
  * **Anonymous Users:** Read-only access to Swagger documentation and registration/login endpoints.
  * **Authenticated Users:** Ability to view plays/performances and create ticket reservations.
  * **Admin Staff:** Full CRUD access to manage genres, actors, halls, plays, and performance schedules.
* **Database Query Optimization:** Fully mitigated N+1 query overhead using `select_related`, `prefetch_related`, and database annotations (`F()` expressions, `Count()`).
* **Filtering & Pagination:** Comprehensive query-parameter filters (by title, genres, actors, dates) with global page-number pagination.
* **API Throttling (Rate Limiting):** Dedicated rate limiting for authenticated and anonymous requests to prevent API abuse.
* **Interactive API Documentation:** Interactive Swagger UI and Redoc generated dynamically via `drf-spectacular`.
* **Comprehensive Test Suite:** Unit and integration tests covering authentication, permission barriers, filtering, and reservation logic.

---

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Framework:** Django & Django REST Framework
* **Auth:** Simple JWT (`djangorestframework-simplejwt`)
* **Documentation:** `drf-spectacular` (OpenAPI 3.0 / Swagger)
* **Containerization:** Docker & Docker Compose
* **Code Quality:** Flake8

---

## 🐳 Getting Started with Docker

### 1. Clone the repository
```bash
git clone https://github.com/malyshkoserhii/theatre-api.git
cd theatre-api
```

### 2. Environment Configuration
Create a .env file in the project root:
```bash
POSTGRES_PASSWORD=theatre
POSTGRES_USER=theatre
POSTGRES_DB=theatre
POSTGRES_HOST=db
POSTGRES_PORT=5432
PGDATA=/var/lib/postgresql/data
```

### 3. Build and Run Containers
```bash
docker compose up --build
```
The API server will be available at http://localhost:8000/.

## ⚙️ Initial Setup

### Apply Migrations
```bash
docker compose exec app python manage.py migrate
```

### Create a Superuser
```bash
docker compose exec app python manage.py createsuperuser
```

## 📚 API Endpoints

### Authentication & User Management

| Method | Endpoint | Description | Roles |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/user/register/` | Register a new user | Public |
| `POST` | `/api/user/token/` | Obtain JWT access and refresh token pair | Public |
| `POST` | `/api/user/token/refresh/` | Refresh JWT access token | Public |
| `POST` | `/api/user/token/verify/` | Verify token validity | Public |
| `GET` | `/api/user/me/` | Retrieve current user profile | Authenticated |
| `PATCH` | `/api/user/me/` | Update current user profile | Authenticated |

### Theatre Management

| Method | Endpoint | Description | Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/theatre/genres/` | List all genres | Authenticated |
| `POST` | `/api/theatre/genres/` | Create a new genre | Admin |
| `GET` | `/api/theatre/actors/` | List all actors | Authenticated |
| `POST` | `/api/theatre/actors/` | Create a new actor | Admin |
| `GET` | `/api/theatre/theatre_halls/` | List all theatre halls | Authenticated |
| `POST` | `/api/theatre/theatre_halls/` | Create a new theatre hall | Admin |
| `GET` | `/api/theatre/plays/` | List plays (supports filters & pagination) | Authenticated |
| `POST` | `/api/theatre/plays/` | Create a new play | Admin |
| `GET` | `/api/theatre/plays/{id}/` | Retrieve detailed play info | Authenticated |
| `PATCH` | `/api/theatre/plays/{id}/` | Update play details | Admin |
| `DELETE` | `/api/theatre/plays/{id}/` | Delete a play | Admin |
| `GET` | `/api/theatre/performances/` | List performances (supports filters & pagination) | Authenticated |
| `POST` | `/api/theatre/performances/` | Schedule a new performance | Admin |
| `GET` | `/api/theatre/performances/{id}/` | Retrieve performance info and taken seats | Authenticated |
| `PATCH` | `/api/theatre/performances/{id}/` | Update scheduled performance | Admin |
| `DELETE` | `/api/theatre/performances/{id}/` | Delete a performance | Admin |
| `GET` | `/api/theatre/reservations/` | List current user's reservation history | Authenticated |
| `POST` | `/api/theatre/reservations/` | Book tickets and create a reservation | Authenticated |

## 🔍 Query Parameters & Filtering

* **Filter plays by title:** `GET /api/theatre/plays/?title=hamlet`
* **Filter plays by genres (IDs):** `GET /api/theatre/plays/?genres=1,2`
* **Filter plays by actors (IDs):** `GET /api/theatre/plays/?actors=3,5`
* **Filter performances by date:** `GET /api/theatre/performances/?date=2026-10-15`
* **Filter performances by play ID:** `GET /api/theatre/performances/?play=1`
* **Pagination navigation:** `GET /api/theatre/plays/?page=2`

## 📖 API Documentation

Once the server is running, explore and test the endpoints directly in the browser:

* **Swagger UI:** [http://localhost:8000/api/doc/swagger/](http://localhost:8000/api/doc/swagger/)
* **Redoc:** [http://localhost:8000/api/doc/redoc/](http://localhost:8000/api/doc/redoc/)
* **Raw OpenAPI Schema:** [http://localhost:8000/api/doc/schema/](http://localhost:8000/api/doc/schema/)

### 🧪 Testing & Code Quality
#### Run Automated Tests
```bash
docker compose exec app python manage.py test
```
#### Run Flake8 Linter
```bash
docker compose exec app flake8
```
