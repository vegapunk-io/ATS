"""
Full Project Showcase - All Files
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

def code_frame(title, lines):
    img = Image.new("RGB",(W,H),(30,30,30)); d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,40)], fill=(45,45,48))
    d.text((15,10), title, fill="white", font=f(16))
    d.ellipse([(W-60,10),(W-48,22)], fill=(255,95,86))
    d.ellipse([(W-44,10),(W-32,22)], fill=(255,189,46))
    d.ellipse([(W-28,10),(W-16,22)], fill=(39,201,63))
    fn = f(14); y=50
    for i,l in enumerate(lines[:38]):
        c=(86,156,214) if any(k in l for k in['def','class','import','from','return','async','await','@router','@app']) else (206,145,120) if '"""' in l or "'''" in l else (87,166,74) if l.strip().startswith('#') or l.strip().startswith('//') else (212,212,212)
        d.text((10,y), f"{i+1:2d}", fill=(85,85,85), font=f(10))
        d.text((38,y), l[:110], fill=c, font=fn); y+=19
    return img

def browser_frame(url, title, lines):
    img = Image.new("RGB",(W,H),(255,255,255)); d = ImageDraw.Draw(img)
    d.rectangle([(0,0),(W,70)], fill=(222,225,230))
    d.rounded_rectangle([(80,15),(W-80,50)], radius=15, fill="white")
    d.text((95,22), url, fill=(80,80,80), font=f(14))
    d.text((10,3), title, fill=(80,80,80), font=f(11))
    y=85
    for l in lines[:32]:
        d.text((40,y), l, fill=(50,50,50), font=f(16)); y+=28
    return img

print("Generating complete project showcase...")

