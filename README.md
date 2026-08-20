<div align="center">

# 🏢 Attendance Tracker

### Full-Stack HR Management System

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[![GitHub stars](https://img.shields.io/github/stars/vegapunk-io/ATS?style=for-the-badge)](https://github.com/vegapunk-io/ATS/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/vegapunk-io/ATS?style=for-the-badge)](https://github.com/vegapunk-io/ATS/network/members)
[![GitHub issues](https://img.shields.io/github/issues/vegapunk-io/ATS?style=for-the-badge)](https://github.com/vegapunk-io/ATS/issues)

---

**A comprehensive attendance management system with 22+ modules covering employee management, leaves, tasks, chat, salary, and more.**

[🚀 Live Demo](http://localhost:8000) | [📖 API Docs](http://localhost:8000/docs) | [🎯 Report Bug](https://github.com/vegapunk-io/ATS/issues)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [📊 Database Schema](#-database-schema)
- [🚀 Quick Start](#-quick-start)
- [🔌 API Endpoints](#-api-endpoints)
- [📁 Project Structure](#-project-structure)
- [🎨 Screenshots](#-screenshots)
- [🔧 Configuration](#-configuration)
- [📝 License](#-license)

---

## ✨ Features

### 👤 User Features

| Feature | Description |
|---------|-------------|
| 🔐 Authentication | Secure JWT-based login/logout |
| ⏰ Check-in/Out | Self-service attendance marking |
| 📅 Calendar View | Visual attendance calendar |
| 🏖️ Leave Management | Apply for leaves with status tracking |
| 💬 Team Chat | Real-time messaging with channels |
| 📋 Task Management | Create, assign, and track tasks |
| 🔔 Notifications | Real-time notification system |
| 👤 Profile Management | Update personal information |

### 👑 Admin Features

| Feature | Description |
|---------|-------------|
| 👥 People Management | Full CRUD for employees |
| 👨‍💼 User Accounts | Create and manage user roles |
| 📊 Attendance Records | View, filter, and edit records |
| 📈 Reports & Analytics | Summary reports with CSV export |
| 🏢 Department Management | Organize teams by departments |
| ⏰ Shift Management | Create and assign shifts |
| 🔄 Shift Swaps | Handle shift swap requests |
| 💰 Salary Management | Generate and manage salaries |
| 🎉 Holiday Calendar | Manage company holidays |
| 📢 Announcements | Post company-wide announcements |
| ⏱️ Overtime Tracking | Approve/reject overtime requests |
| 📝 Activity Logs | Complete audit trail |
| ⚙️ System Settings | Configure application settings |

---

## 🏗️ Architecture

### System Architecture

```mermaid
graph TB
    subgraph Frontend
        A[Browser] -->|HTML/CSS/JS| B[Static Files]
    end
    
    subgraph Backend
        C[FastAPI Server] --> D[Auth Middleware]
        D --> E[API Routes]
        E --> F[Business Logic]
    end
    
    subgraph Database
        G[PostgreSQL] --> H[Users Table]
        G --> I[People Table]
        G --> J[Attendance Table]
        G --> K[Leaves Table]
        G --> L[Tasks Table]
    end
    
    B -->|HTTP| C
    F -->|SQLAlchemy| G
```

### Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant A as FastAPI
    participant D as PostgreSQL
    
    U->>B: Login Request
    B->>A: POST /api/auth/login
    A->>D: Verify Credentials
    D-->>A: User Data
    A-->>B: JWT Token
    B-->>U: Store Token
    
    U->>B: Check-in Request
    B->>A: POST /api/attendance/check-in
    A->>A: Validate Token
    A->>D: Create Record
    D-->>A: Record Created
    A-->>B: Success Response
    B-->>U: Show Check-in Time
```

### Authentication Flow

```mermaid
flowchart LR
    A[Login Form] -->|Credentials| B[POST /api/auth/login]
    B -->|Valid| C[Generate JWT]
    B -->|Invalid| D[Return 401]
    C --> E[Store in localStorage]
    E --> F[Attach to Headers]
    F --> G[Access Protected Routes]
    G -->|Token Valid| H[Return Data]
    G -->|Token Invalid| I[Redirect to Login]
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | FastAPI | REST API Framework |
| **Database** | PostgreSQL | Primary Database |
| **ORM** | SQLAlchemy 2.0 | Database ORM |
| **Auth** | JWT + bcrypt | Authentication |
| **Validation** | Pydantic v2 | Data Validation |
| **Frontend** | JavaScript ES6 | Client-side Logic |
| **Styling** | CSS3 | UI Styling |

---

## 📊 Database Schema

```mermaid
erDiagram
    USERS ||--o{ ATTENDANCE_RECORDS : has
    PEOPLE ||--o{ ATTENDANCE_RECORDS : has
    USERS ||--o| PEOPLE : linked_to
    PEOPLE ||--o{ LEAVES : requests
    PEOPLE ||--o{ TASKS : assigned
    PEOPLE ||--o{ OVERTIME : requests
    DEPARTMENTS ||--o{ PEOPLE : contains
    SHIFTS ||--o{ PEOPLE : assigns
    
    USERS {
        int id PK
        string username UK
        string email UK
        string full_name
        string hashed_password
        string role
        boolean is_active
        int person_id FK
    }
    
    PEOPLE {
        int id PK
        string full_name
        string email
        string group_name
        boolean is_active
        int department_id FK
    }
    
    ATTENDANCE_RECORDS {
        int id PK
        int person_id FK
        date date
        datetime check_in
        datetime check_out
        string status
        text note
    }
    
    LEAVES {
        int id PK
        int person_id FK
        string leave_type
        date start_date
        date end_date
        text reason
        string status
    }
    
    TASKS {
        int id PK
        string title
        text description
        int assigned_to FK
        string priority
        string status
        date due_date
    }
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+

### Installation

```bash
# Clone the repository
git clone https://github.com/vegapunk-io/ATS.git
cd ATS/attendance-tracker

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install tzdata  # Windows only
```

### Database Setup

```sql
CREATE USER attendance WITH PASSWORD 'attendance_dev';
CREATE DATABASE attendance OWNER attendance;
```

### Run the Application

```bash
# Seed the database
python -m scripts.seed

# Start the server
uvicorn app.main:app --reload
```

### Access the Application

| Service | URL |
|---------|-----|
| 🏠 Main App | http://localhost:8000 |
| 📖 API Docs | http://localhost:8000/docs |
| 🔐 Login | http://localhost:8000/login |

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login and get JWT token |
| `GET` | `/api/auth/me` | Get current user info |

### People Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/people` | List all people |
| `POST` | `/api/people` | Add new person |
| `PATCH` | `/api/people/{id}` | Update person |
| `DELETE` | `/api/people/{id}` | Delete person |

### Attendance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/attendance` | List attendance records |
| `GET` | `/api/attendance/today` | Get today's record |
| `POST` | `/api/attendance/check-in` | Self check-in |
| `POST` | `/api/attendance/check-out` | Self check-out |

### Leaves

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/leaves` | List leave requests |
| `POST` | `/api/leaves` | Apply for leave |
| `PATCH` | `/api/leaves/{id}` | Approve/Reject leave |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/tasks` | List tasks |
| `POST` | `/api/tasks` | Create task |
| `PATCH` | `/api/tasks/{id}` | Update task status |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/chat` | Get messages |
| `POST` | `/api/chat` | Send message |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reports/summary` | Get summary report |
| `GET` | `/api/reports/export` | Export to CSV |

---

## 📁 Project Structure

```
ATS/
├── attendance-tracker/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Settings management
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── security.py          # JWT & password hashing
│   │   ├── deps.py              # Dependencies (auth)
│   │   ├── routers/
│   │   │   ├── auth.py          # Authentication routes
│   │   │   ├── users.py         # User management
│   │   │   ├── people.py        # People management
│   │   │   ├── attendance.py    # Attendance tracking
│   │   │   ├── leaves.py        # Leave management
│   │   │   ├── tasks.py         # Task management
│   │   │   ├── chat.py          # Chat messaging
│   │   │   ├── salary.py        # Salary management
│   │   │   ├── reports.py       # Reports & export
│   │   │   └── ...              # 22 modules total
│   │   └── static/
│   │       ├── index.html       # Main SPA
│   │       ├── login.html       # Login page
│   │       ├── app.js           # Frontend logic
│   │       └── styles.css       # CSS styling
│   ├── scripts/
│   │   └── seed.py              # Database seeding
│   ├── requirements.txt
│   └── .env.example
└── LICENSE
```

---

## 👥 Default Accounts

| Role | Username | Password |
|------|----------|----------|
| 👑 Admin | `admin` | `admin123` |
| 👤 User | `rahul` | `user123` |

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

Made with ❤️ by [Vegapunk-io](https://github.com/vegapunk-io)

</div>
