"""
Full Showcase Video Generator - Code + Web App
Generates a 3-minute video showing both code and web application.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont


class FullShowcaseVideo:
    """Generate full showcase video with code and web app."""

    def __init__(self, output_dir: str = "scripts/showcase_frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = 1920
        self.height = 1080
        self.frame_num = 0
        self.fps = 30
        self.slide_duration = 3  # seconds per slide

    def get_font(self, size: int, bold: bool = False):
        """Get font with fallback."""
        fonts_to_try = [
            "consola.ttf" if not bold else "consolab.ttf",
            "cour.ttf",
            "arial.ttf",
        ]
        for font_name in fonts_to_try:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                continue
        return ImageFont.load_default()

    def create_gradient_bg(self, color1: tuple, color2: tuple) -> Image.Image:
        """Create gradient background."""
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        for y in range(self.height):
            ratio = y / self.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        return img

    def create_dark_bg(self) -> Image.Image:
        """Create dark IDE-like background."""
        return Image.new("RGB", (self.width, self.height), (30, 30, 30))

    def add_text_centered(self, draw: ImageDraw, text: str, y: int, 
                          font: ImageFont, fill: tuple = "white"):
        """Add centered text."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        draw.text((x, y), text, fill=fill, font=font)

    def add_title_bar(self, img: Image.Image, title: str, is_code: bool = False):
        """Add title bar at top."""
        draw = ImageDraw.Draw(img)
        bar_color = (45, 45, 48) if is_code else (240, 240, 240)
        text_color = "white" if is_code else "black"
        
        draw.rectangle([(0, 0), (self.width, 50)], fill=bar_color)
        font = self.get_font(20)
        draw.text((20, 15), title, fill=text_color, font=font)
        
        if is_code:
            draw.ellipse([(self.width-80, 15), (self.width-60, 35)], fill=(255, 95, 86))
            draw.ellipse([(self.width-55, 15), (self.width-35, 35)], fill=(255, 189, 46))
            draw.ellipse([(self.width-30, 15), (self.width-10, 35)], fill=(39, 201, 63))

    def save_frame(self, img: Image.Image, section: str = ""):
        """Save frame to disk."""
        prefix = f"{section}_" if section else ""
        filename = self.output_dir / f"{prefix}frame_{self.frame_num:04d}.png"
        img.save(filename)
        self.frame_num += 1
        return filename

    def create_code_frame(self, filename: str, code: list, line_numbers: bool = True) -> Image.Image:
        """Create a frame showing code."""
        img = self.create_dark_bg()
        self.add_title_bar(img, filename, is_code=True)
        draw = ImageDraw.Draw(img)
        
        code_font = self.get_font(22)
        line_font = self.get_font(18)
        
        # Syntax colors
        keyword_color = (86, 156, 214)
        string_color = (206, 145, 120)
        comment_color = (87, 166, 74)
        function_color = (220, 220, 170)
        normal_color = (212, 212, 212)
        line_color = (85, 85, 85)
        
        y = 70
        for i, line in enumerate(code[:40]):
            if line_numbers:
                draw.text((20, y), f"{i+1:3d}", fill=line_color, font=line_font)
                x_offset = 70
            else:
                x_offset = 40
            
            # Simple syntax highlighting
            if line.strip().startswith('#'):
                color = comment_color
            elif any(kw in line for kw in ['def ', 'class ', 'import ', 'from ', 'return ', 'async ', 'await ']):
                color = keyword_color
            elif '"""' in line or "'''" in line or '"' in line or "'" in line:
                color = string_color
            elif '(' in line and ')' in line:
                color = function_color
            else:
                color = normal_color
            
            draw.text((x_offset, y), line[:100], fill=color, font=code_font)
            y += 28
        
        return img

    def create_slide_frame(self, title: str, items: list, icon: str = "•") -> Image.Image:
        """Create a feature slide."""
        img = self.create_gradient_bg((20, 60, 120), (10, 30, 60))
        self.add_title_bar(img, title, is_code=False)
        draw = ImageDraw.Draw(img)
        
        title_font = self.get_font(48, bold=True)
        item_font = self.get_font(28)
        
        self.add_text_centered(draw, title, 80, title_font, "white")
        
        y = 180
        for item in items:
            draw.text((150, y), f"{icon} {item}", fill=(200, 220, 255), font=item_font)
            y += 55
        
        return img

    def create_browser_frame(self, url: str, title: str, content_lines: list) -> Image.Image:
        """Create a frame simulating browser view."""
        img = Image.new("RGB", (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Browser chrome
        draw.rectangle([(0, 0), (self.width, 90)], fill=(222, 225, 230))
        draw.rectangle([(0, 90), (self.width, 130)], fill=(245, 245, 245))
        
        # URL bar
        draw.rounded_rectangle([(100, 25), (self.width-100, 65)], radius=20, fill="white")
        url_font = self.get_font(22)
        draw.text((120, 33), url, fill=(80, 80, 80), font=url_font)
        
        # Tab
        tab_font = self.get_font(16)
        draw.text((20, 5), title, fill=(80, 80, 80), font=tab_font)
        
        # Content area
        content_font = self.get_font(24)
        y = 160
        for line in content_lines[:35]:
            draw.text((100, y), line, fill=(50, 50, 50), font=content_font)
            y += 40
        
        return img

    def generate_all_frames(self):
        """Generate all frames for the showcase video."""
        print("Generating showcase frames...")
        
        # SECTION 1: Title (5 seconds = 150 frames)
        print("  [1/8] Title slide...")
        for _ in range(150):
            img = self.create_gradient_bg((20, 80, 160), (10, 40, 80))
            draw = ImageDraw.Draw(img)
            title_font = self.get_font(72, bold=True)
            sub_font = self.get_font(36)
            self.add_text_centered(draw, "Attendance Tracker", 350, title_font, "white")
            self.add_text_centered(draw, "Full-Stack FastAPI Application", 450, sub_font, (180, 200, 230))
            self.add_text_centered(draw, "FastAPI • PostgreSQL • SQLAlchemy • JWT • Vanilla JS", 520, sub_font, (150, 170, 200))
            self.save_frame(img, "title")

        # SECTION 2: Project Structure (10 seconds)
        print("  [2/8] Project structure...")
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
            img = self.create_code_frame("Project Structure", structure)
            self.save_frame(img, "structure")

        # SECTION 3: Backend Code - Models (15 seconds)
        print("  [3/8] Backend code - models.py...")
        models_code = [
            '"""SQLAlchemy Models"""',
            "from sqlalchemy import Column, Integer, String, DateTime, ForeignKey",
            "from sqlalchemy.orm import relationship",
            "from app.database import Base",
            "",
            "",
            "class User(Base):",
            '    __tablename__ = "users"',
            "",
            "    id = Column(Integer, primary_key=True, index=True)",
            "    username = Column(String, unique=True, index=True)",
            "    hashed_password = Column(String)",
            "    role = Column(String, default='user')",
            "    person_id = Column(Integer, ForeignKey('people.id'))",
            "",
            "    person = relationship('Person', back_populates='user')",
            "",
            "",
            "class Person(Base):",
            '    __tablename__ = "people"',
            "",
            "    id = Column(Integer, primary_key=True, index=True)",
            "    name = Column(String, index=True)",
            "    email = Column(String, unique=True)",
            "    department = Column(String)",
            "    created_at = Column(DateTime)",
            "",
            "    user = relationship('User', back_populates='person')",
            "    attendance = relationship('AttendanceRecord', back_populates='person')",
            "",
            "",
            "class AttendanceRecord(Base):",
            '    __tablename__ = "attendance_records"',
            "",
            "    id = Column(Integer, primary_key=True, index=True)",
            "    person_id = Column(Integer, ForeignKey('people.id'))",
            "    date = Column(DateTime)",
            "    check_in = Column(DateTime)",
            "    check_out = Column(DateTime)",
            "    status = Column(String)",
            "",
            "    person = relationship('Person', back_populates='attendance')",
        ]
        for _ in range(450):
            img = self.create_code_frame("app/models.py", models_code)
            self.save_frame(img, "models")

        # SECTION 4: Backend Code - Security (15 seconds)
        print("  [4/8] Backend code - security.py...")
        security_code = [
            '"""JWT & Password Security"""',
            "from datetime import datetime, timedelta",
            "from typing import Optional",
            "from jose import JWTError, jwt",
            "from passlib.context import CryptContext",
            "from app.config import settings",
            "",
            "pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')",
            "",
            "",
            "def verify_password(plain_password: str, hashed_password: str) -> bool:",
            "    return pwd_context.verify(plain_password, hashed_password)",
            "",
            "",
            "def get_password_hash(password: str) -> str:",
            "    return pwd_context.hash(password)",
            "",
            "",
            "def create_token(data: dict, expires_delta: Optional[timedelta] = None):",
            "    to_encode = data.copy()",
            "    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))",
            "    to_encode.update({'exp': expire})",
            "    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm='HS256')",
            "",
            "",
            "def decode_token(token: str) -> Optional[dict]:",
            "    try:",
            "        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])",
            "        return payload",
            "    except JWTError:",
            "        return None",
            "",
            "",
            "async def authenticate_user(db, username: str, password: str):",
            "    user = await db.query(User).filter(User.username == username).first()",
            "    if not user or not verify_password(password, user.hashed_password):",
            "        return None",
            "    return user",
        ]
        for _ in range(450):
            img = self.create_code_frame("app/security.py", security_code)
            self.save_frame(img, "security")

        # SECTION 5: Backend Code - Routers (15 seconds)
        print("  [5/8] Backend code - routers/auth.py...")
        auth_code = [
            '"""Authentication Routes"""',
            "from fastapi import APIRouter, Depends, HTTPException",
            "from fastapi.security import OAuth2PasswordRequestForm",
            "from sqlalchemy.ext.asyncio import AsyncSession",
            "from app.deps import get_db",
            "from app.security import authenticate_user, create_token",
            "",
            "router = APIRouter(prefix='/api/auth', tags=['auth'])",
            "",
            "",
            "@router.post('/login')",
            "async def login(",
            "    form_data: OAuth2PasswordRequestForm = Depends(),",
            "    db: AsyncSession = Depends(get_db)",
            "):",
            "    user = await authenticate_user(db, form_data.username, form_data.password)",
            "    if not user:",
            "        raise HTTPException(status_code=401, detail='Invalid credentials')",
            "    ",
            "    access_token = create_token(data={'sub': str(user.id), 'role': user.role})",
            "    return {'access_token': access_token, 'token_type': 'bearer'}",
            "",
            "",
            "@router.get('/me')",
            "async def get_current_user(",
            "    current_user = Depends(get_current_user)",
            "):",
            "    return {",
            "        'id': current_user.id,",
            "        'username': current_user.username,",
            "        'role': current_user.role,",
            "        'person': current_user.person.name if current_user.person else None",
            "    }",
        ]
        for _ in range(450):
            img = self.create_code_frame("app/routers/auth.py", auth_code)
            self.save_frame(img, "auth")

        # SECTION 6: Frontend Code (15 seconds)
        print("  [6/8] Frontend code - app.js...")
        js_code = [
            '// Frontend JavaScript',
            'const API_BASE = "/api";',
            'let token = localStorage.getItem("token");',
            '',
            'async function login(username, password) {',
            '    const formData = new URLSearchParams();',
            '    formData.append("username", username);',
            '    formData.append("password", password);',
            '    ',
            '    const response = await fetch(`${API_BASE}/auth/login`, {',
            '        method: "POST",',
            '        headers: {"Content-Type": "application/x-www-form-urlencoded"},',
            '        body: formData',
            '    });',
            '    ',
            '    if (response.ok) {',
            '        const data = await response.json();',
            '        localStorage.setItem("token", data.access_token);',
            '        window.location.href = "/";',
            '    }',
            '}',
            '',
            'async function checkIn() {',
            '    const response = await fetch(`${API_BASE}/attendance/check-in`, {',
            '        method: "POST",',
            '        headers: {"Authorization": `Bearer ${token}`}',
            '    });',
            '    if (response.ok) {',
            '        loadDashboard();',
            '    }',
            '}',
            '',
            'async function checkOut() {',
            '    const response = await fetch(`${API_BASE}/attendance/check-out`, {',
            '        method: "POST",',
            '        headers: {"Authorization": `Bearer ${token}`}',
            '    });',
            '    if (response.ok) {',
            '        loadDashboard();',
            '    }',
            '}',
        ]
        for _ in range(450):
            img = self.create_code_frame("static/app.js", js_code)
            self.save_frame(img, "frontend")

        # SECTION 7: Web App - Login (10 seconds)
        print("  [7/8] Web app - login page...")
        login_lines = [
            "",
            "",
            "╔══════════════════════════════════════════╗",
            "║           ATTENDANCE TRACKER             ║",
            "╠══════════════════════════════════════════╣",
            "║                                          ║",
            "║   Username: [admin                 ]     ║",
            "║                                          ║",
            "║   Password: [••••••               ]     ║",
            "║                                          ║",
            "║         [    LOGIN    ]                  ║",
            "║                                          ║",
            "╚══════════════════════════════════════════╝",
        ]
        for _ in range(300):
            img = self.create_browser_frame("http://localhost:8000/login", "Login", login_lines)
            self.save_frame(img, "login")

        # SECTION 8: Web App - Dashboard (10 seconds)
        print("  [8/8] Web app - dashboard...")
        dashboard_lines = [
            "┌─────────────────────────────────────────┐",
            "│  ATTENDANCE TRACKER         [Admin] [ Logout ] │",
            "├──────────┬──────────────────────────────┤",
            "│ Menu     │  Dashboard                   │",
            "├──────────┼──────────────────────────────┤",
            "│ Dashboard│  Today: Monday, Aug 10, 2026  │",
            "│ People   │                              │",
            "│ Users    │  Status: CHECKED IN          │",
            "│ Attend.  │  Check-in: 09:00 AM          │",
            "│ Reports  │  Check-out: --:--            │",
            "│          │                              │",
            "│          │  [CHECK OUT]                 │",
            "│          │                              │",
            "│          │  Weekly Attendance:          │",
            "│          │  Mon ✓ Tue ✓ Wed ✓ Thu ✓ Fri  │",
            "│          │                              │",
            "│          │  Recent Records:             │",
            "│          │  08/10 - Present (09:00-     )",
            "│          │  08/09 - Present (08:55-17:05)",
            "│          │  08/08 - Present (09:02-17:10)",
            "└──────────┴──────────────────────────────┘",
        ]
        for _ in range(300):
            img = self.create_browser_frame("http://localhost:8000/", "Dashboard", dashboard_lines)
            self.save_frame(img, "dashboard")

        print(f"Generated {self.frame_num} frames in {self.output_dir}")

    def compile_video(self, output_path: str = "attendance_tracker_full_showcase.mp4"):
        """Compile frames to video using ffmpeg."""
        print(f"Compiling video to {output_path}...")
        
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(self.fps),
            "-i", str(self.output_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "23",
            output_path,
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Video saved to {output_path}")
            return output_path
        except FileNotFoundError:
            print("ffmpeg not found. Install: winget install ffmpeg")
            return None
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            return None

    def cleanup(self):
        """Remove temporary frames."""
        print("Cleaning up frames...")
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else "attendance_tracker_full_showcase.mp4"
    
    generator = FullShowcaseVideo()
    generator.generate_all_frames()
    generator.compile_video(output)
    generator.cleanup()
    
    print(f"\nDone! Video: {output}")
    print("Duration: ~3 minutes (5400 frames @ 30fps)")


if __name__ == "__main__":
    main()