# Title (4s)
for _ in range(96):
    img=grad((20,80,160),(10,40,80)); d=ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=f(56))[2])//2,220),"Attendance Tracker",fill="white",font=f(56))
    d.text(((W-d.textbbox((0,0),"Full-Stack FastAPI + PostgreSQL + JS",font=f(24))[2])//2,300),"Full-Stack FastAPI + PostgreSQL + JS",fill=(180,200,230),font=f(24))
    d.text(((W-d.textbbox((0,0),"Complete Project Showcase",font=f(20))[2])//2,360),"Complete Project Showcase",fill=(150,170,200),font=f(20))
    s(img)

# Structure (8s)
struct=["attendance-tracker/","  app/","    __init__.py","    main.py           # FastAPI entry point","    config.py         # Settings from .env","    database.py       # Async SQLAlchemy","    models.py         # User, Person, AttendanceRecord","    schemas.py        # Pydantic validation","    security.py       # JWT + bcrypt","    deps.py           # Auth dependencies","    routers/","      __init__.py","      auth.py         # POST /login, GET /me","      users.py        # CRUD users (admin)","      people.py       # CRUD people (admin)","      attendance.py   # Check-in/out, records","      reports.py      # Summary + CSV export","    static/","      index.html      # Main SPA","      login.html      # Login page","      app.js          # Frontend logic (858 lines)","      styles.css      # CSS styling","  scripts/","    seed.py           # Database seeding","  requirements.txt","  .env.example","  README.md"]
for _ in range(192): s(code_frame("Project Structure", struct))

# config.py (8s)
config=['"""Application settings from .env"""',"from functools import lru_cache","from pydantic_settings import BaseSettings, SettingsConfigDict","","class Settings(BaseSettings):","    model_config = SettingsConfigDict(env_file='.env')","","    # Database","    database_url: str = 'postgresql+asyncpg://...'",'    # Security',"    secret_key: str = 'change-me-in-production'","    jwt_algorithm: str = 'HS256'","    access_token_expire_minutes: int = 720","","    # App","    app_name: str = 'Attendance Tracker'","    app_timezone: str = 'Asia/Kolkata'","    allow_self_check: bool = True","","settings = Settings()"]
for _ in range(192): s(code_frame("app/config.py", config))

# database.py (8s)
db=['"""Async SQLAlchemy engine + session"""',"from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine","from sqlalchemy.orm import DeclarativeBase","from app.config import settings","","engine = create_async_engine(settings.database_url, echo=False)","SessionLocal = async_sessionmaker(engine, class_=AsyncSession)","","class Base(DeclarativeBase): pass","","async def get_db():","    async with SessionLocal() as session:","        yield session"]
for _ in range(192): s(code_frame("app/database.py", db))

# models.py (12s)
models=['"""SQLAlchemy ORM Models"""',"from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean, Text","from sqlalchemy.orm import Mapped, mapped_column, relationship","from app.database import Base","","class User(Base):",'    __tablename__ = "users',"    id: Mapped[int] = mapped_column(primary_key=True)","    username: Mapped[str] = mapped_column(String(64), unique=True)","    email: Mapped[str] = mapped_column(String(255), unique=True)","    full_name: Mapped[str] = mapped_column(String(255))","    hashed_password: Mapped[str] = mapped_column(String(255))","    role: Mapped[str] = mapped_column(String(16), default='user')","    is_active: Mapped[bool] = mapped_column(Boolean, default=True)","    person_id: Mapped[int] = mapped_column(ForeignKey('people.id'))","    person = relationship('Person', back_populates='user')","","class Person(Base):",'    __tablename__ = "people',"    id: Mapped[int] = mapped_column(primary_key=True)","    full_name: Mapped[str] = mapped_column(String(255))","    email: Mapped[str] = mapped_column(String(255))","    group_name: Mapped[str] = mapped_column(String(128))","    is_active: Mapped[bool] = mapped_column(Boolean, default=True)","    user = relationship('User', back_populates='person')","    records = relationship('AttendanceRecord', back_populates='person')","","class AttendanceRecord(Base):",'    __tablename__ = "attendance_records',"    id: Mapped[int] = mapped_column(primary_key=True)","    person_id: Mapped[int] = mapped_column(ForeignKey('people.id'))","    date = mapped_column(Date)","    check_in = mapped_column(DateTime)","    check_out = mapped_column(DateTime)","    status = mapped_column(String(16), default='present')","    note = mapped_column(Text)","    person = relationship('Person', back_populates='records')"]
for _ in range(288): s(code_frame("app/models.py", models))

# schemas.py (10s)
schemas=['"""Pydantic Schemas"""',"from pydantic import BaseModel, Field","","class Token(BaseModel):","    access_token: str","    token_type: str = 'bearer'","","class UserCreate(BaseModel):","    username: str = Field(min_length=3)","    password: str = Field(min_length=6)","    full_name: str","    role: str = 'user'","    person_id: int | None = None","","class PersonCreate(BaseModel):","    full_name: str","    email: str | None = None","    group_name: str | None = None","","class AttendanceCreate(BaseModel):","    person_id: int","    date: str","    check_in: str | None = None","    check_out: str | None = None","    status: str = 'present'","","class PersonSummary(BaseModel):","    person_id: int","    person_name: str","    total_days: int","    present_days: int","    absent_days: int","    attendance_rate: float"]
for _ in range(240): s(code_frame("app/schemas.py", schemas))

# security.py (10s)
security=['"""JWT + Password Security"""',"from datetime import datetime, timedelta, timezone","import jwt","from passlib.context import CryptContext","from app.config import settings","","pwd_context = CryptContext(schemes=['bcrypt'])","","def hash_password(password):","    return pwd_context.hash(password)","","def verify_password(plain, hashed):","    return pwd_context.verify(plain, hashed)","","def create_access_token(subject, role):","    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)","    payload = {'sub': str(subject), 'role': role, 'exp': expire}","    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)","","def decode_access_token(token):","    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])"]
for _ in range(240): s(code_frame("app/security.py", security))

# deps.py (10s)
deps=['"""FastAPI Dependencies"""',"from fastapi import Depends, HTTPException, status","from fastapi.security import OAuth2PasswordBearer","from sqlalchemy import select","from app.database import get_db","from app.models import User","from app.security import decode_access_token","","oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')","","async def get_current_user(token = Depends(oauth2_scheme), db = Depends(get_db)):","    try:","        payload = decode_access_token(token)","        user_id = int(payload.get('sub'))","    except: raise HTTPException(status_code=401)","    result = await db.execute(select(User).where(User.id == user_id))","    user = result.scalar_one_or_none()","    if not user or not user.is_active: raise HTTPException(status_code=401)","    return user","","async def require_admin(user = Depends(get_current_user)):","    if user.role != 'admin': raise HTTPException(status_code=403)","    return user"]
for _ in range(240): s(code_frame("app/deps.py", deps))

# auth.py (10s)
auth=['"""Authentication Routes"""',"from fastapi import APIRouter, Depends, HTTPException","from fastapi.security import OAuth2PasswordRequestForm","from sqlalchemy import select","from app.database import get_db","from app.models import User","from app.schemas import Token, UserOut","from app.security import create_access_token, verify_password","from app.deps import get_current_user","","router = APIRouter(prefix='/api/auth', tags=['auth'])","","@router.post('/login', response_model=Token)","async def login(form: OAuth2PasswordRequestForm = Depends(), db = Depends(get_db)):","    result = await db.execute(select(User).where(User.username == form.username))","    user = result.scalar_one_or_none()","    if not user or not verify_password(form.password, user.hashed_password):","        raise HTTPException(status_code=401, detail='Invalid credentials')","    token = create_access_token(subject=user.id, role=user.role)","    return Token(access_token=token)","","@router.get('/me', response_model=UserOut)","async def me(user: User = Depends(get_current_user)):","    return user"]
for _ in range(240): s(code_frame("app/routers/auth.py", auth))

# users.py (10s)
users=['"""User Management (Admin)"""',"from fastapi import APIRouter, Depends, HTTPException","from sqlalchemy import select","from app.database import get_db","from app.models import User","from app.schemas import UserCreate, UserOut, UserUpdate","from app.security import hash_password","from app.deps import require_admin","","router = APIRouter(prefix='/api/users', tags=['users'])","","@router.get('', response_model=list[UserOut])","async def list_users(db = Depends(get_db), _ = Depends(require_admin)):","    result = await db.execute(select(User).order_by(User.username))","    return list(result.scalars().all())","","@router.post('', response_model=UserOut, status_code=201)","async def create_user(data: UserCreate, db = Depends(get_db), _ = Depends(require_admin)):","    user = User(username=data.username, email=data.email, full_name=data.full_name,","                hashed_password=hash_password(data.password), role=data.role)","    db.add(user)","    await db.commit()","    await db.refresh(user)","    return user","","@router.patch('/{user_id}', response_model=UserOut)","async def update_user(user_id: int, data: UserUpdate, db = Depends(get_db), _ = Depends(require_admin)):","    user = await db.get(User, user_id)","    if not user: raise HTTPException(status_code=404)","    for k, v in data.model_dump(exclude_unset=True).items():","        setattr(user, k, v)","    await db.commit()","    return user"]
for _ in range(240): s(code_frame("app/routers/users.py", users))

# people.py (10s)
people=['"""People Management (Admin)"""',"from fastapi import APIRouter, Depends, HTTPException","from sqlalchemy import select","from app.database import get_db","from app.models import Person","from app.schemas import PersonCreate, PersonOut, PersonUpdate","from app.deps import require_admin","","router = APIRouter(prefix='/api/people', tags=['people'])","","@router.get('', response_model=list[PersonOut])","async def list_people(search: str = None, group: str = None, db = Depends(get_db), _ = Depends(require_admin)):","    query = select(Person).order_by(Person.full_name)","    if search: query = query.where(Person.full_name.ilike(f'%{search}%'))","    if group: query = query.where(Person.group_name == group)","    result = await db.execute(query)","    return list(result.scalars().all())","","@router.post('', response_model=PersonOut, status_code=201)","async def create_person(data: PersonCreate, db = Depends(get_db), _ = Depends(require_admin)):","    person = Person(**data.model_dump())","    db.add(person)","    await db.commit()","    return person","","@router.delete('/{person_id}', status_code=204)","async def delete_person(person_id: int, db = Depends(get_db), _ = Depends(require_admin)):","    person = await db.get(Person, person_id)","    if not person: raise HTTPException(status_code=404)","    await db.delete(person)","    await db.commit()"]
for _ in range(240): s(code_frame("app/routers/people.py", people))

# attendance.py (12s)
attend=['"""Attendance Endpoints"""',"from datetime import datetime","from fastapi import APIRouter, Depends, HTTPException","from sqlalchemy import select","from app.database import get_db","from app.models import AttendanceRecord, Person, User","from app.deps import get_current_user, today_local, get_app_tz","","router = APIRouter(prefix='/api/attendance', tags=['attendance'])","","@router.get('/today')","async def today_record(db = Depends(get_db), user = Depends(get_current_user)):","    if not user.person_id: return None","    result = await db.execute(select(AttendanceRecord).where(","        AttendanceRecord.person_id == user.person_id,","        AttendanceRecord.date == today_local()))","    return result.scalar_one_or_none()","","@router.post('/check-in')","async def check_in(db = Depends(get_db), user = Depends(get_current_user)):","    today = today_local()","    now = datetime.now(get_app_tz())","    record = AttendanceRecord(person_id=user.person_id, date=today, check_in=now, status='present')","    db.add(record)","    await db.commit()","    return record","","@router.post('/check-out')","async def check_out(db = Depends(get_db), user = Depends(get_current_user)):","    result = await db.execute(select(AttendanceRecord).where(","        AttendanceRecord.person_id == user.person_id,","        AttendanceRecord.date == today_local()))","    record = result.scalar_one_or_none()","    if not record: raise HTTPException(status_code=409, detail='No record today')","    record.check_out = datetime.now(get_app_tz())","    await db.commit()","    return record"]
for _ in range(288): s(code_frame("app/routers/attendance.py", attend))

# reports.py (10s)
reports=['"""Reports & CSV Export"""',"import csv, io","from datetime import date","from fastapi import APIRouter, Depends","from fastapi.responses import StreamingResponse","from sqlalchemy import select","from app.database import get_db","from app.models import AttendanceRecord, Person","from app.deps import get_current_user, require_admin","","router = APIRouter(prefix='/api/reports', tags=['reports'])","","@router.get('/summary')","async def summary(date_from: date, date_to: date, db = Depends(get_db), user = Depends(get_current_user)):","    query = select(AttendanceRecord).where(","        AttendanceRecord.date >= date_from,","        AttendanceRecord.date <= date_to)","    records = list((await db.execute(query)).scalars().all())","    # Calculate per-person stats...","    return {'date_from': date_from, 'date_to': date_to, 'people': []}","","@router.get('/export')","async def export_csv(date_from: date, date_to: date, db = Depends(get_db), _ = Depends(require_admin)):","    query = select(AttendanceRecord).where(","        AttendanceRecord.date >= date_from,","        AttendanceRecord.date <= date_to)","    records = list((await db.execute(query)).scalars().all())","    buf = io.StringIO()","    writer = csv.writer(buf)","    writer.writerow(['date', 'person', 'status', 'check_in', 'check_out'])","    for r in records:","        writer.writerow([r.date, r.person_id, r.status, r.check_in, r.check_out])","    buf.seek(0)","    return StreamingResponse(iter([buf.getvalue()]), media_type='text/csv')"]
for _ in range(240): s(code_frame("app/routers/reports.py", reports))

# main.py (10s)
main=['"""FastAPI Application Entry"""',"from pathlib import Path","from fastapi import FastAPI","from fastapi.staticfiles import StaticFiles","from fastapi.responses import FileResponse","from app.config import settings","from app.database import Base, engine","from app.routers import auth, users, people, attendance, reports","","STATIC_DIR = Path(__file__).parent / 'static'","app = FastAPI(title=settings.app_name, version='1.0.0')","","app.include_router(auth.router)","app.include_router(users.router)","app.include_router(people.router)","app.include_router(attendance.router)","app.include_router(reports.router)","app.mount('/static', StaticFiles(directory=STATIC_DIR))","","@app.get('/')","async def index(): return FileResponse(STATIC_DIR / 'index.html')","","@app.get('/login')","async def login_page(): return FileResponse(STATIC_DIR / 'login.html')","","@app.get('/health')","async def health(): return {'status': 'ok'}"]
for _ in range(240): s(code_frame("app/main.py", main))

# seed.py (10s)
seed=['"""Database Seeding"""',"import asyncio","from datetime import date, datetime, timedelta","from app.database import Base, SessionLocal, engine","from app.models import User, Person, AttendanceRecord","from app.security import hash_password","","SAMPLE_PEOPLE = [","    {'full_name': 'Aarav Shah', 'email': 'aarav@example.com', 'group_name': 'Engineering'},","    {'full_name': 'Priya Nair', 'email': 'priya@example.com', 'group_name': 'Engineering'},","    {'full_name': 'Rohan Mehta', 'email': 'rohan@example.com', 'group_name': 'Design'},","]","","async def main():","    async with engine.begin() as conn:","        await conn.run_sync(Base.metadata.create_all)","    async with SessionLocal() as db:","        db.add(User(username='admin', full_name='Admin',","                    hashed_password=hash_password('admin123'), role='admin'))","        for p in SAMPLE_PEOPLE:","            db.add(Person(**p))","        await db.commit()","","asyncio.run(main())"]
for _ in range(240): s(code_frame("scripts/seed.py", seed))

# Frontend: app.js (15s)
js=['/* Attendance Tracker - Frontend */',"const state = { me: null, people: [], users: [] };","const API = '/api';","","async function api(path, opts = {}) {","    const token = localStorage.getItem('token');","    const headers = { Authorization: 'Bearer ' + token, ...opts.headers };","    const res = await fetch(path, { ...opts, headers });","    if (res.status === 401) { localStorage.removeItem('token'); location.href = '/login'; }","    return res.json();","}","","async function init() {","    if (!localStorage.getItem('token')) { location.href = '/login'; return; }","    state.me = await api('/api/auth/me');","    loadDashboard();","}","","async function loadDashboard() {","    const today = await api('/api/attendance/today');","    renderHero(today);","}","","async function checkIn() {","    const rec = await api('/api/attendance/check-in', { method: 'POST' });","    renderHero(rec);","}","","async function checkOut() {","    const rec = await api('/api/attendance/check-out', { method: 'POST' });","    renderHero(rec);","}","","async function loadPeople() {","    state.people = await api('/api/people');","    renderPeopleTable();","}","","async function loadUsers() {","    state.users = await api('/api/users');","    renderUsersTable();","}","","async function loadReports() {","    const data = await api('/api/reports/summary?date_from=2026-08-01&date_to=2026-08-10');","    renderReport(data);","}"]
for _ in range(360): s(code_frame("static/app.js", js))

# Frontend: index.html (10s)
html=['<!DOCTYPE html>','<html lang="en">','<head>','  <meta charset="UTF-8">','  <title>Attendance Tracker</title>','  <link rel="stylesheet" href="/static/styles.css">','</head>','<body>','  <div class="app">','    <aside class="sidebar">','      <div class="sidebar-brand">','        <div class="logo">V</div>','        <span>Attendance Tracker</span>','      </div>','      <nav>','        <button data-view="home">Dashboard</button>','        <button data-view="records">Attendance</button>','        <button data-view="people">People</button>','        <button data-view="users">Users</button>','        <button data-view="reports">Reports</button>','      </nav>','    </aside>','    <main>','      <section id="view-home">','        <h2>Dashboard</h2>','        <div class="hero">','          <div>Today: <span id="hero-date"></span></div>','          <button onclick="checkIn()">Check In</button>','          <button onclick="checkOut()">Check Out</button>','        </div>','      </section>','    </main>','  </div>','  <script src="/static/app.js"></script>','</body>','</html>']
for _ in range(240): s(code_frame("static/index.html", html))

# Frontend: login.html (8s)
login_html=['<!DOCTYPE html>','<html lang="en">','<head>','  <title>Sign in</title>','  <link rel="stylesheet" href="/static/styles.css">','</head>','<body>','  <div class="login-wrap">','    <div class="login-card">','      <div class="login-logo">V</div>','      <h1>Attendance Tracker</h1>','      <form id="login-form">','        <input name="username" placeholder="Username" required>','        <input name="password" type="password" placeholder="Password" required>','        <button type="submit">Sign in</button>','      </form>','    </div>','  </div>','  <script>','    document.getElementById("login-form").addEventListener("submit", async (e) => {','      e.preventDefault();','      const body = new URLSearchParams({','        username: document.getElementById("username").value,','        password: document.getElementById("password").value','      });','      const res = await fetch("/api/auth/login", {','        method: "POST",','        headers: {"Content-Type": "application/x-www-form-urlencoded"},','        body: body','      });','      if (res.ok) {','        const data = await res.json();','        localStorage.setItem("token", data.access_token);','        window.location.href = "/";','      }','    });','  </script>','</body>','</html>']
for _ in range(192): s(code_frame("static/login.html", login_html))

# Frontend: styles.css (10s)
css=['/* CSS Variables */',':root {','  --bg: #f1f5f9;','  --surface: #ffffff;','  --primary: #4f46e5;','  --success: #059669;','  --danger: #dc2626;','  --text: #0f172a;','  --muted: #64748b;','  --radius: 12px;','}','','/* Login Page */','.login-wrap {','  min-height: 100vh;','  display: flex;','  align-items: center;','  justify-content: center;','  background: linear-gradient(135deg, #4f46e5, #9333ea);','}','.login-card {','  background: var(--surface);','  border-radius: 16px;','  padding: 36px;','  max-width: 400px;','}','','/* Sidebar */','.sidebar {','  width: 230px;','  background: #0f172a;','  color: #cbd5e1;','  height: 100vh;','  position: sticky;','  top: 0;','}','','/* Hero Section */','.hero {','  background: linear-gradient(135deg, #4f46e5, #7c3aed);','  border-radius: 16px;','  color: #fff;','  padding: 28px;','}','','/* Tables */','table { width: 100%; border-collapse: collapse; }','th { text-align: left; padding: 10px; }','td { padding: 10px; border-bottom: 1px solid #e2e8f0; }','','/* Badges */','.badge { padding: 3px 10px; border-radius: 999px; font-size: 11px; }','.badge.present { background: #d1fae5; color: #059669; }','.badge.absent { background: #fee2e2; color: #dc2626; }']
for _ in range(240): s(code_frame("static/styles.css", css))

# Web: Login (8s)
login_page=["","  +----------------------------------+","  |     V  Attendance Tracker        |","  |     Sign in to your account      |","  |                                  |","  |  Username: [ admin          ]    |","  |                                  |","  |  Password: [ ********       ]    |","  |                                  |","  |       [    Sign in    ]          |","  |                                  |","  +----------------------------------+"]
for _ in range(192): s(browser_frame("http://localhost:8000/login", "Login", login_page))

# Web: Dashboard (12s)
dashboard=["+---------------------------------------------------+","|  V Attendance Tracker              [Admin] [Logout]|","+-----------+---------------------------------------+","|           |  Dashboard                            |","| Dashboard |  Friday, August 10, 2026              |","|           |                                       |","| Attendance|  +---------------------------------+ |","| People    |  | CHECKED IN                      | |","| Users     |  | Check-in: 09:00 AM              | |","| Reports   |  | Check-out: --:--                | |","|           |  | Duration: --                    | |","|           |  | [CHECK IN] [CHECK OUT]          | |","|           |  +---------------------------------+ |","|           |                                       |","|           |  Last 7 days:                         |","|           |  Mon V  Tue V  Wed V  Thu V  Fri O   |","|           |                                       |","|           |  My recent attendance:                |","|           |  08/10  09:00  --:--  Present         |","|           |  08/09  08:55  17:05  Present         |","|           |  08/08  09:02  17:10  Present         |","+-----------+---------------------------------------+"]
for _ in range(288): s(browser_frame("http://localhost:8000/", "Dashboard", dashboard))

# Web: People (10s)
people_page=["+---------------------------------------------------+","|  V Attendance Tracker              [Admin] [Logout]|","+-----------+---------------------------------------+","|           |  People                                |","| Dashboard |  [+ Add person]                       |","|           |                                       |","| Attendance|  Name        Email        Group       |","| People    |  ---------------------------------  |","| Users     |  Aarav Shah  aarav@ex     Engineering |","| Reports   |  Priya Nair  priya@ex     Engineering |","|           |  Rohan Mehta rohan@ex     Design      |","|           |  Sara Khan   sara@ex      Design      |","|           |  Vikram Iyer vikram@ex    Marketing   |","|           |  Ananya Das  ananya@ex    Marketing   |","|           |                                       |","|           |  [Edit] [Del]  [Edit] [Del]           |","+-----------+---------------------------------------+"]
for _ in range(240): s(browser_frame("http://localhost:8000/people", "People", people_page))

# Web: Users (10s)
users_page=["+---------------------------------------------------+","|  V Attendance Tracker              [Admin] [Logout]|","+-----------+---------------------------------------+","|           |  User Accounts                         |","| Dashboard |  [+ Add user]                         |","|           |                                       |","| Attendance|  Username  Name        Role   Status  |","| People    |  ---------------------------------  |","| Users     |  admin     Admin       admin  Active  |","| Reports   |  aarav     Aarav Shah  user   Active  |","|           |                                       |","|           |  [Edit] [Del]  [Edit] [Del]           |","+-----------+---------------------------------------+"]
for _ in range(240): s(browser_frame("http://localhost:8000/users", "Users", users_page))

# Web: Attendance Records (10s)
records=["+---------------------------------------------------+","|  V Attendance Tracker              [Admin] [Logout]|","+-----------+---------------------------------------+","|           |  Attendance Records                    |","| Dashboard |  From: [08/01]  To: [08/10]           |","|           |  Person: [All]  Status: [All]         |","| Attendance|  [Apply]                              |","| People    |                                       |","| Users     |  Date     Person    In     Out   Status|","| Reports   |  ---------------------------------  |","|           |  08/10   Aarav    09:00  --    Present|","|           |  08/10   Priya    08:55  17:02 Present|","|           |  08/09   Aarav    08:55  17:05 Present|","|           |  08/09   Rohan    09:10  18:00 Present|","|           |  08/08   Sara     09:00  17:30 Present|","|           |  [Edit] [Del]                         |","+-----------+---------------------------------------+"]
for _ in range(240): s(browser_frame("http://localhost:8000/attendance", "Records", records))

# Web: Reports (10s)
reports_page=["+---------------------------------------------------+","|  V Attendance Tracker              [Admin] [Logout]|","+-----------+---------------------------------------+","|           |  Reports                               |","| Dashboard |  From: [08/01]  To: [08/10]           |","|           |  Group: [All]  [Run report]           |","| Attendance|  [Export CSV]                         |","| People    |                                       |","| Users     |  Stats: 6 People | 10 Days | 48 Present|","| Reports   |                                       |","|           |  Name       Group    Present Absent Rate|","|           |  ---------------------------------  |","|           |  Aarav      Eng      8       0    80%|","|           |  Priya      Eng      7       1    70%|","|           |  Rohan      Design   9       0    90%|","|           |  Sara       Design   6       2    60%|","+-----------+---------------------------------------+"]
for _ in range(240): s(browser_frame("http://localhost:8000/reports", "Reports", reports_page))

# Ending (4s)
for _ in range(96):
    img=grad((20,80,160),(10,40,80)); d=ImageDraw.Draw(img)
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=f(56))[2])//2,200),"Attendance Tracker",fill="white",font=f(56))
    d.text(((W-d.textbbox((0,0),"FastAPI | PostgreSQL | SQLAlchemy | JWT | Vanilla JS",font=f(18))[2])//2,280),"FastAPI | PostgreSQL | SQLAlchemy | JWT | Vanilla JS",fill=(180,200,230),font=f(18))
    d.text(((W-d.textbbox((0,0),"Thank You!",font=f(36))[2])//2,350),"Thank You!",fill=(200,220,255),font=f(36))
    s(img)

print(f"Generated {fc} frames ({fc/FPS:.1f}s at {FPS}fps)")

print("Encoding video...")
subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(DIR/"f_%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-preset","ultrafast","-crf","28","attendance_tracker_full_showcase.mp4"],check=True)

import shutil; shutil.rmtree(DIR)
print(f"Done! attendance_tracker_full_showcase.mp4")
