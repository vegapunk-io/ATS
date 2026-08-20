"""
Quick Video Generator - Minimal dependencies
Creates a simple slideshow video from text and screenshots.
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw, ImageFont


class QuickVideoGenerator:
    """Generate quick video frames for manual compilation."""

    def __init__(self, output_dir: str = "scripts/video_frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.width = 1920
        self.height = 1080
        self.frame_num = 0

    def create_slide(self, title: str, content: list, bg_color: tuple = (20, 60, 120)):
        """Create a single slide image."""
        img = Image.new("RGB", (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 56)
            content_font = ImageFont.truetype("arial.ttf", 32)
        except IOError:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()

        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.width - title_width) // 2, 100), title, fill="white", font=title_font
        )

        y = 220
        for line in content:
            draw.text((150, y), f"• {line}", fill=(220, 240, 255), font=content_font)
            y += 60

        filename = self.output_dir / f"slide_{self.frame_num:03d}.png"
        img.save(filename)
        self.frame_num += 1
        print(f"Created: {filename}")

    def generate_all_slides(self):
        """Generate all showcase slides."""
        print("Generating video frames...")
        
        self.create_slide(
            "Attendance Tracker",
            ["Full-Stack Tracking System", "FastAPI + PostgreSQL + JavaScript"],
            (20, 80, 160),
        )
        
        self.create_slide(
            "Tech Stack",
            [
                "FastAPI - Python web framework",
                "PostgreSQL - Database",
                "SQLAlchemy 2.0 - ORM",
                "JWT - Authentication",
                "Vanilla JS - Frontend",
            ],
            (30, 70, 140),
        )
        
        self.create_slide(
            "Backend Features",
            [
                "Async Python with FastAPI",
                "RESTful API endpoints",
                "JWT + bcrypt security",
                "User & People management",
                "Attendance tracking",
                "CSV export",
            ],
            (40, 90, 160),
        )
        
        self.create_slide(
            "Frontend Features",
            [
                "Clean login interface",
                "Real-time dashboard",
                "Weekly attendance view",
                "Admin management panels",
                "Reports & export",
            ],
            (50, 100, 170),
        )
        
        self.create_slide(
            "Security",
            [
                "JWT token authentication",
                "Bcrypt password hashing",
                "Role-based access control",
                "Protected endpoints",
            ],
            (60, 80, 150),
        )
        
        self.create_slide(
            "Get Started",
            [
                "git clone <repo>",
                "pip install -r requirements.txt",
                "python -m scripts.seed",
                "uvicorn app.main:app --reload",
                "Open http://localhost:8000",
            ],
            (20, 60, 120),
        )

        print(f"\nGenerated {self.frame_num} slides in {self.output_dir}")
        print("\nTo create video, run:")
        print(f'  ffmpeg -framerate 1 -i "{self.output_dir}/slide_%03d.png" -c:v libx264 -pix_fmt yuv420p output.mp4')


def main():
    generator = QuickVideoGenerator()
    generator.generate_all_slides()


if __name__ == "__main__":
    main()
