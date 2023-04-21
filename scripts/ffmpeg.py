"""Module to wrap calls to ffmpeg"""

import os
import subprocess


class Ffmpeg:
    """Warapper class for ffmpeg"""

    def is_ffmpeg_installed(self) -> bool:
        """Check if ffmpeg is installed"""
        try:
            return 0 == subprocess.call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return False

    def create_video(self, input_folder: str, output: str, framerate: float) -> bool:
        """Create mp4 video from ordered images in input folder"""
        if os.path.isfile(output):
            os.remove(output)
        input_pattern: str = os.path.join(input_folder, "%5d.png")
        args: list[str] = ["ffmpeg", "-framerate", f"1/{framerate}", "-i", input_pattern, "-c:v", "libx264", "-r", "25", output]
        return 0 == subprocess.call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
