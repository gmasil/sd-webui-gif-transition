import os
import uuid
import gradio as gr
import modules.scripts as scripts
from modules.shared import state
from modules.processing import process_images, fix_seed


def map_from_to(x: int, a: int, b: int, c: int, d: int) -> float:
    y = (x-a)/(b-a)*(d-c)+c
    return round(y, 2)


def build_prompts(original_prompt: str, start_tag: str, end_tag: str, bias_min: float, bias_max: float, image_count: int) -> list[str]:
    image_count = int(image_count)
    prompts = []
    for i in range(image_count):
        first_bias = map_from_to((image_count-1-i) / (image_count-1), 0, 1, bias_min, bias_max)
        second_bias = map_from_to(i / (image_count-1), 0, 1, bias_min, bias_max)
        prompts.append(f"({start_tag}:{first_bias}), ({end_tag}:{second_bias}), {original_prompt}, ")
    return prompts


def make_gif(frames, filename=None, frame_duration=100):
    if filename is None:
        filename = str(uuid.uuid4())

    outpath = "/output/gif-transition"
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    first_frame, append_frames = frames[0], frames[1:]
    first_frame.save(f"{outpath}/{filename}.gif", format="GIF", append_images=append_frames, save_all=True, duration=frame_duration, loop=0)
    return first_frame


class GifTransitionExtension(scripts.Script):
    def __init__(self):
        super().__init__()
        self.working: bool = False
        self.stored_images = []
        self.stored_all_prompts = []
        self.stored_infotexts = []

    def title(self):
        return "GIF Transition"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        with gr.Group():
            with gr.Accordion("GIF Transition", open=False, elem_id="giftransition"):
                with gr.Row():
                    gr_enabled: bool = gr.Checkbox(label='Enable', value=False)
                with gr.Row():
                    gr_start_tag: str = gr.Textbox(label="Start tag", value="short hair")
                    gr_end_tag: str = gr.Textbox(label="End tag", value="long hair")
                with gr.Row():
                    gr_bias_min: float = gr.Number(label="Bias min", value=0.6)
                    gr_bias_max: float = gr.Number(label="Bias max", value=1.4)
                with gr.Row():
                    gr_image_count: int = gr.Number(label="Amount of frames", value=12)
                    gr_gif_duration: int = gr.Number(label="Total animation duration (in ms)", value=1000)

        return [gr_enabled, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count, gr_gif_duration]

    def process(self, p, gr_enabled: bool, gr_start_tag: str, gr_end_tag: str, gr_bias_min: float, gr_bias_max: float, gr_image_count: int, gr_gif_duration: int):
        if not gr_enabled or self.working:
            return

        gr_image_count = int(gr_image_count)

        if gr_image_count <= 0:
            return

        self.working = True
        self.stored_images = []
        self.stored_all_prompts = []
        self.stored_infotexts = []

        p.batch_size = 1
        p.n_iter = 1

        original_prompt = p.prompt.strip().rstrip(',')
        frame_prompts = build_prompts(original_prompt, gr_start_tag, gr_end_tag, gr_bias_min, gr_bias_max, gr_image_count)

        fix_seed(p)

        state.job_count = len(frame_prompts)

        for i in range(len(frame_prompts)):
            if state.interrupted:
                return

            p.prompt = frame_prompts[i]
            proc = process_images(p)

            if state.interrupted:
                return

            self.stored_images += proc.images
            self.stored_all_prompts += proc.all_prompts
            self.stored_infotexts += proc.infotexts

        # remove pose images of ControlNet if present
        if len(frame_prompts) * 2 == len(self.stored_images):
            del self.stored_images[1::2]

        frame_duration: int = int(gr_gif_duration/len(frame_prompts))
        make_gif(self.stored_images, frame_duration=frame_duration)

        self.working = False
        p.n_iter = 0

    def postprocess(self, p, processed, gr_enabled: bool, gr_start_tag: str, gr_end_tag: str, gr_bias_min: float, gr_bias_max: float, gr_image_count: int, gr_gif_duration: int):
        if not gr_enabled or self.working:
            return
        processed.images = self.stored_images
        processed.all_prompts = self.stored_all_prompts
        processed.infotexts = self.stored_infotexts
