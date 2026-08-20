"""
Showcase Video Generator for Attendance Tracker
Generates a promotional video showcasing the application features.
"""

import os
import sys
from pathlib import Path

try:
    from moviepy import (
        ImageClip,
        concatenate_videoclips,
    )
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install moviepy Pillow numpy")
    from moviepy import (
        ImageClip,
        concatenate_videoclips,
    )
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np


class ShowcaseVideoGenerator:
    """Generate showcase video for Attendance Tracker."""

    def __init__(self, output_path: str = "showcase_video.mp4"):
        self.output_path = output_path
        self.width = 1920
        self.height = 1080
        self.fps = 30
        self.duration_per_scene = 4
        self.slides_dir = Path("scripts/slides")
        self.slides_dir.mkdir(exist_ok=True)

    def create_gradient_background(
        self, color1: tuple, color2: tuple, size: tuple = None
    ) -> np.ndarray:
        """Create a gradient background image."""
        if size is None:
            size = (self.width, self.height)

        img = Image.new("RGB", size)
        draw = ImageDraw.Draw(img)

        for y in range(size[1]):
            ratio = y / size[1]
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))

        return np.array(img)

    def create_title_slide(self, title: str, subtitle: str) -> np.ndarray:
        """Create a title slide with gradient background."""
        bg = self.create_gradient_background((20, 100, 200), (40, 60, 120))
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 72)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
        except IOError:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        title_y = self.height // 2 - 80
        draw.text((title_x, title_y), title, fill="white", font=title_font)

        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        sub_x = (self.width - sub_width) // 2
        sub_y = title_y + 120
        draw.text((sub_x, sub_y), subtitle, fill=(200, 220, 255), font=subtitle_font)

        return np.array(img)

    def create_feature_slide(
        self, title: str, features: list, icon: str = "★"
    ) -> np.ndarray:
        """Create a feature listing slide."""
        bg = self.create_gradient_background((30, 80, 150), (20, 50, 100))
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 56)
            feature_font = ImageFont.truetype("arial.ttf", 32)
        except IOError:
            title_font = ImageFont.load_default()
            feature_font = ImageFont.load_default()

        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.width - title_width) // 2
        draw.text((title_x, 100), title, fill="white", font=title_font)

        y_offset = 250
        for feature in features:
            text = f"{icon} {feature}"
            draw.text((200, y_offset), text, fill=(220, 240, 255), font=feature_font)
            y_offset += 70

        return np.array(img)

    def create_code_slide(self, title: str, code: str, language: str = "python") -> np.ndarray:
        """Create a code showcase slide."""
        bg = Image.new("RGB", (self.width, self.height), (30, 30, 30))
        draw = ImageDraw.Draw(bg)

        try:
            title_font = ImageFont.truetype("arial.ttf", 42)
            code_font = ImageFont.truetype("consola.ttf", 24)
        except IOError:
            try:
                code_font = ImageFont.truetype("cour.ttf", 24)
            except IOError:
                title_font = ImageFont.load_default()
                code_font = ImageFont.load_default()

        draw.text((100, 50), title, fill="white", font=title_font)
        draw.line([(100, 110), (600, 110)], fill=(100, 150, 255), width=3)

        lines = code.strip().split("\n")
        y_offset = 160
        for line in lines[:20]:
            draw.text((120, y_offset), line, fill=(200, 255, 200), font=code_font)
            y_offset += 35

        return np.array(bg)

    def create_architecture_slide(self) -> np.ndarray:
        """Create an architecture diagram slide."""
        bg = self.create_gradient_background((25, 60, 120), (15, 40, 80))
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 48)
            label_font = ImageFont.truetype("arial.ttf", 28)
        except IOError:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()

        draw.text((self.width // 2 - 200, 50), "System Architecture", fill="white", font=title_font)

        boxes = [
            (200, 200, 500, 320, "Frontend\nVanilla JS + HTML/CSS", (70, 130, 230)),
            (700, 200, 1000, 320, "FastAPI\nBackend", (50, 180, 100)),
            (1200, 200, 1500, 320, "PostgreSQL\nDatabase", (200, 100, 60)),
            (700, 400, 1000, 520, "JWT Auth\nSecurity", (180, 60, 180)),
        ]

        for x1, y1, x2, y2, label, color in boxes:
            draw.rounded_rectangle([x1, y1, x2, y2], radius=15, fill=color)
            lines = label.split("\n")
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=label_font)
                text_width = bbox[2] - bbox[0]
                text_x = x1 + (x2 - x1 - text_width) // 2
                text_y = y1 + 30 + i * 35
                draw.text((text_x, text_y), line, fill="white", font=label_font)

        arrows = [
            (500, 260, 700, 260),
            (1000, 260, 1200, 260),
            (850, 320, 850, 400),
        ]

        for x1, y1, x2, y2 in arrows:
            draw.line([(x1, y1), (x2, y2)], fill="white", width=3)
            draw.polygon([(x2, y2), (x2 - 10, y2 - 10), (x2 - 10, y2 + 10)], fill="white")

        return np.array(img)

    def create_ending_slide(self) -> np.ndarray:
        """Create the ending/CTA slide."""
        bg = self.create_gradient_background((20, 80, 160), (10, 40, 100))
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        try:
            title_font = ImageFont.truetype("arial.ttf", 64)
            sub_font = ImageFont.truetype("arial.ttf", 32)
        except IOError:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        title = "Attendance Tracker"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((self.width - title_width) // 2, 300), title, fill="white", font=title_font)

        subtitle = "Full-Stack FastAPI Application"
        sub_bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sub_width = sub_bbox[2] - sub_bbox[0]
        draw.text(
            ((self.width - sub_width) // 2, 420), subtitle, fill=(200, 220, 255), font=sub_font
        )

        tech = "FastAPI • PostgreSQL • SQLAlchemy • JWT • Vanilla JS"
        tech_bbox = draw.textbbox((0, 0), tech, font=sub_font)
        tech_width = tech_bbox[2] - tech_bbox[0]
        draw.text(
            ((self.width - tech_width) // 2, 520), tech, fill=(180, 200, 230), font=sub_font
        )

        return np.array(img)

    def generate_video(self):
        """Generate the complete showcase video."""
        print("Generating showcase video...")

        scenes = []

        print("  Creating title slide...")
        title_img = self.create_title_slide(
            "Attendance Tracker", "Full-Stack Tracking System"
        )
        scenes.append(ImageClip(title_img).with_duration(self.duration_per_scene + 1))

        print("  Creating tech stack slide...")
        tech_img = self.create_feature_slide(
            "Tech Stack",
            [
                "FastAPI - High-performance Python framework",
                "PostgreSQL - Production-ready database",
                "SQLAlchemy 2.0 - Modern async ORM",
                "JWT Authentication - Secure token-based auth",
                "Pydantic v2 - Data validation",
                "Vanilla JavaScript - Lightweight frontend",
            ],
            "⚡",
        )
        scenes.append(ImageClip(tech_img).with_duration(self.duration_per_scene))

        print("  Creating architecture slide...")
        arch_img = self.create_architecture_slide()
        scenes.append(ImageClip(arch_img).with_duration(self.duration_per_scene + 1))

        print("  Creating backend features slide...")
        backend_img = self.create_feature_slide(
            "Backend Features",
            [
                "Async Python with FastAPI",
                "RESTful API endpoints",
                "JWT + bcrypt authentication",
                "CRUD operations for users & people",
                "Attendance check-in/check-out",
                "CSV export & reports",
            ],
            "🔧",
        )
        scenes.append(ImageClip(backend_img).with_duration(self.duration_per_scene))

        print("  Creating code sample slide...")
        code = """from fastapi import FastAPI, Depends
from app.security import create_token
from app.deps import get_db, get_current_user

app = FastAPI()

@app.post("/api/auth/login")
async def login(username: str, password: str):
    user = await authenticate(username, password)
    token = create_token(user.id)
    return {"access_token": token}"""
        code_img = self.create_code_slide("API Endpoint Example", code)
        scenes.append(ImageClip(code_img).with_duration(self.duration_per_scene + 1))

        print("  Creating frontend features slide...")
        frontend_img = self.create_feature_slide(
            "Frontend Features",
            [
                "Clean, responsive login interface",
                "Real-time dashboard with attendance status",
                "Weekly attendance visualization",
                "Admin: People & user management",
                "Admin: Attendance records & filters",
                "Admin: Reports & CSV export",
            ],
            "🎨",
        )
        scenes.append(ImageClip(frontend_img).with_duration(self.duration_per_scene))

        print("  Creating security slide...")
        security_img = self.create_feature_slide(
            "Security Features",
            [
                "JWT token-based authentication",
                "Bcrypt password hashing",
                "Role-based access control",
                "Admin vs User permissions",
                "Protected API endpoints",
                "Secure session management",
            ],
            "🔒",
        )
        scenes.append(ImageClip(security_img).with_duration(self.duration_per_scene))

        print("  Creating ending slide...")
        ending_img = self.create_ending_slide()
        scenes.append(ImageClip(ending_img).with_duration(self.duration_per_scene + 2))

        print("  Concatenating scenes...")
        final_video = concatenate_videoclips(scenes, method="compose")

        print(f"  Saving video to {self.output_path}...")
        final_video.write_videofile(
            self.output_path,
            fps=self.fps,
            codec="libx264",
            audio=False,
            preset="medium",
            threads=4,
        )

        print(f"Video generated successfully: {self.output_path}")
        return self.output_path


def main():
    output = sys.argv[1] if len(sys.argv) > 1 else "attendance_tracker_showcase.mp4"
    generator = ShowcaseVideoGenerator(output_path=output)
    generator.generate_video()


if __name__ == "__main__":
    main()
