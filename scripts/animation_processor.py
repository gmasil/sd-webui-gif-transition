"""Module to create several animation types"""

import os
import tempfile
import uuid
from typing import Any, List

from modules.shared import opts

from scripts.ffmpeg import Ffmpeg
from scripts.webp import Webp


class AnimationProcessor:
    """Class to create several animation types from given frames"""

    def __init__(self) -> None:
        self.ffmpeg: Ffmpeg = Ffmpeg()
        self.webp: Webp = Webp()

    def create_animation(self, frames: List[Any], base_outpath: str | None, animation_duration: int, animation_type: str) -> str:
        """Function to generate an animated image or video from the given frames and saves it to a generic output directory"""

        # strip any postfixes from animation type like "(not installed)"
        animation_type = animation_type.split(" ")[0]
        filename: str = str(uuid.uuid4())

        if base_outpath is None:
            base_outpath = opts.outdir_txt2img_samples
        outpath: str = os.path.join(base_outpath, "gif-transition")
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        full_file_path: str = os.path.join(outpath, f"{filename}.{animation_type}")

        if animation_type == "gif":
            self.create_gif(frames, full_file_path, animation_duration)
        elif animation_type == "webp":
            self.create_webp(frames, full_file_path, animation_duration)
        elif animation_type == "mp4":
            self.create_mp4(frames, full_file_path, animation_duration)

        # this should never happen, fall back to gif
        return full_file_path

    def create_gif(self, frames: List[Any], full_file_path: str, animation_duration: int) -> None:
        """Create gif from given frames"""
        frame_duration: int = int(animation_duration/len(frames))
        first_frame, append_frames = frames[0], frames[1:]
        first_frame.save(full_file_path, format="GIF", append_images=append_frames, save_all=True, duration=frame_duration, loop=0)

    def create_webp(self, frames: List[Any], full_file_path: str, animation_duration: int) -> None:
        """Create webp from given frames"""
        tmp: str = os.path.join(tempfile.gettempdir(), "sd-webui-gif-transition")
        os.makedirs(tmp, exist_ok=True)
        # save frames as png to disk
        saved_pngs = []
        for frame in frames:
            frame_filename: str = os.path.join(tmp, f"{str(uuid.uuid4())}.png")
            frame.save(frame_filename)
            saved_pngs += [frame_filename]
        self.webp.create_webp(saved_pngs, animation_duration, full_file_path)
        for saved_png in saved_pngs:
            if os.path.isfile(saved_png):
                os.remove(saved_png)

    def create_mp4(self, frames: List[Any], full_file_path: str, animation_duration: int) -> None:
        """Create mp4 from given frames"""
        tmp: str = os.path.join(tempfile.gettempdir(), "sd-webui-gif-transition", str(uuid.uuid4()))
        os.makedirs(tmp, exist_ok=True)
        frame_duration: float = animation_duration/len(frames)/1000
        saved_pngs = []
        i: int = 0
        for frame in frames:
            frame_filename: str = os.path.join(tmp, f"{i:05d}.png")
            frame.save(frame_filename)
            saved_pngs += [frame_filename]
            i += 1
        self.ffmpeg.create_video(tmp, full_file_path, frame_duration)
        for saved_png in saved_pngs:
            if os.path.isfile(saved_png):
                os.remove(saved_png)
        os.rmdir(tmp)
