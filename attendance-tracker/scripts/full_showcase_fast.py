"""
Quick Full Showcase Video - Code + Web App (Fast Version)
"""

import os
import sys
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont


W, H = 1920, 1080
FPS = 30
FRAMES_DIR = Path("scripts/frames")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
frame_count = 0


def font(size, bold=False):
    for f in ["consolab.ttf", "consola.ttf", "cour.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except IOError:
            continue
    return ImageFont.load_default()


def save(img):
    global frame_count
    img.save(FRAMES_DIR / f"f_{frame_count:05d}.png")
    frame_count += 1


def gradient(c1, c2):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c1[i]*(1-r)+c2[i]*r) for i in range(3)))
    return img


def code_frame(title, lines):
    img = Image.new("RGB", (W, H), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,50)], fill=(45,45,48))
    d.text((20,15), title, fill="white", font=font(20))
    d.ellipse([(W-80,15),(W-60,35)], fill=(255,95,86))
    d.ellipse([(W-55,15),(W-35,35)], fill=(255,189,46))
    d.ellipse([(W-30,15),(W-10,35)], fill=(39,201,63))
    f = font(22)
    y = 70
    for i, line in enumerate(lines[:38]):
        color = (86,156,214) if any(k in line for k in ['def','class','import','from','return','async','await']) else (206,145,120) if '"""' in line or '"' in line else (87,166,74) if line.strip().startswith('#') else (212,212,212)
        d.text((70, y), f"{i+1:3d}", fill=(85,85,85), font=font(18))
        d.text((110, y), line[:95], fill=color, font=f)
        y += 28
    return img


def browser_frame(url, title, lines):
    img = Image.new("RGB", (W, H), (255,255,255))
    d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,90)], fill=(222,225,230))
    d.rounded_rectangle([(100,25),(W-100,65)], radius=20, fill="white")
    d.text((120,33), url, fill=(80,80,80), font=font(22))
    d.text((20,5), title, fill=(80,80,80), font=font(16))
    y = 120
    for line in lines[:38]:
        d.text((80, y), line, fill=(50,50,50), font=font(24))
        y += 40
    return img


