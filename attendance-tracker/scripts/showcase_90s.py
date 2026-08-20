"""
1:30 Showcase Video Generator
Generates a 90-second video showing key features.
"""
import os
import subprocess
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
DIR = Path("scripts/frames_90s")
DIR.mkdir(parents=True, exist_ok=True)
fc = 0


def get_font(sz):
    for n in ["consola.ttf", "cour.ttf", "arial.ttf"]:
        try:
            return ImageFont.truetype(n, sz)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def save(img):
    global fc
    img.save(DIR / f"f_{fc:04d}.png")
    fc += 1


def gradient(c1, c2):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y / H
        color = tuple(int(c1[i] * (1 - r) + c2[i] * r) for i in range(3))
        d.line([(0, y), (W, y)], fill=color)
    return img


def code_frame(title, lines):
    img = Image.new("RGB", (W, H), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (W, 40)], fill=(45, 45, 48))
    d.text((15, 10), title, fill="white", font=get_font(16))
    d.ellipse([(W - 60, 10), (W - 48, 22)], fill=(255, 95, 86))
    d.ellipse([(W - 44, 10), (W - 32, 22)], fill=(255, 189, 46))
    d.ellipse([(W - 28, 10), (W - 16, 22)], fill=(39, 201, 63))
    fn = get_font(14)
    y = 50
    for i, l in enumerate(lines[:38]):
        if any(k in l for k in ["def", "class", "import", "from", "return", "async", "await", "@router", "@app"]):
            c = (86, 156, 214)
        elif '"""' in l or "'''" in l:
            c = (206, 145, 120)
        elif l.strip().startswith("#"):
            c = (87, 166, 74)
        else:
            c = (212, 212, 212)
        d.text((10, y), f"{i + 1:2d}", fill=(85, 85, 85), font=get_font(10))
        d.text((38, y), l[:110], fill=c, font=fn)
        y += 19
    return img


def browser_frame(url, title, lines):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (W, 70)], fill=(222, 225, 230))
    d.rounded_rectangle([(80, 15), (W - 80, 50)], radius=15, fill="white")
    d.text((95, 22), url, fill=(80, 80, 80), font=get_font(14))
    d.text((10, 3), title, fill=(80, 80, 80), font=get_font(11))
    y = 85
    for l in lines[:32]:
        d.text((40, y), l, fill=(50, 50, 50), font=get_font(16))
        y += 28
    return img


def slide_frame(title, subtitle, items):
    img = gradient((20, 80, 160), (10, 40, 80))
    d = ImageDraw.Draw(img)
    d.text(((W - d.textbbox((0, 0), title, font=get_font(48))[2]) // 2, 100), title, fill="white", font=get_font(48))
    d.text(((W - d.textbbox((0, 0), subtitle, font=get_font(20))[2]) // 2, 170), subtitle, fill=(180, 200, 230), font=get_font(20))
    y = 250
    for item in items:
        d.text((200, y), f"• {item}", fill=(200, 220, 255), font=get_font(22))
        y += 50
    return img


print("Generating 90-second showcase...")

# Scene 1: Title (3s = 72 frames)
for _ in range(72):
    img = gradient((20, 80, 160), (10, 40, 80))
    d = ImageDraw.Draw(img)
    d.text(((W - d.textbbox((0, 0), "Attendance Tracker", font=get_font(56))[2]) // 2, 250), "Attendance Tracker", fill="white", font=get_font(56))
    d.text(((W - d.textbbox((0, 0), "HR Management System", font=get_font(24))[2]) // 2, 330), "HR Management System", fill=(180, 200, 230), font=get_font(24))
    save(img)

# Scene 2: Login (5s = 120 frames)
login = [
    "╔══════════════════════════════════════╗",
    "║        ATTENDANCE TRACKER            ║",
    "╠══════════════════════════════════════╣",
    "║                                      ║",
    "║  Username: [ admin            ]      ║",
    "║                                      ║",
    "║  Password: [ ********         ]      ║",
    "║                                      ║",
    "║        [    SIGN IN    ]             ║",
    "║                                      ║",
    "╚══════════════════════════════════════╝",
]
for _ in range(120):
    save(browser_frame("http://localhost:8000/login", "Login", login))

# Scene 3: Dashboard (8s = 192 frames)
dashboard = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Dashboard                             |",
    "|  Dashboard |  Tuesday, August 19, 2026              |",
    "|            |                                        |",
    "|  Leaves    |  +----------------------------------+ |",
    "|  Tasks     |  | CHECKED IN                       | |",
    "|  Chat      |  | Check-in: 09:00 AM               | |",
    "|  Reports   |  | Check-out: --:--                 | |",
    "|  Salary    |  | Duration: --                     | |",
    "|            |  +----------------------------------+ |",
    "|            |                                        |",
    "|            |  This Week:                            |",
    "|            |  Mon✓ Tue✓ Wed-- Thu-- Fri--          |",
    "|            |                                        |",
    "|            |  My Recent:                            |",
    "|            |  08/19  09:00  --     Present          |",
    "|            |  08/18  08:55  17:05  Present          |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/", "Dashboard", dashboard))

# Scene 4: Leaves (8s = 192 frames)
leaves = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Leave Requests                        |",
    "|  Dashboard |  [+ Apply Leave]                       |",
    "|            |                                        |",
    "|  Leaves    |  Person     Type    From      To       |",
    "|  Tasks     |  ----------------------------------   |",
    "|  Chat      |  Aarav      Sick    08/15    08/16    |",
    "|  Reports   |  Priya      Casual  08/20    08/22    |",
    "|  Salary    |  Rohan      Annual  09/01    09/05    |",
    "|            |                                        |",
    "|            |  Status: Approved  Rejected  Pending   |",
    "|            |  [Approve] [Reject]                    |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/leaves", "Leaves", leaves))

# Scene 5: Tasks (8s = 192 frames)
tasks = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Tasks                                 |",
    "|  Dashboard |  [+ New Task]                          |",
    "|            |                                        |",
    "|  Leaves    |  Title        Assignee   Priority  Status",
    "|  Tasks     |  ----------------------------------   |",
    "|  Chat      |  Fix login    Aarav      High     Done |",
    "|  Reports   |  API docs     Priya      Normal   Todo |",
    "|  Salary    |  UI redesign  Rohan      Urgent   Progress",
    "|            |                                        |",
    "|            |  [Start] [Done] [Delete]               |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/tasks", "Tasks", tasks))

# Scene 6: Chat (8s = 192 frames)
chat = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Chat — #general                       |",
    "|  Dashboard |                                        |",
    "|            |  Priya: Hello team!                    |",
    "|  Leaves    |  Aarav: Hey Priya!                    |",
    "|  Tasks     |  Rohan: Working on the API            |",
    "|  Chat      |  Admin: Great progress!               |",
    "|  Reports   |                                        |",
    "|  Salary    |  +----------------------------------+ |",
    "|            |  | Type a message...          [Send]| |",
    "|            |  +----------------------------------+ |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/chat", "Chat", chat))

