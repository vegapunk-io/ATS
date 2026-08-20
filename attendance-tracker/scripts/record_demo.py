"""
Screen Recording Script for Attendance Tracker Demo
Records the actual application in action.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

try:
    import pyautogui
    from PIL import Image
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install pyautogui Pillow numpy")
    import pyautogui
    from PIL import Image
    import numpy as np


class DemoRecorder:
    """Record the application demo automatically."""

    def __init__(self, output_path: str = "demo_recording.mp4", duration: int = 60):
        self.output_path = output_path
        self.duration = duration
        self.fps = 15
        self.frames_dir = Path("scripts/frames")
        self.frames_dir.mkdir(exist_ok=True)
        self.frame_count = 0

    def capture_frame(self) -> np.ndarray:
        """Capture current screen."""
        screenshot = pyautogui.screenshot()
        return np.array(screenshot)

    def save_frame(self, frame: np.ndarray):
        """Save frame to disk."""
        img = Image.fromarray(frame)
        img.save(self.frames_dir / f"frame_{self.frame_count:05d}.png")
        self.frame_count += 1

    def record_screen(self):
        """Record screen for specified duration."""
        print(f"Recording screen for {self.duration} seconds...")
        print("Press Ctrl+C to stop early.")
        
        start_time = time.time()
        frame_interval = 1.0 / self.fps

        try:
            while time.time() - start_time < self.duration:
                frame_start = time.time()
                
                frame = self.capture_frame()
                self.save_frame(frame)
                
                elapsed = time.time() - frame_start
                sleep_time = max(0, frame_interval - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\nRecording stopped by user.")

        print(f"Captured {self.frame_count} frames.")

    def compile_video(self):
        """Compile frames to video using ffmpeg."""
        print("Compiling video...")
        
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate", str(self.fps),
            "-i", str(self.frames_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            self.output_path,
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Video saved to {self.output_path}")
        except FileNotFoundError:
            print("ffmpeg not found. Please install ffmpeg:")
            print("  Windows: winget install ffmpeg")
            print("  Or download from: https://ffmpeg.org/download.html")
        except subprocess.CalledProcessError as e:
            print(f"Error compiling video: {e}")

    def cleanup(self):
        """Remove temporary frame files."""
        print("Cleaning up frames...")
        for frame_file in self.frames_dir.glob("frame_*.png"):
            frame_file.unlink()
        self.frames_dir.rmdir()

    def run(self):
        """Run the recording process."""
        self.record_screen()
        self.compile_video()
        self.cleanup()


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    output = sys.argv[2] if len(sys.argv) > 2 else "attendance_tracker_demo.mp4"
    
    recorder = DemoRecorder(output_path=output, duration=duration)
    
    print("=== Attendance Tracker Demo Recorder ===")
    print(f"Duration: {duration} seconds")
    print(f"Output: {output}")
    print()
    print("Make sure the application is running at http://localhost:8000")
    print("The recording will start in 3 seconds...")
    print("Press Ctrl+C to stop early.")
    print()
    
    time.sleep(3)
    recorder.run()


if __name__ == "__main__":
    main()
