"""Extension entrypoint for stable-diffusion-webui"""

import os
import uuid
import gradio as gr
from modules import scripts
from modules.shared import state
from modules.processing import process_images, fix_seed


def map_from_to(value: int, source_min: int, source_max: int, target_min: int, target_max: int) -> float:
    """Function to map a value from a source range to a target range"""
    mapped: float = (value-source_min)/(source_max-source_min)*(target_max-target_min)+target_min
    return round(mapped, 2)


def build_prompts(original_prompt: str, start_tag: str, end_tag: str, bias_min: float, bias_max: float, image_count: int) -> list[str]:
    """Function to build SD prompts with a linear transition from start_tag to end_tag"""
    image_count = int(image_count)
    prompts = []
    for i in range(image_count):
        first_bias = map_from_to((image_count-1-i) / (image_count-1), 0, 1, bias_min, bias_max)
        second_bias = map_from_to(i / (image_count-1), 0, 1, bias_min, bias_max)
        prompts.append(f"({start_tag}:{first_bias}), ({end_tag}:{second_bias}), {original_prompt}, ")
    return prompts


def make_gif(frames, animation_duration: int):
    """Function to generate an animated GIF from the given frames and saves it to a generic output directory"""
    filename: str = str(uuid.uuid4())

    outpath = "/output/gif-transition"
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    frame_duration: int = int(animation_duration/len(frames))
    first_frame, append_frames = frames[0], frames[1:]
    full_file_path: str = f"{outpath}/{filename}.gif"
    first_frame.save(full_file_path, format="GIF", append_images=append_frames, save_all=True, duration=frame_duration, loop=0)
    return [full_file_path]


class GifTransitionExtension(scripts.Script):
    """Main extension class"""

    def __init__(self):
        super().__init__()
        self.working: bool = False
        self.stored_images = []
        self.stored_all_prompts = []
        self.stored_infotexts = []
        self.stored_seeds = []

    def title(self):
        """Define extension title"""
        return "GIF Transition"

    def show(self, _is_img2img):
        """Always show the script in txt2img and img2img tabs"""
        return scripts.AlwaysVisible

    def create_gif(self, animation_duration):
        """Function to generate an animated GIF from the given frames and saves it to a generic output directory"""
        return make_gif(self.stored_images, animation_duration)

    def ui(self, _is_img2img):
        """Generate gradio UI"""
        with gr.Group():
            with gr.Accordion("GIF Transition", open=False, elem_id="giftransition"):
                with gr.Row():
                    gr_enabled: bool = gr.Checkbox(label='Enable', value=False)
                    gr_only_recreate_gif: bool = gr.Checkbox(label='Only recreate gif', value=False)
                with gr.Row():
                    gr_start_tag: str = gr.Textbox(label="Start tag", value="short hair")
                    gr_end_tag: str = gr.Textbox(label="End tag", value="long hair")
                with gr.Row():
                    gr_bias_min: float = gr.Number(label="Bias min", value=0.6)
                    gr_bias_max: float = gr.Number(label="Bias max", value=1.4)
                with gr.Row():
                    gr_image_count: int = gr.Number(label="Amount of frames", value=12)
                    gr_gif_duration: int = gr.Number(label="Total animation duration (in ms)", value=1000)

        return [gr_enabled, gr_only_recreate_gif, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count, gr_gif_duration]

    def process(self, p, gr_enabled: bool, gr_only_recreate_gif: bool, gr_start_tag: str, gr_end_tag: str, gr_bias_min: float, gr_bias_max: float, gr_image_count: int, _gr_gif_duration: int):
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

        if gr_image_count <= 0:
            # skip processing if no images should be generated
            p.n_iter = 0
            return

        # reset state
        self.working = True
        self.stored_images = []
        self.stored_all_prompts = []
        self.stored_infotexts = []
        self.stored_seeds = []

        p.batch_size = 1
        p.n_iter = 1

        original_prompt = p.prompt.strip().rstrip(',')
        frame_prompts = build_prompts(original_prompt, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count)

        fix_seed(p)

        state.job_count = len(frame_prompts)

        for frame_prompt in frame_prompts:
            if state.interrupted:
                return

            p.prompt = frame_prompt
            proc = process_images(p)

            if state.interrupted:
                return

            self.stored_images += proc.images
            self.stored_all_prompts += proc.all_prompts
            self.stored_infotexts += proc.infotexts
            self.stored_seeds += proc.all_seeds

        # remove pose images of ControlNet if present
        if len(frame_prompts) * 2 == len(self.stored_images):
            del self.stored_images[1::2]

        self.working = False
        p.n_iter = 0

    def postprocess(self, _p, processed, gr_enabled: bool, gr_only_recreate_gif: bool, _gr_start_tag: str, _gr_end_tag: str, _gr_bias_min: float, _gr_bias_max: float, gr_image_count: int, gr_gif_duration: int):
        """Function to collect all generated images after processing is done"""

        if self.working:
            return

        if (not gr_enabled or not gr_only_recreate_gif or len(self.stored_images) == 0) and (not gr_enabled or self.working or gr_image_count <= 0):
            # skip if not required
            return

        processed.images = self.stored_images.copy()
        processed.all_prompts = self.stored_all_prompts.copy()
        processed.infotexts = self.stored_infotexts.copy()
        processed.all_seeds = self.stored_seeds.copy()

        if len(self.stored_images) > 0 and len(self.stored_images) == gr_image_count:
            processed.images += self.create_gif(gr_gif_duration)
            processed.all_prompts += ["GIF Transition Result"]
            processed.infotexts += ["GIF Transition Result"]
            processed.all_seeds += [-1]
