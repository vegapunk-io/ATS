# Attendance Tracker

A full-stack attendance tracking system built with **FastAPI**, **PostgreSQL**, and **vanilla JavaScript**.

## Features

### For Admins
- Manage people (employees/students)
- Create and manage user accounts
- View and edit attendance records
- Generate attendance reports
- Export data to CSV

### For Users
- Self check-in/check-out
- View personal attendance history
- Dashboard with weekly overview

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | JWT + bcrypt |
| Frontend | Vanilla JS, HTML, CSS |
| Validation | Pydantic v2 |

## Quick Start

### 1. Prerequisites
- Python 3.10+
- PostgreSQL

### 2. Database Setup
```sql
CREATE USER attendance WITH PASSWORD 'attendance_dev';
CREATE DATABASE attendance OWNER attendance;
```

### 3. Install Dependencies
```bash
cd attendance-tracker
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pip install tzdata  # Required for Windows
```

### 4. Seed Database
```bash
python -m scripts.seed
```

### 5. Run Server
```bash
uvicorn app.main:app --reload
```

### 6. Access Application
- **App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Login**: http://localhost:8000/login

## Default Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| User | rahul | user123 |

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login (OAuth2)
- `GET /api/auth/me` - Get current user

### Users (Admin)
- `GET /api/users` - List users
- `POST /api/users` - Create user
- `PATCH /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

### People (Admin)
- `GET /api/people` - List people
- `POST /api/people` - Add person
- `PATCH /api/people/{id}` - Update person
- `DELETE /api/people/{id}` - Delete person

### Attendance
- `GET /api/attendance` - List records
- `POST /api/attendance/check-in` - Self check-in
- `POST /api/attendance/check-out` - Self check-out
- `POST /api/attendance/manual` - Manual entry (Admin)
- `PATCH /api/attendance/{id}` - Update record
- `DELETE /api/attendance/{id}` - Delete record

### Reports (Admin)
- `GET /api/reports/summary` - Summary report
- `GET /api/reports/export` - Export CSV

## Project Structure

```
attendance-tracker/
├── app/
│   ├── main.py          # FastAPI app entry
│   ├── config.py        # Settings
│   ├── database.py      # DB connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── security.py      # JWT & passwords
│   ├── deps.py          # Dependencies
│   ├── routers/         # API routes
│   └── static/          # Frontend
├── scripts/
│   └── seed.py          # DB seeding
└── requirements.txt
```

## License

MIT
