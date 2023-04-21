"""Extension entrypoint for stable-diffusion-webui"""

from typing import Any, List

import gradio as gr
from modules import scripts
from modules.processing import (Processed, StableDiffusionProcessing, fix_seed,
                                process_images)
from modules.shared import state

from scripts.animation_processor import AnimationProcessor


class GifTransitionExtension(scripts.Script):
    """Main extension class"""

    def __init__(self) -> None:
        super().__init__()
        self.animation_processor: AnimationProcessor = AnimationProcessor()
        self.working: bool = False
        self.stored_images: List[Any] = []
        self.stored_all_prompts: List[str] = []
        self.stored_infotexts: List[str] = []
        self.stored_seeds: List[int] = []
        self.outpath: str | None = None

    def title(self) -> str:
        """Define extension title"""
        return "GIF Transition"

    def show(self, _is_img2img: bool) -> Any:
        """Always show the script in txt2img and img2img tabs"""
        return scripts.AlwaysVisible

    def map_from_to(self, value: float, source_min: float, source_max: float, target_min: float, target_max: float) -> float:
        """Function to map a value from a source range to a target range"""
        mapped: float = (value-source_min)/(source_max-source_min)*(target_max-target_min)+target_min
        return round(mapped, 2)

    def build_prompts(self, original_prompt: str, start_tag: str, end_tag: str, bias_min: float, bias_max: float, image_count: int) -> List[str]:
        """Function to build SD prompts with a linear transition from start_tag to end_tag"""
        image_count = int(image_count)
        prompts = []
        for i in range(image_count):
            first_bias = self.map_from_to((image_count-1-i) / (image_count-1), 0, 1, bias_min, bias_max)
            second_bias = self.map_from_to(i / (image_count-1), 0, 1, bias_min, bias_max)
            prompts.append(f"({start_tag}:{first_bias}), ({end_tag}:{second_bias}), {original_prompt}, ")
        return prompts

    def create_animation(self, animation_duration: int, animation_type: str) -> str:
        """Function to generate an animated GIF from the given frames and saves it to a generic output directory"""
        return self.animation_processor.create_animation(self.stored_images, self.outpath, animation_duration, animation_type)

    def ui(self, _is_img2img: bool) -> List[Any]:
        """Generate gradio UI"""

        def get_animation_type_choices() -> List[str]:
            mp4_supported: bool = self.animation_processor.ffmpeg.is_ffmpeg_installed()
            return ["webp", "gif", f"mp4{'' if mp4_supported else ' (ffmpeg not installed)'}"]

        with gr.Group():
            with gr.Accordion("GIF Transition", open=False, elem_id="giftransition"):
                with gr.Row():
                    gr_enabled: bool = gr.Checkbox(label='Enable', value=False)
                    gr_only_recreate_gif: bool = gr.Checkbox(label='Only recreate gif/webp', value=False)
                with gr.Row():
                    gr_start_tag: str = gr.Textbox(label="Start tag", value="short hair")
                    gr_end_tag: str = gr.Textbox(label="End tag", value="long hair")
                with gr.Row():
                    gr_bias_min: float = gr.Slider(label="Bias min (default: 0.6)", value=0.6, minimum=0.0, maximum=3.0, step=0.1)
                    gr_bias_max: float = gr.Slider(label="Bias max (default: 1.4)", value=1.4, minimum=0.0, maximum=3.0, step=0.1)
                with gr.Row():
                    gr_image_count: int = gr.Number(label="Amount of frames", value=12, precision=0)
                    gr_animation_duration: int = gr.Number(label="Total animation duration (in ms)", value=1000, precision=0)
                    gr_type: str = gr.Dropdown(choices=get_animation_type_choices(), label="Image type", value="webp")

        return [gr_enabled, gr_only_recreate_gif, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count, gr_animation_duration, gr_type]

    def process(self, p: StableDiffusionProcessing, gr_enabled: bool, gr_only_recreate_gif: bool, gr_start_tag: str, gr_end_tag: str, gr_bias_min: float, gr_bias_max: float, gr_image_count: int, _gr_animation_duration: int, _gr_type: str) -> None:
        """Main process function to intercept image generation"""

        if not gr_enabled or self.working:
            # prevent endless loop
            return

        if gr_enabled and gr_only_recreate_gif and len(self.stored_images) > 0:
            # skip processing, only generate gif in postprocess
            p.n_iter = 0
            return

        # enforce int type
        gr_image_count = int(gr_image_count)

        # reset state
        self.working = True
        self.stored_images = []
        self.stored_all_prompts = []
        self.stored_infotexts = []
        self.stored_seeds = []
        self.outpath = p.outpath_samples

        p.batch_size = 1
        p.n_iter = 1

        original_prompt = p.prompt.strip().rstrip(',')
        if gr_image_count <= 1:
            frame_prompts = [original_prompt]
        else:
            frame_prompts = self.build_prompts(original_prompt, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count)

        fix_seed(p)

        state.job_count = len(frame_prompts)

        for frame_prompt in frame_prompts:
            if state.interrupted:
                self.working = False
                return

            p.prompt = frame_prompt
            proc = process_images(p)

            if state.interrupted:
                self.working = False
                return

            self.stored_images += proc.images
            self.stored_all_prompts += proc.all_prompts
            self.stored_infotexts += proc.infotexts
            self.stored_seeds += proc.all_seeds

        # remove pose images of ControlNet if present
        if len(self.stored_images) % len(frame_prompts) == 0:
            # found multitude of rendered images
            nth_element: int = len(self.stored_images) // len(frame_prompts)
            self.stored_images = self.stored_images[::nth_element]

        self.working = False
        p.n_iter = 0

    def postprocess(self, _p: StableDiffusionProcessing, processed: Processed, gr_enabled: bool, gr_only_recreate_gif: bool, _gr_start_tag: str, _gr_end_tag: str, _gr_bias_min: float, _gr_bias_max: float, gr_image_count: int, gr_animation_duration: int, gr_type: str) -> None:
        """Function to collect all generated images after processing is done"""

        if self.working:
            return

        if (not gr_enabled or not gr_only_recreate_gif or len(self.stored_images) == 0) and (not gr_enabled or self.working):
            # skip if not required
            return

        processed.images = self.stored_images.copy()
        processed.all_prompts = self.stored_all_prompts.copy()
        processed.infotexts = self.stored_infotexts.copy()
        processed.all_seeds = self.stored_seeds.copy()

        is_valid_animation_type: bool = " " not in gr_type

        if gr_image_count > 1 and len(self.stored_images) > 0 and len(self.stored_images) == gr_image_count and is_valid_animation_type:
            processed.images += [self.create_animation(gr_animation_duration, gr_type)]
            processed.all_prompts += ["GIF Transition Result"]
            processed.infotexts += ["GIF Transition Result"]
            processed.all_seeds += [-1]
