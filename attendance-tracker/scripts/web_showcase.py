"""
Web App Showcase Video - Actual UI Views Only
"""
import os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 720
FPS = 24
DIR = Path("scripts/frames")
DIR.mkdir(parents=True, exist_ok=True)
fc = 0

def f(sz):
    for n in ["arial.ttf","segoeui.ttf","consola.ttf"]:
        try: return ImageFont.truetype(n, sz)
        except (IOError, OSError): pass
    return ImageFont.load_default()

def s(img):
    global fc; img.save(DIR / f"f_{fc:04d}.png"); fc += 1

def draw_button(d, x, y, w, h, text, color=(79,70,229), text_color="white"):
    d.rounded_rectangle([(x,y),(x+w,y+h)], radius=8, fill=color)
    bbox = d.textbbox((0,0), text, font=f(14))
    tw = bbox[2]-bbox[0]
    d.text((x+(w-tw)//2, y+8), text, fill=text_color, font=f(14))

def draw_input(d, x, y, w, value="", placeholder=""):
    d.rounded_rectangle([(x,y),(x+w,y+32)], radius=6, fill="white", outline=(226,232,240), width=1)
    txt = value if value else placeholder
    color = (15,23,42) if value else (148,163,184)
    d.text((x+10, y+8), txt, fill=color, font=f(13))

def draw_badge(d, x, y, text, bg, fg):
    bbox = d.textbbox((0,0), text, font=f(11))
    w = bbox[2]-bbox[0]+16
    d.rounded_rectangle([(x,y),(x+w,y+22)], radius=11, fill=bg)
    d.text((x+8, y+4), text, fill=fg, font=f(11))

print("Generating web app frames...")

# ==================== LOGIN PAGE (8s) ====================
for _ in range(192):
    # Gradient background
    img = Image.new("RGB", (W,H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y/H
        d.line([(0,y),(W,y)], fill=(tuple(int(c*(1-r*0.5)) for c in (79,70,229))))
    
    # Login card
    cx, cy = W//2-180, H//2-180
    d.rounded_rectangle([(cx,cy),(cx+360,cy+360)], radius=16, fill="white")
    
    # Logo
    d.rounded_rectangle([(cx+154,cy+24),(cx+206,cy+76)], radius=14, fill=(79,70,229))
    d.text((cx+170, cy+35), "V", fill="white", font=f(28))
    
    # Title
    d.text((cx+70, cy+90), "Attendance Tracker", fill=(15,23,42), font=f(22))
    d.text((cx+105, cy+120), "Sign in to your account", fill=(100,116,139), font=f(12))
    
    # Form
    d.text((cx+30, cy+160), "Username", fill=(100,116,139), font=f(12))
    draw_input(d, cx+30, cy+180, 300, "admin")
    
    d.text((cx+30, cy+224), "Password", fill=(100,116,139), font=f(12))
    draw_input(d, cx+30, cy+244, 300, "admin123")
    
    draw_button(d, cx+30, cy+296, 300, 40, "Sign in")
    
    s(img)

# ==================== DASHBOARD - Admin (15s) ====================
for _ in range(360):
    img = Image.new("RGB", (W,H), (241,245,249))
    d = ImageDraw.Draw(img)
    
    # Sidebar
    d.rectangle([(0,0),(220,H)], fill=(15,23,42))
    d.rounded_rectangle([(16,16),(56,56)], radius=10, fill=(79,70,229))
    d.text((24,24), "V", fill="white", font=f(20))
    d.text((64,20), "Attendance", fill="white", font=f(14))
    d.text((64,38), "Tracker System", fill=(148,163,184), font=f(10))
    
    # Nav items
    nav = [("Dashboard", True), ("Attendance", False), ("People", False), ("Users", False), ("Reports", False)]
    ny = 80
    for name, active in nav:
        if active:
            d.rounded_rectangle([(10,ny),(210,ny+36)], radius=8, fill=(79,70,229))
            d.text((24, ny+9), name, fill="white", font=f(13))
        else:
            d.text((24, ny+9), name, fill=(203,213,225), font=f(13))
        ny += 44
    
    # User info at bottom
    d.rounded_rectangle([(10,620),(210,700)], radius=8, fill=(30,41,59))
    d.rounded_rectangle([(20,632),(56,668)], radius=18, fill=(79,70,229))
    d.text((30,640), "A", fill="white", font=f(14))
    d.text((64,636), "System Admin", fill="white", font=f(12))
    d.text((64,654), "Administrator", fill=(148,163,184), font=f(10))
    draw_button(d, 20, 678, 180, 28, "Sign out", (71,85,105))
    
    # Main content
    d.text((260, 20), "Dashboard", fill=(15,23,42), font=f(22))
    d.text((260, 48), "Today's attendance at a glance", fill=(100,116,139), font=f(12))
    d.text((1050, 24), "Friday, August 10, 2026", fill=(79,70,229), font=f(12))
    
    # Hero card
    d.rounded_rectangle([(250,80),(1260,240)], radius=16, fill=(79,70,229))
    d.text((280,100), "FRIDAY, AUGUST 10, 2026", fill=(255,255,255,180), font=f(11))
    d.text((280,120), "Checked In", fill="white", font=f(26))
    d.text((280,160), "09:00 AM", fill="white", font=f(16))
    d.text((280,178), "Check-in", fill=(200,220,255), font=f(11))
    d.text((420,160), "--:--", fill="white", font=f(16))
    d.text((420,178), "Check-out", fill=(200,220,255), font=f(11))
    d.text((540,160), "5h 23m", fill="white", font=f(16))
    d.text((540,178), "Duration", fill=(200,220,255), font=f(11))
    
    # Status pill
    d.rounded_rectangle([(700,160),(810,184)], radius=12, fill=(255,255,255,30))
    d.ellipse([(710,166),(722,178)], fill=(52,211,153))
    d.text((728,164), "On clock", fill="white", font=f(12))
    
    # Buttons
    draw_button(d, 900, 155, 120, 36, "Check in", (255,255,255), (79,70,229))
    draw_button(d, 1040, 155, 120, 36, "Check out", (255,255,255,40), "white")
    
    # Last 7 days card
    d.rounded_rectangle([(250,260),(1260,380)], radius=12, fill="white", outline=(226,232,240))
    d.text((270,274), "Last 7 days", fill=(15,23,42), font=f(14))
    
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    dates = ["4","5","6","7","8","9","10"]
    icons = ["V","V","V","V","O","-","-"]
    dx = 280
    for i in range(7):
        is_today = (i==4)
        if is_today:
            d.rounded_rectangle([(dx-5,298),(dx+75,360)], radius=8, fill=(238,242,255), outline=(79,70,229))
        d.text((dx+20, 300), days[i], fill=(100,116,139), font=f(10))
        d.text((dx+25, 316), dates[i], fill=(15,23,42), font=f(13))
        color = (5,150,105) if icons[i]=="V" else (220,38,38) if icons[i]=="-" else (100,116,139)
        d.text((dx+22, 338), icons[i], fill=color, font=f(16))
        dx += 95
    
    # Recent attendance card
    d.rounded_rectangle([(250,400),(1260,680)], radius=12, fill="white", outline=(226,232,240))
    d.text((270,414), "My recent attendance", fill=(15,23,42), font=f(14))
    
    # Table header
    d.line([(270,440),(1240,440)], fill=(226,232,240))
    headers = ["Date","In","Out","Duration","Status"]
    hx = [280, 450, 570, 700, 850]
    for i, h in enumerate(headers):
        d.text((hx[i], 446), h, fill=(100,116,139), font=f(11))
    
    # Table rows
    rows = [
        ("08/10/2026","09:00","--:--","5h 23m","Present"),
        ("08/09/2026","08:55","17:05","8h 10m","Present"),
        ("08/08/2026","09:02","17:10","8h 8m","Present"),
        ("08/07/2026","08:50","17:00","8h 10m","Present"),
        ("08/06/2026","09:05","17:15","8h 10m","Present"),
    ]
    ry = 472
    for row in rows:
        d.line([(270,ry),(1240,ry)], fill=(241,245,249))
        for i, val in enumerate(row):
            color = (15,23,42) if i < 4 else (5,150,105)
            d.text((hx[i], ry+8), val, fill=color, font=f(12))
        ry += 36
    
    s(img)

# ==================== PEOPLE PAGE (10s) ====================
for _ in range(240):
    img = Image.new("RGB", (W,H), (241,245,249))
    d = ImageDraw.Draw(img)
    
    # Sidebar
    d.rectangle([(0,0),(220,H)], fill=(15,23,42))
    d.rounded_rectangle([(16,16),(56,56)], radius=10, fill=(79,70,229))
    d.text((24,24), "V", fill="white", font=f(20))
    d.text((64,20), "Attendance", fill="white", font=f(14))
    d.text((64,38), "Tracker System", fill=(148,163,184), font=f(10))
    
    nav = [("Dashboard", False), ("Attendance", False), ("People", True), ("Users", False), ("Reports", False)]
    ny = 80
    for name, active in nav:
        if active:
            d.rounded_rectangle([(10,ny),(210,ny+36)], radius=8, fill=(79,70,229))
            d.text((24, ny+9), name, fill="white", font=f(13))
        else:
            d.text((24, ny+9), name, fill=(203,213,225), font=f(13))
        ny += 44
    
    # Main content
    d.text((260, 20), "People", fill=(15,23,42), font=f(22))
    d.text((260, 48), "Employees, students or members being tracked", fill=(100,116,139), font=f(12))
    draw_button(d, 1100, 20, 140, 36, "+ Add person")
    
    # Table card
    d.rounded_rectangle([(250,80),(1260,680)], radius=12, fill="white", outline=(226,232,240))
    
    # Table header
    headers = ["Name","Email","Group","Status","Linked user",""]
    hx = [270, 450, 650, 820, 940, 1100]
    d.line([(270,110),(1240,110)], fill=(226,232,240))
    for i, h in enumerate(headers):
        d.text((hx[i], 116), h, fill=(100,116,139), font=f(11))
    
    # Table rows
    people = [
        ("Rahul Sharma", "rahul.sharma@techcorp.com", "Engineering", "Active", "rahul"),
        ("Neha Patel", "neha.patel@techcorp.com", "Engineering", "Active", "--"),
        ("Amit Kumar", "amit.kumar@techcorp.com", "Engineering", "Active", "--"),
        ("Sneha Reddy", "sneha.reddy@techcorp.com", "Design", "Active", "--"),
        ("Vikram Singh", "vikram.singh@techcorp.com", "Design", "Active", "--"),
        ("Pooja Gupta", "pooja.gupta@techcorp.com", "Marketing", "Active", "--"),
    ]
    ry = 136
    for name, email, group, status, user in people:
        d.line([(270,ry),(1240,ry)], fill=(241,245,249))
        d.text((hx[0], ry+8), name, fill=(15,23,42), font=f(12))
        d.text((hx[1], ry+8), email, fill=(100,116,139), font=f(12))
        d.text((hx[2], ry+8), group, fill=(100,116,139), font=f(12))
        draw_badge(d, hx[3], ry+8, status, (209,250,229), (5,150,105))
        d.text((hx[4], ry+8), user, fill=(100,116,139), font=f(12))
        draw_button(d, hx[5], ry+4, 50, 24, "Edit", (241,245,249), (15,23,42))
        draw_button(d, hx[5]+58, ry+4, 50, 24, "Del", (254,226,226), (220,38,38))
        ry += 52
    
    s(img)

# ==================== USERS PAGE (10s) ====================
for _ in range(240):
    img = Image.new("RGB", (W,H), (241,245,249))
    d = ImageDraw.Draw(img)
    
    # Sidebar
    d.rectangle([(0,0),(220,H)], fill=(15,23,42))
    d.rounded_rectangle([(16,16),(56,56)], radius=10, fill=(79,70,229))
    d.text((24,24), "V", fill="white", font=f(20))
    d.text((64,20), "Attendance", fill="white", font=f(14))
    d.text((64,38), "Tracker System", fill=(148,163,184), font=f(10))
    
    nav = [("Dashboard", False), ("Attendance", False), ("People", False), ("Users", True), ("Reports", False)]
    ny = 80
    for name, active in nav:
        if active:
            d.rounded_rectangle([(10,ny),(210,ny+36)], radius=8, fill=(79,70,229))
            d.text((24, ny+9), name, fill="white", font=f(13))
        else:
            d.text((24, ny+9), name, fill=(203,213,225), font=f(13))
        ny += 44
    
    # Main content
    d.text((260, 20), "User Accounts", fill=(15,23,42), font=f(22))
    d.text((260, 48), "Login accounts and roles", fill=(100,116,139), font=f(12))
    draw_button(d, 1100, 20, 140, 36, "+ Add user")
    
    # Table card
    d.rounded_rectangle([(250,80),(1260,680)], radius=12, fill="white", outline=(226,232,240))
    
    # Table header
    headers = ["Username","Full name","Email","Role","Status","Linked person",""]
    hx = [270, 400, 570, 750, 850, 970, 1120]
    d.line([(270,110),(1240,110)], fill=(226,232,240))
    for i, h in enumerate(headers):
        d.text((hx[i], 116), h, fill=(100,116,139), font=f(11))
    
    # Table rows
    users = [
        ("admin", "System Administrator", "admin@techcorp.com", "admin", "Active", "--"),
        ("rahul", "Rahul Sharma", "rahul.sharma@techcorp.com", "user", "Active", "Rahul Sharma"),
    ]
    ry = 136
    for uname, fname, email, role, status, person in users:
        d.line([(270,ry),(1240,ry)], fill=(241,245,249))
        d.text((hx[0], ry+8), uname, fill=(15,23,42), font=f(12))
        d.text((hx[1], ry+8), fname, fill=(15,23,42), font=f(12))
        d.text((hx[2], ry+8), email, fill=(100,116,139), font=f(12))
        draw_badge(d, hx[3], ry+8, role, (238,242,255), (79,70,229))
        draw_badge(d, hx[4], ry+8, status, (209,250,229), (5,150,105))
        d.text((hx[5], ry+8), person, fill=(100,116,139), font=f(12))
        draw_button(d, hx[6], ry+4, 50, 24, "Edit", (241,245,249), (15,23,42))
        draw_button(d, hx[6]+58, ry+4, 50, 24, "Del", (254,226,226), (220,38,38))
        ry += 52
    
    s(img)

# ==================== ATTENDANCE RECORDS (10s) ====================
for _ in range(240):
    img = Image.new("RGB", (W,H), (241,245,249))
    d = ImageDraw.Draw(img)
    
    # Sidebar
    d.rectangle([(0,0),(220,H)], fill=(15,23,42))
    d.rounded_rectangle([(16,16),(56,56)], radius=10, fill=(79,70,229))
    d.text((24,24), "V", fill="white", font=f(20))
    d.text((64,20), "Attendance", fill="white", font=f(14))
    d.text((64,38), "Tracker System", fill=(148,163,184), font=f(10))
    
    nav = [("Dashboard", False), ("Attendance", True), ("People", False), ("Users", False), ("Reports", False)]
    ny = 80
    for name, active in nav:
        if active:
            d.rounded_rectangle([(10,ny),(210,ny+36)], radius=8, fill=(79,70,229))
            d.text((24, ny+9), name, fill="white", font=f(13))
        else:
            d.text((24, ny+9), name, fill=(203,213,225), font=f(13))
        ny += 44
    
    # Main content
    d.text((260, 20), "Attendance Records", fill=(15,23,42), font=f(22))
    d.text((260, 48), "View and manage attendance entries", fill=(100,116,139), font=f(12))
    
    # Filters
    d.rounded_rectangle([(250,80),(1260,140)], radius=12, fill="white", outline=(226,232,240))
    d.text((270,90), "From", fill=(100,116,139), font=f(11))
    draw_input(d, 270, 108, 130, "2026-08-01")
    d.text((420,90), "To", fill=(100,116,139), font=f(11))
    draw_input(d, 420, 108, 130, "2026-08-10")
    d.text((570,90), "Person", fill=(100,116,139), font=f(11))
    draw_input(d, 570, 108, 150, "All people")
    d.text((740,90), "Status", fill=(100,116,139), font=f(11))
    draw_input(d, 740, 108, 100, "All")
    draw_button(d, 860, 108, 80, 32, "Apply")
    
    # Table card
    d.rounded_rectangle([(250,160),(1260,680)], radius=12, fill="white", outline=(226,232,240))
    
    # Table header
    headers = ["Date","Person","Group","In","Out","Duration","Status",""]
    hx = [270, 370, 520, 650, 750, 850, 960, 1080]
    d.line([(270,190),(1240,190)], fill=(226,232,240))
    for i, h in enumerate(headers):
        d.text((hx[i], 196), h, fill=(100,116,139), font=f(11))
    
    # Table rows
    records = [
        ("08/10/2026","Rahul Sharma","Engineering","09:00","--:--","5h 23m","Present"),
        ("08/10/2026","Neha Patel","Engineering","08:55","17:02","8h 7m","Present"),
        ("08/09/2026","Rahul Sharma","Engineering","08:55","17:05","8h 10m","Present"),
        ("08/09/2026","Amit Kumar","Engineering","09:10","18:00","8h 50m","Present"),
        ("08/08/2026","Sneha Reddy","Design","09:00","17:30","8h 30m","Present"),
        ("08/08/2026","Vikram Singh","Design","09:05","18:15","9h 10m","Present"),
    ]
    ry = 216
    for date, name, group, ci, co, dur, status in records:
        d.line([(270,ry),(1240,ry)], fill=(241,245,249))
        d.text((hx[0], ry+8), date, fill=(15,23,42), font=f(12))
        d.text((hx[1], ry+8), name, fill=(15,23,42), font=f(12))
        d.text((hx[2], ry+8), group, fill=(100,116,139), font=f(12))
        d.text((hx[3], ry+8), ci, fill=(15,23,42), font=f(12))
        d.text((hx[4], ry+8), co, fill=(15,23,42), font=f(12))
        d.text((hx[5], ry+8), dur, fill=(100,116,139), font=f(12))
        draw_badge(d, hx[6], ry+8, status, (209,250,229), (5,150,105))
        draw_button(d, hx[7], ry+4, 50, 24, "Edit", (241,245,249), (15,23,42))
        ry += 52
    
    s(img)

# ==================== REPORTS PAGE (10s) ====================
for _ in range(240):
    img = Image.new("RGB", (W,H), (241,245,249))
    d = ImageDraw.Draw(img)
    
    # Sidebar
    d.rectangle([(0,0),(220,H)], fill=(15,23,42))
    d.rounded_rectangle([(16,16),(56,56)], radius=10, fill=(79,70,229))
    d.text((24,24), "V", fill="white", font=f(20))
    d.text((64,20), "Attendance", fill="white", font=f(14))
    d.text((64,38), "Tracker System", fill=(148,163,184), font=f(10))
    
    nav = [("Dashboard", False), ("Attendance", False), ("People", False), ("Users", False), ("Reports", True)]
    ny = 80
    for name, active in nav:
        if active:
            d.rounded_rectangle([(10,ny),(210,ny+36)], radius=8, fill=(79,70,229))
            d.text((24, ny+9), name, fill="white", font=f(13))
        else:
            d.text((24, ny+9), name, fill=(203,213,225), font=f(13))
        ny += 44
    
    # Main content
    d.text((260, 20), "Reports", fill=(15,23,42), font=f(22))
    d.text((260, 48), "Summary per person for a date range", fill=(100,116,139), font=f(12))
    draw_button(d, 1100, 20, 140, 36, "Export CSV", (255,255,255), (79,70,229))
    
    # Filters
    d.rounded_rectangle([(250,80),(1260,140)], radius=12, fill="white", outline=(226,232,240))
    d.text((270,90), "From", fill=(100,116,139), font=f(11))
    draw_input(d, 270, 108, 130, "2026-08-01")
    d.text((420,90), "To", fill=(100,116,139), font=f(11))
    draw_input(d, 420, 108, 130, "2026-08-10")
    d.text((570,90), "Group", fill=(100,116,139), font=f(11))
    draw_input(d, 570, 108, 150, "All groups")
    draw_button(d, 740, 108, 120, 32, "Run report")
    
    # Stat cards
    stats = [("6","People"),("10","Days in range"),("44","Present day-marks"),("2","Absent day-marks"),("352h","Total work time")]
    sx = 260
    for val, label in stats:
        d.rounded_rectangle([(sx,158),(sx+170,220)], radius=12, fill="white", outline=(226,232,240))
        d.text((sx+16, 170), val, fill=(15,23,42), font=f(24))
        d.text((sx+16, 200), label, fill=(100,116,139), font=f(11))
        sx += 190
    
    # Table card
    d.rounded_rectangle([(250,240),(1260,680)], radius=12, fill="white", outline=(226,232,240))
    
    # Table header
    headers = ["Person","Group","Present","Absent","Half","Holiday","Work time","Avg in","Avg out","Rate"]
    hx = [270, 420, 540, 610, 680, 750, 830, 950, 1050, 1150]
    d.line([(270,270),(1240,270)], fill=(226,232,240))
    for i, h in enumerate(headers):
        d.text((hx[i], 276), h, fill=(100,116,139), font=f(10))
    
    # Table rows
    reports = [
        ("Rahul Sharma","Engineering","8","0","0","0","65h 20m","09:00","17:10","80%"),
        ("Neha Patel","Engineering","7","1","0","0","58h 45m","08:55","17:02","70%"),
        ("Amit Kumar","Engineering","9","0","0","0","74h 30m","09:05","17:45","90%"),
        ("Sneha Reddy","Design","6","2","0","0","50h 15m","09:10","17:20","60%"),
        ("Vikram Singh","Marketing","8","0","0","0","68h 00m","09:00","18:00","80%"),
        ("Pooja Gupta","Marketing","6","2","0","0","48h 30m","08:55","17:10","60%"),
    ]
    ry = 296
    for name, group, pres, ab, half, hol, work, avg_in, avg_out, rate in reports:
        d.line([(270,ry),(1240,ry)], fill=(241,245,249))
        d.text((hx[0], ry+8), name, fill=(15,23,42), font=f(12))
        d.text((hx[1], ry+8), group, fill=(100,116,139), font=f(12))
        d.text((hx[2], ry+8), pres, fill=(15,23,42), font=f(12))
        d.text((hx[3], ry+8), ab, fill=(220,38,38), font=f(12))
        d.text((hx[4], ry+8), half, fill=(15,23,42), font=f(12))
        d.text((hx[5], ry+8), hol, fill=(15,23,42), font=f(12))
        d.text((hx[6], ry+8), work, fill=(100,116,139), font=f(12))
        d.text((hx[7], ry+8), avg_in, fill=(15,23,42), font=f(12))
        d.text((hx[8], ry+8), avg_out, fill=(15,23,42), font=f(12))
        # Rate bar
        rate_val = int(rate.replace('%',''))
        d.rounded_rectangle([(hx[9], ry+10),(hx[9]+80, ry+20)], radius=4, fill=(241,245,249))
        d.rounded_rectangle([(hx[9], ry+10),(hx[9]+rate_val, ry+20)], radius=4, fill=(5,150,105))
        d.text((hx[9]+85, ry+8), rate, fill=(15,23,42), font=f(12))
        ry += 48
    
    s(img)

# ==================== ENDING (4s) ====================
for _ in range(96):
    img = Image.new("RGB", (W,H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y/H
        d.line([(0,y),(W,y)], fill=(tuple(int(c*(1-r*0.5)) for c in (79,70,229))))
    
    d.text(((W-d.textbbox((0,0),"Attendance Tracker",font=f(48))[2])//2, 240), "Attendance Tracker", fill="white", font=f(48))
    d.text(((W-d.textbbox((0,0),"FastAPI | PostgreSQL | SQLAlchemy | JWT | Vanilla JS",font=f(16))[2])//2, 310), "FastAPI | PostgreSQL | SQLAlchemy | JWT | Vanilla JS", fill=(200,220,255), font=f(16))
    d.text(((W-d.textbbox((0,0),"Thank You!",font=f(32))[2])//2, 370), "Thank You!", fill=(200,220,255), font=f(32))
    s(img)

print(f"Generated {fc} frames ({fc/FPS:.1f}s)")

print("Encoding video...")
subprocess.run(["ffmpeg","-y","-framerate",str(FPS),"-i",str(DIR/"f_%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-preset","ultrafast","-crf","28","attendance_tracker_web_showcase.mp4"],check=True)

import shutil; shutil.rmtree(DIR)
print(f"Done! attendance_tracker_web_showcase.mp4")