def slide_frame(title, items, icon="•"):
    img = gradient((20,60,120), (10,30,60))
    d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,50)], fill=(240,240,240))
    d.text((20,15), title, fill="black", font=font(20))
    d.text(((W-d.textbbox((0,0),title,font=font(48,True))[2])//2, 80), title, fill="white", font=font(48,True))
    y = 180
    for item in items:
        d.text((150, y), f"{icon} {item}", fill=(200,220,255), font=font(28))
        y += 55
    return img


print("Generating frames...")

# 1. TITLE (5 sec = 150 frames)
for _ in range(150):
    img = gradient((20,80,160), (10,40,80))
    d = ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=font(72,True))[2])//2, 350), "Attendance Tracker", fill="white", font=font(72,True))
    d.text(((W-d.textbbox((0,0),"Full-Stack FastAPI Application",font=font(36))[2])//2, 450), "Full-Stack FastAPI Application", fill=(180,200,230), font=font(36))
    d.text(((W-d.textbbox((0,0),"FastAPI • PostgreSQL • SQLAlchemy • JWT • Vanilla JS",font=font(28))[2])//2, 520), "FastAPI • PostgreSQL • SQLAlchemy • JWT • Vanilla JS", fill=(150,170,200), font=font(28))
    save(img)

# 2. PROJECT STRUCTURE (10 sec)
structure = [
    "attendance-tracker/",
    "├── app/",
    "│   ├── main.py          # FastAPI entry point",
    "│   ├── models.py        # SQLAlchemy models",
    "│   ├── schemas.py       # Pydantic schemas",
    "│   ├── security.py      # JWT & passwords",
    "│   ├── config.py        # Settings",
    "│   ├── database.py      # DB connection",
    "│   ├── deps.py          # Dependencies",
    "│   ├── routers/         # API routes",
    "│   │   ├── auth.py",
    "│   │   ├── users.py",
    "│   │   ├── people.py",
    "│   │   ├── attendance.py",
    "│   │   └── reports.py",
    "│   └── static/          # Frontend",
    "│       ├── index.html",
    "│       ├── login.html",
    "│       ├── app.js",
    "│       └── styles.css",
    "├── scripts/",
    "│   └── seed.py",
    "└── requirements.txt",
]
for _ in range(300):
    save(code_frame("Project Structure", structure))

# 3. MODELS (15 sec)
models = [
    '"""SQLAlchemy Models"""',
    "from sqlalchemy import Column, Integer, String, DateTime, ForeignKey",
    "from sqlalchemy.orm import relationship",
    "from app.database import Base",
    "",
    "class User(Base):",
    '    __tablename__ = "users"',
    "    id = Column(Integer, primary_key=True, index=True)",
    "    username = Column(String, unique=True, index=True)",
    "    hashed_password = Column(String)",
    "    role = Column(String, default='user')",
    "    person_id = Column(Integer, ForeignKey('people.id'))",
    "    person = relationship('Person', back_populates='user')",
    "",
    "class Person(Base):",
    '    __tablename__ = "people"',
    "    id = Column(Integer, primary_key=True, index=True)",
    "    name = Column(String, index=True)",
    "    email = Column(String, unique=True)",
    "    department = Column(String)",
    "    created_at = Column(DateTime)",
    "    user = relationship('User', back_populates='person')",
    "    attendance = relationship('AttendanceRecord', back_populates='person')",
    "",
    "class AttendanceRecord(Base):",
    '    __tablename__ = "attendance_records"',
    "    id = Column(Integer, primary_key=True, index=True)",
    "    person_id = Column(Integer, ForeignKey('people.id'))",
    "    date = Column(DateTime)",
    "    check_in = Column(DateTime)",
    "    check_out = Column(DateTime)",
    "    status = Column(String)",
    "    person = relationship('Person', back_populates='attendance')",
]
for _ in range(450):
    save(code_frame("app/models.py", models))

# 4. SECURITY (15 sec)
security = [
    '"""JWT & Password Security"""',
    "from datetime import datetime, timedelta",
    "from jose import JWTError, jwt",
    "from passlib.context import CryptContext",
    "from app.config import settings",
    "",
    "pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')",
    "",
    "def verify_password(plain, hashed):",
    "    return pwd_context.verify(plain, hashed)",
    "",
    "def get_password_hash(password):",
    "    return pwd_context.hash(password)",
    "",
    "def create_token(data, expires_delta=None):",
    "    to_encode = data.copy()",
    "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))",
    "    to_encode.update({'exp': expire})",
    "    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm='HS256')",
    "",
    "def decode_token(token):",
    "    try:",
    "        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])",
    "    except JWTError:",
    "        return None",
    "",
    "async def authenticate_user(db, username, password):",
    "    user = await db.query(User).filter(User.username == username).first()",
    "    if not user or not verify_password(password, user.hashed_password):",
    "        return None",
    "    return user",
]
for _ in range(450):
    save(code_frame("app/security.py", security))

# 5. AUTH ROUTER (15 sec)
auth = [
    '"""Authentication Routes"""',
    "from fastapi import APIRouter, Depends, HTTPException",
    "from fastapi.security import OAuth2PasswordRequestForm",
    "from app.deps import get_db",
    "from app.security import authenticate_user, create_token",
    "",
    "router = APIRouter(prefix='/api/auth', tags=['auth'])",
    "",
    "@router.post('/login')",
    "async def login(form_data: OAuth2PasswordRequestForm = Depends(),",
    "                db = Depends(get_db)):",
    "    user = await authenticate_user(db, form_data.username, form_data.password)",
    "    if not user:",
    "        raise HTTPException(status_code=401)",
    "    token = create_token(data={'sub': str(user.id), 'role': user.role})",
    "    return {'access_token': token, 'token_type': 'bearer'}",
    "",
    "@router.get('/me')",
    "async def get_current_user(current_user = Depends(get_current_user)):",
    "    return {",
    "        'id': current_user.id,",
    "        'username': current_user.username,",
    "        'role': current_user.role,",
    "    }",
]
for _ in range(450):
    save(code_frame("app/routers/auth.py", auth))

# 6. FRONTEND JS (15 sec)
js = [
    '// Frontend JavaScript',
    'const API = "/api";',
    'let token = localStorage.getItem("token");',
    '',
    'async function login(username, password) {',
    '    const res = await fetch(`${API}/auth/login`, {',
    '        method: "POST",',
    '        headers: {"Content-Type": "application/x-www-form-urlencoded"},',
    '        body: `username=${username}&password=${password}`',
    '    });',
    '    if (res.ok) {',
    '        const data = await res.json();',
    '        localStorage.setItem("token", data.access_token);',
    '        window.location.href = "/";',
    '    }',
    '}',
    '',
    'async function checkIn() {',
    '    await fetch(`${API}/attendance/check-in`, {',
    '        method: "POST",',
    '        headers: {"Authorization": `Bearer ${token}`}',
    '    });',
    '    loadDashboard();',
    '}',
    '',
    'async function checkOut() {',
    '    await fetch(`${API}/attendance/check-out`, {',
    '        method: "POST",',
    '        headers: {"Authorization": `Bearer ${token}`}',
    '    });',
    '    loadDashboard();',
    '}',
]
for _ in range(450):
    save(code_frame("static/app.js", js))

# 7. LOGIN PAGE (10 sec)
login = [
    "",
    "╔══════════════════════════════════════════════╗",
    "║           ATTENDANCE TRACKER                 ║",
    "╠══════════════════════════════════════════════╣",
    "║                                              ║",
    "║   Username:  [ admin                     ]   ║",
    "║                                              ║",
    "║   Password:  [ ••••••                    ]   ║",
    "║                                              ║",
    "║            [     LOGIN     ]                 ║",
    "║                                              ║",
    "╚══════════════════════════════════════════════╝",
]
for _ in range(300):
    save(browser_frame("http://localhost:8000/login", "Login", login))

# 8. DASHBOARD (10 sec)
dash = [
    "┌─────────────────────────────────────────────────┐",
    "│  ATTENDANCE TRACKER              [Admin] [Logout]│",
    "├───────────┬─────────────────────────────────────┤",
    "│ Menu      │  Dashboard                          │",
    "├───────────┼─────────────────────────────────────┤",
    "│ Dashboard │  Today: Monday, Aug 10, 2026        │",
    "│ People    │                                     │",
    "│ Users     │  Status: CHECKED IN                 │",
    "│ Attendance│  Check-in: 09:00 AM                 │",
    "│ Reports   │  Check-out: --:--                   │",
    "│           │                                     │",
    "│           │  [CHECK OUT]                        │",
    "│           │                                     │",
    "│           │  Weekly: Mon✓ Tue✓ Wed✓ Thu✓ Fri    │",
    "│           │                                     │",
    "│           │  Recent:                            │",
    "│           │  08/10 - Present (09:00-            )",
    "│           │  08/09 - Present (08:55-17:05)      ",
    "│           │  08/08 - Present (09:02-17:10)      ",
    "└───────────┴─────────────────────────────────────┘",
]
for _ in range(300):
    save(browser_frame("http://localhost:8000/", "Dashboard", dash))

# 9. PEOPLE PAGE (10 sec)
people = [
    "┌─────────────────────────────────────────────────┐",
    "│  ATTENDANCE TRACKER              [Admin] [Logout]│",
    "├───────────┬─────────────────────────────────────┤",
    "│ Menu      │  People Management                  │",
    "├───────────┼─────────────────────────────────────┤",
    "│ Dashboard │  [+ Add Person]                     │",
    "│ People    │                                     │",
    "│ Users     │  Name        Email        Dept      │",
    "│ Attendance│  ─────────────────────────────────  │",
    "│ Reports   │  Aarav      aarav@mail   IT        │",
    "│           │  Priya      priya@mail   HR        │",
    "│           │  Rahul      rahul@mail   Sales     │",
    "│           │  Neha       neha@mail    IT        │",
    "│           │  Vikram     vikram@mail  Marketing │",
    "│           │                                     │",
    "│           │  [Edit] [Delete]                    │",
    "└───────────┴─────────────────────────────────────┘",
]
for _ in range(300):
    save(browser_frame("http://localhost:8000/people", "People", people))

# 10. ATTENDANCE RECORDS (10 sec)
attend = [
    "┌─────────────────────────────────────────────────┐",
    "│  ATTENDANCE TRACKER              [Admin] [Logout]│",
    "├───────────┬─────────────────────────────────────┤",
    "│ Menu      │  Attendance Records                 │",
    "├───────────┼─────────────────────────────────────┤",
    "│ Dashboard │  Date Range: [08/01] to [08/10]     │",
    "│ People    │  Person: [All ▼]                    │",
    "│ Users     │  [Search]                           │",
    "│ Attendance│                                     │",
    "│ Reports   │  Date     Name      In     Out     │",
    "│           │  ─────────────────────────────────  │",
    "│           │  08/10   Aarav     09:00  --:--    │",
    "│           │  08/10   Priya     08:55  17:02    │",
    "│           │  08/09   Aarav     08:55  17:05    │",
    "│           │  08/09   Rahul     09:10  18:00    │",
    "│           │  [Export CSV]                       │",
    "└───────────┴─────────────────────────────────────┘",
]
for _ in range(300):
    save(browser_frame("http://localhost:8000/attendance", "Attendance", attend))

# 11. ENDING (5 sec)
for _ in range(150):
    img = gradient((20,80,160), (10,40,80))
    d = ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=font(72,True))[2])//2, 350), "Attendance Tracker", fill="white", font=font(72,True))
    d.text(((W-d.textbbox((0,0),"Thank You",font=font(48))[2])//2, 450), "Thank You", fill=(180,200,230), font=font(48))
    save(img)

print(f"Generated {frame_count} frames")

# Compile with ffmpeg
print("Compiling video...")
out = "attendance_tracker_full_showcase.mp4"
subprocess.run([
    "ffmpeg", "-y", "-framerate", str(FPS),
    "-i", str(FRAMES_DIR / "f_%05d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-preset", "fast", "-crf", "23", out
], check=True)

# Cleanup
import shutil
shutil.rmtree(FRAMES_DIR)

print(f"Done! {out}")
print(f"Duration: {frame_count/FPS:.0f} seconds")
