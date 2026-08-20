# Attendance Tracker - Demo Video Script

## Overview
A full-stack attendance tracking system built with FastAPI, PostgreSQL, and vanilla JavaScript.

---

## Part 1: Project Structure (30 seconds)
Show the project folder structure:
```
attendance-tracker/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── security.py      # JWT & password hashing
│   ├── config.py        # Settings management
│   ├── database.py      # Database connection
│   ├── deps.py          # Dependencies (auth)
│   ├── routers/         # API endpoints
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── people.py
│   │   ├── attendance.py
│   │   └── reports.py
│   └── static/          # Frontend files
│       ├── index.html
│       ├── login.html
│       ├── app.js
│       └── styles.css
├── scripts/
│   └── seed.py          # Database seeding
└── requirements.txt
```

---

## Part 2: Backend Code Highlights (1 minute)

### Database Models (models.py)
Show the User, Person, and AttendanceRecord models.

### Authentication (security.py)
Show password hashing with bcrypt and JWT token creation.

### API Endpoints (routers/)
- POST /api/auth/login - OAuth2 login
- GET /api/auth/me - Current user
- CRUD /api/users - User management
- CRUD /api/people - Person management
- POST /api/attendance/check-in - Self check-in
- POST /api/attendance/check-out - Self check-out
- GET /api/reports/summary - Attendance reports

---

## Part 3: Frontend Features (2 minutes)

### Login Page
1. Show clean login form
2. Demo admin login (admin / admin123)
3. Show JWT stored in localStorage

### Dashboard
1. Show today's attendance status
2. Check-in / Check-out buttons
3. Weekly attendance strip
4. Recent attendance records

### Admin Features (login as admin)
1. **People Management**
   - View all people
   - Add new person
   - Edit person
   - Delete person

2. **User Management**
   - View all users
   - Create new user
   - Assign roles (admin/user)
   - Link user to person

3. **Attendance Records**
   - Filter by date range
   - Filter by person
   - Manual record entry
   - Edit/Delete records

4. **Reports**
   - Summary per person
   - Attendance rate calculation
   - Export to CSV

### User Features (login as regular user)
1. View own attendance
2. Self check-in/check-out
3. View recent records

---

## Part 4: API Demo (1 minute)

### Using curl or Postman:
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=admin123"

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"

# List users
curl http://localhost:8000/api/users \
  -H "Authorization: Bearer <token>"

# Check in
curl -X POST http://localhost:8000/api/attendance/check-in \
  -H "Authorization: Bearer <token>"
```

---

## Part 5: Technical Highlights (30 seconds)

1. **Async Python** - FastAPI with async/await
2. **PostgreSQL** - Production-ready database
3. **JWT Authentication** - Secure token-based auth
4. **SQLAlchemy 2.0** - Modern ORM with async support
5. **Pydantic v2** - Data validation
6. **Clean Architecture** - Separation of concerns

---

## Recording Tips

1. Use screen recording software (OBS, Camtasia, or built-in)
2. Show code in VS Code with syntax highlighting
3. Show the app running in browser side-by-side
4. Use terminal to show API calls
5. Keep it under 5 minutes total
