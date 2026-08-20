"""
Quick 3-min Showcase - Lower resolution for speed
"""
import os, sys, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
DIR = Path("scripts/frames")
DIR.mkdir(parents=True, exist_ok=True)
fc = 0

def f(sz):
    for n in ["consola.ttf","cour.ttf","arial.ttf"]:
        try: return ImageFont.truetype(n, sz)
        except (IOError, OSError): pass
    return ImageFont.load_default()

def s(img):
    global fc; img.save(DIR / f"f_{fc:04d}.png"); fc += 1

def grad(c1,c2):
    img = Image.new("RGB",(W,H)); d = ImageDraw.Draw(img)
    for y in range(H):
        r=y/H; d.line([(0,y),(W,y)], fill=tuple(int(c1[i]*(1-r)+c2[i]*r) for i in range(3)))
    return img

def code(title, lines):
    img = Image.new("RGB",(W,H),(30,30,30)); d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,40)], fill=(45,45,48))
    d.text((15,10), title, fill="white", font=f(16))
    d.ellipse([(W-60,10),(W-48,22)], fill=(255,95,86))
    d.ellipse([(W-44,10),(W-32,22)], fill=(255,189,46))
    d.ellipse([(W-28,10),(W-16,22)], fill=(39,201,63))
    fn = f(18); y=55
    for i,l in enumerate(lines[:30]):
        c=(86,156,214) if any(k in l for k in['def','class','import','from','return','async','await']) else (206,145,120) if '"""' in l or '"' in l else (212,212,212)
        d.text((50,y), f"{i+1:2d}", fill=(85,85,85), font=f(14))
        d.text((80,y), l[:85], fill=c, font=fn); y+=24
    return img

def browser(url, title, lines):
    img = Image.new("RGB",(W,H),(255,255,255)); d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,70)], fill=(222,225,230))
    d.rounded_rectangle([(80,15),(W-80,50)], radius=15, fill="white")
    d.text((95,22), url, fill=(80,80,80), font=f(16))
    d.text((10,3), title, fill=(80,80,80), font=f(12))
    y=90
    for l in lines[:28]:
        d.text((60,y), l, fill=(50,50,50), font=f(20)); y+=30
    return img

print("Generating frames...")

