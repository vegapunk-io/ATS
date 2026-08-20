# Demo Recording Guide

## Option 1: Manual Recording (Step-by-Step)

### Scene 1: Project Setup (30s)
```
Show terminal:
cd attendance-tracker
pip install -r requirements.txt
python -m scripts.seed
uvicorn app.main:app --reload
```

### Scene 2: Login (20s)
```
Browser: http://localhost:8000/login
- Show clean login form
- Login as admin
- Show redirect to dashboard
```

### Scene 3: Dashboard (30s)
```
- Show today's attendance
- Show weekly strip
- Show recent records
```

### Scene 4: Admin Features (60s)
```
Sidebar: People
- Show list of people
- Add new person

Sidebar: Users
- Show user list
- Create new user

Sidebar: Attendance
- Show records table
- Filter by date
```

### Scene 5: Reports (30s)
```
Sidebar: Reports
- Run report for current month
- Show statistics
- Export CSV
```

### Scene 6: User View (30s)
```
Logout → Login as aarav
- Show limited sidebar
- Check in/out
- View own records
```

### Scene 7: API Demo (30s)
```
Show Swagger UI: http://localhost:8000/docs
- Test login endpoint
- Show authenticated requests
```

## Total: ~3-4 minutes

## Recording Tools
- **Windows**: Xbox Game Bar (Win+G)
- **Mac**: QuickTime
- **Cross-platform**: OBS Studio (free)

---

## Option 2: Automated Video Generation

### Quick Slide Generator (No moviepy required)
```bash
cd attendance-tracker
python scripts/quick_video.py

# Compile to video (requires ffmpeg):
ffmpeg -framerate 1 -i "scripts/video_frames/slide_%03d.png" -c:v libx264 -pix_fmt yuv420p showcase.mp4
```

### Full Video Generator (moviepy)
```bash
cd attendance-tracker
pip install moviepy Pillow numpy
python scripts/generate_showcase_video.py
```

### Screen Recorder (records actual app)
```bash
cd attendance-tracker
pip install pyautogui Pillow numpy

# Start the server first:
uvicorn app.main:app --reload

# Then record (60 seconds):
python scripts/record_demo.py 60 my_demo.mp4
```

---

## Video Scripts Location
- `scripts/generate_showcase_video.py` - Auto-generated promotional video
- `scripts/record_demo.py` - Screen recording of live app
- `scripts/quick_video.py` - Simple slide frames generator
