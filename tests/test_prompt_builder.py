import unittest

from scripts.prompt_builder import PromptBuilder


class TestPromptBuilder(unittest.TestCase):

    def test_prompt_preparation_standard(self):
        prompt_builder = PromptBuilder()
        prefix, suffix = prompt_builder.prepare_prompt("realistic, 1girl, brown hair")
        self.assertEqual(prefix, "")
        self.assertEqual(suffix, ", realistic, 1girl, brown hair")

    def test_prompt_preparation_split(self):
        prompt_builder = PromptBuilder()
        prefix, suffix = prompt_builder.prepare_prompt("realistic, 1girl, $transition, brown hair")
        self.assertEqual(prefix, "realistic, 1girl, ")
        self.assertEqual(suffix, ", brown hair")

    def test_standard(self):
        prompt_builder = PromptBuilder()

        original_prompt = "realistic, 1girl, brown hair"
        start_tag = "short hair"
        end_tag = "long hair"
        bias_min = 0.4
        bias_max = 1.6
        image_count = 5
        prompts = prompt_builder.build_prompts(original_prompt, start_tag, end_tag, bias_min, bias_max, image_count)

        expected_prompts = ['(short hair:1.6), (long hair:0.4), realistic, 1girl, brown hair',
                            '(short hair:1.3), (long hair:0.7), realistic, 1girl, brown hair',
                            '(short hair:1.0), (long hair:1.0), realistic, 1girl, brown hair',
                            '(short hair:0.7), (long hair:1.3), realistic, 1girl, brown hair',
                            '(short hair:0.4), (long hair:1.6), realistic, 1girl, brown hair']

        self.assertEqual(prompts, expected_prompts)

    def test_replace(self):
        prompt_builder = PromptBuilder()

        original_prompt = "realistic, 1girl, $transition, brown hair"
        start_tag = "short hair"
        end_tag = "long hair"
        bias_min = 0.4
        bias_max = 1.6
        image_count = 5
        prompts = prompt_builder.build_prompts(original_prompt, start_tag, end_tag, bias_min, bias_max, image_count)

        expected_prompts = ['realistic, 1girl, (short hair:1.6), (long hair:0.4), brown hair',
                            'realistic, 1girl, (short hair:1.3), (long hair:0.7), brown hair',
                            'realistic, 1girl, (short hair:1.0), (long hair:1.0), brown hair',
                            'realistic, 1girl, (short hair:0.7), (long hair:1.3), brown hair',
                            'realistic, 1girl, (short hair:0.4), (long hair:1.6), brown hair']

        self.assertEqual(prompts, expected_prompts)


if __name__ == '__main__':
    unittest.main()