# Scene 7: Salary (8s = 192 frames)
salary = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Salary — August 2026                  |",
    "|  Dashboard |  [+ Generate Salary]                   |",
    "|            |                                        |",
    "|  Leaves    |  Person    Base    Present  Net Salary |",
    "|  Tasks     |  ----------------------------------   |",
    "|  Chat      |  Aarav     50000   22/24    45833     |",
    "|  Reports   |  Priya     55000   20/24    45833     |",
    "|  Salary    |  Rohan     48000   23/24    46000     |",
    "|            |                                        |",
    "|            |  Total Payroll: 137,666                |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/salary", "Salary", salary))

# Scene 8: Reports (8s = 192 frames)
reports = [
    "+----------------------------------------------------+",
    "|  ATTENDANCE TRACKER                  [Admin] [Logout]",
    "+------------+----------------------------------------+",
    "|            |  Reports                               |",
    "|  Dashboard |  From: [08/01]  To: [08/31]           |",
    "|            |  [Run Report]  [Export CSV]            |",
    "|  Leaves    |                                        |",
    "|  Tasks     |  Summary:                              |",
    "|  Chat      |  Total People: 6                       |",
    "|  Reports   |  Total Days: 24                        |",
    "|  Salary    |  Present: 138  Absent: 6               |",
    "|            |  Attendance Rate: 95.8%                |",
    "|            |                                        |",
    "|            |  Per Person:                           |",
    "|            |  Aarav: 96%  Priya: 92%  Rohan: 98%   |",
    "+------------+----------------------------------------+",
]
for _ in range(192):
    save(browser_frame("http://localhost:8000/reports", "Reports", reports))

# Scene 9: API Docs (5s = 120 frames)
api_docs = [
    "+----------------------------------------------------+",
    "|  Swagger UI — Attendance Tracker API                |",
    "+----------------------------------------------------+",
    "|                                                      |",
    "|  Authentication                                      |",
    "|  POST /api/auth/login — Login                        |",
    "|  GET  /api/auth/me — Current user                    |",
    "|                                                      |",
    "|  People                                              |",
    "|  GET  /api/people — List people                      |",
    "|  POST /api/people — Add person                       |",
    "|                                                      |",
    "|  Attendance                                          |",
    "|  POST /api/attendance/check-in                       |",
    "|  POST /api/attendance/check-out                      |",
    "|                                                      |",
    "|  + 22 more endpoints...                              |",
    "+----------------------------------------------------+",
]
for _ in range(120):
    save(browser_frame("http://localhost:8000/docs", "API Docs", api_docs))

# Scene 10: Tech Stack (5s = 120 frames)
tech = [
    ("Backend", "FastAPI + Python 3.10+"),
    ("Database", "PostgreSQL + asyncpg"),
    ("ORM", "SQLAlchemy 2.0 (async)"),
    ("Auth", "JWT + bcrypt"),
    ("Validation", "Pydantic v2"),
    ("Frontend", "Vanilla JS + HTML + CSS"),
    ("API", "22 Modules, 50+ Endpoints"),
]
img = gradient((20, 80, 160), (10, 40, 80))
d = ImageDraw.Draw(img)
d.text(((W - d.textbbox((0, 0), "Tech Stack", font=get_font(48))[2]) // 2, 80), "Tech Stack", fill="white", font=get_font(48))
y = 180
for label, value in tech:
    d.text((200, y), f"{label}:", fill=(180, 200, 230), font=get_font(24))
    d.text((450, y), value, fill="white", font=get_font(24))
    y += 55
for _ in range(120):
    save(img)

# Scene 11: Ending (3s = 72 frames)
for _ in range(72):
    img = gradient((20, 80, 160), (10, 40, 80))
    d = ImageDraw.Draw(img)
    d.text(((W - d.textbbox((0, 0), "Attendance Tracker", font=get_font(48))[2]) // 2, 250), "Attendance Tracker", fill="white", font=get_font(48))
    d.text(((W - d.textbbox((0, 0), "Thank You", font=get_font(36))[2]) // 2, 340), "Thank You", fill=(200, 220, 255), font=get_font(36))
    save(img)

print(f"Generated {fc} frames ({fc / FPS:.1f}s at {FPS}fps)")

# Compile to video
print("Encoding video...")
output = "attendance_tracker_90s_showcase.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", str(DIR / "f_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-preset", "ultrafast",
    "-crf", "28",
    output
], check=True)

shutil.rmtree(DIR)
print(f"Done! Video: {output}")
