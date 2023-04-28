"""Module to prepare and build prompts including transition tags"""

from typing import List, Tuple


class PromptBuilder:
    """Class to prepare and build prompts including transition tags"""

    def prepare_prompt(self, prompt: str) -> Tuple[str, str]:
        """Function to prepare prompt, acts as entrypoint on where to place transition tags"""
        if "$transition" in prompt:
            prefix, suffix = prompt.split("$transition")
        else:
            prefix = ""
            suffix = f", {prompt}"
        return prefix, suffix

    def map_from_to(self, value: float, source_min: float, source_max: float, target_min: float, target_max: float) -> float:
        """Function to map a value from a source range to a target range"""
        mapped: float = (value-source_min)/(source_max-source_min)*(target_max-target_min)+target_min
        return round(mapped, 2)

    def build_prompts(self, original_prompt: str, start_tag: str, end_tag: str, bias_min: float, bias_max: float, image_count: int) -> List[str]:
        """Function to build SD prompts with a linear transition from start_tag to end_tag"""
        image_count = int(image_count)
        prompts = []
        prefix, suffix = self.prepare_prompt(original_prompt)
        for i in range(image_count):
            first_bias = self.map_from_to((image_count-1-i) / (image_count-1), 0, 1, bias_min, bias_max)
            second_bias = self.map_from_to(i / (image_count-1), 0, 1, bias_min, bias_max)
            prompts.append(f"{prefix}({start_tag}:{first_bias}), ({end_tag}:{second_bias}){suffix}")
        return prompts