# Title (3s)
for _ in range(72):
    img=grad((20,80,160),(10,40,80)); d=ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=f(56))[2])//2,250),"Attendance Tracker",fill="white",font=f(56))
    d.text(((W-d.textbbox((0,0),"Full-Stack FastAPI App",font=f(28))[2])//2,330),"Full-Stack FastAPI App",fill=(180,200,230),font=f(28))
    s(img)

# Structure (8s)
struct=["attendance-tracker/","├── app/","│   ├── main.py","│   ├── models.py","│   ├── schemas.py","│   ├── security.py","│   ├── config.py","│   ├── database.py","│   ├── routers/","│   │   ├── auth.py","│   │   ├── users.py","│   │   ├── people.py","│   │   ├── attendance.py","│   │   └── reports.py","│   └── static/","│       ├── index.html","│       ├── app.js","│       └── styles.css","├── scripts/seed.py","└── requirements.txt"]
for _ in range(192): s(code("Project Structure",struct))

# Models (12s)
models=['"""Models"""',"from sqlalchemy import Column, Integer, String, DateTime, ForeignKey","from sqlalchemy.orm import relationship","from app.database import Base","","class User(Base):",'    __tablename__ = "users',"    id = Column(Integer, primary_key=True)","    username = Column(String, unique=True)","    hashed_password = Column(String)","    role = Column(String, default='user')","    person_id = Column(Integer, ForeignKey('people.id'))","    person = relationship('Person')","","class Person(Base):",'    __tablename__ = "people',"    id = Column(Integer, primary_key=True)","    name = Column(String)","    email = Column(String, unique=True)","    department = Column(String)","    created_at = Column(DateTime)","    user = relationship('User')","    attendance = relationship('AttendanceRecord')","","class AttendanceRecord(Base):",'    __tablename__ = "attendance_records',"    id = Column(Integer, primary_key=True)","    person_id = Column(Integer, ForeignKey('people.id'))","    date = Column(DateTime)","    check_in = Column(DateTime)","    check_out = Column(DateTime)","    status = Column(String)","    person = relationship('Person')"]
for _ in range(288): s(code("app/models.py",models))

# Security (12s)
sec=['"""JWT Security"""',"from datetime import datetime, timedelta","from jose import jwt","from passlib.context import CryptContext","from app.config import settings","","pwd_context = CryptContext(schemes=['bcrypt'])","","def verify_password(plain, hashed):","    return pwd_context.verify(plain, hashed)","","def hash_password(password):","    return pwd_context.hash(password)","","def create_token(data):","    expire = datetime.utcnow() + timedelta(minutes=30)","    return jwt.encode({**data, 'exp': expire}, settings.SECRET_KEY, 'HS256')","","def decode_token(token):","    try: return jwt.decode(token, settings.SECRET_KEY, ['HS256'])","    except: return None","","async def authenticate(db, username, password):","    user = await db.query(User).filter(User.username == username).first()","    if user and verify_password(password, user.hashed_password):","        return user","    return None"]
for _ in range(288): s(code("app/security.py",sec))

# Auth Router (12s)
auth=['"""Auth Routes"""',"from fastapi import APIRouter, Depends, HTTPException","from fastapi.security import OAuth2PasswordRequestForm","from app.security import authenticate, create_token","","router = APIRouter(prefix='/api/auth')","","@router.post('/login')","async def login(form: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):","    user = await authenticate(db, form.username, form.password)","    if not user: raise HTTPException(status_code=401)","    return {'access_token': create_token({'sub': str(user.id), 'role': user.role})}","","@router.get('/me')","async def me(user = Depends(get_current_user)):","    return {'id': user.id, 'username': user.username, 'role': user.role}"]
for _ in range(288): s(code("app/routers/auth.py",auth))

# Frontend JS (12s)
js = [
    '// Frontend JavaScript',
    'const API = "/api";',
    'let token = localStorage.getItem("token");',
    '',
    'async function login(u, p) {',
    '    const r = await fetch(API + "/auth/login", {',
    '        method: "POST",',
    '        headers: {"Content-Type": "application/x-www-form-urlencoded"},',
    '        body: "username=" + u + "&password=" + p',
    '    });',
    '    if (r.ok) {',
    '        const d = await r.json();',
    '        localStorage.setItem("token", d.access_token);',
    '        location.href = "/";',
    '    }',
    '}',
    '',
    'async function checkIn() {',
    '    await fetch(API + "/attendance/check-in", {',
    '        method: "POST",',
    '        headers: {"Authorization": "Bearer " + token}',
    '    });',
    '    loadDashboard();',
    '}',
    '',
    'async function checkOut() {',
    '    await fetch(API + "/attendance/check-out", {',
    '        method: "POST",',
    '        headers: {"Authorization": "Bearer " + token}',
    '    });',
    '    loadDashboard();',
    '}',
]
for _ in range(288): s(code("static/app.js",js))

# Login page (8s)
login=["","╔═══════════════════════════════════════╗","║      ATTENDANCE TRACKER               ║","╠═══════════════════════════════════════╣","║                                       ║","║  Username: [ admin              ]     ║","║                                       ║","║  Password: [ ••••••             ]     ║","║                                       ║","║        [    LOGIN    ]                ║","║                                       ║","╚═══════════════════════════════════════╝"]
for _ in range(192): s(browser("http://localhost:8000/login","Login",login))

# Dashboard (12s)
dash=["┌─────────────────────────────────────┐","│ ATTENDANCE TRACKER    [Admin][Logout]│","├─────────┬───────────────────────────┤","│ Menu    │  Dashboard                │","├─────────┼───────────────────────────┤","│Dashbrd  │  Today: Mon, Aug 10, 2026 │","│People   │  Status: CHECKED IN       │","│Users    │  Check-in: 09:00 AM       │","│Attend.  │  Check-out: --:--         │","│Reports  │  [CHECK OUT]              │","│         │  Weekly: V V V V O        │","│         │  Recent:                  │","│         │  08/10 Present (09:00-)    │","│         │  08/09 Present (08:55-17)  │","└─────────┴───────────────────────────┘"]
for _ in range(288): s(browser("http://localhost:8000/","Dashboard",dash))

# People (10s)
people=["┌─────────────────────────────────────┐","│ ATTENDANCE TRACKER    [Admin][Logout]│","├─────────┬───────────────────────────┤","│ Menu    │  People                   │","├─────────┼───────────────────────────┤","│Dashbrd  │  [+ Add Person]           │","│People   │                           │","│Users    │  Name    Email    Dept    │","│Attend.  │  ----------------------- │","│Reports  │  Aarav   aarav@   IT      │","│         │  Priya   priya@   HR      │","│         │  Rahul   rahul@   Sales   │","│         │  [Edit] [Delete]          │","└─────────┴───────────────────────────┘"]
for _ in range(240): s(browser("http://localhost:8000/people","People",people))

# Attendance (10s)
attend=["┌─────────────────────────────────────┐","│ ATTENDANCE TRACKER    [Admin][Logout]│","├─────────┬───────────────────────────┤","│ Menu    │  Attendance               │","├─────────┼───────────────────────────┤","│Dashbrd  │  Date: 08/01 to 08/10    │","│People   │  Person: [All]           │","│Users    │  Date    Name    In  Out │","│Attend.  │  ----------------------- │","│Reports  │  08/10  Aarav  09:00 --  │","│         │  08/10  Priya  08:55 17  │","│         │  08/09  Aarav  08:55 17  │","│         │  [Export CSV]            │","└─────────┴───────────────────────────┘"]
for _ in range(240): s(browser("http://localhost:8000/attendance","Attendance",attend))

# Ending (3s)
for _ in range(72):
    img=grad((20,80,160),(10,40,80)); d=ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=f(56))[2])//2,250),"Attendance Tracker",fill="white",font=f(56))
    d.text(((W-d.textbbox((0,0),"Thank You!",font=f(36))[2])//2,330),"Thank You!",fill=(180,200,230),font=f(36))
    s(img)

print(f"Generated {fc} frames ({fc/FPS:.1f}s)")

# Compile
print("Encoding video...")
subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(DIR/"f_%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-preset","ultrafast","-crf","28","attendance_tracker_full_showcase.mp4"],check=True)

import shutil; shutil.rmtree(DIR)
print(f"Done! attendance_tracker_full_showcase.mp4 ({fc/FPS:.0f}s)")
