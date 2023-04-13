"""Module to generate animated webp image from set of images"""
import os
import webptools

webptools.grant_permission()


def convert_to_webp(images: list[str]) -> list[str]:
    """Function to convert a list of images (path to file) to webp images without animation. Function returns a list of new filenames"""
    webp_images: list[str] = []
    for image in images:
        new_name: str = f"{image}.webp"
        webptools.cwebp(input_image=image, output_image=new_name, option="-q 90", logging="-v")
        webp_images += [new_name]
    return webp_images


def set_image_timings(images: list[str], animation_duration: int) -> list[str]:
    """Function to set image timings for animated webp creation"""
    duration: int = animation_duration // len(images)
    timings: list[str] = []
    for image in images:
        timings += [f"{image} +{duration}"]
    return timings


def create_webp(images: list[str], animation_duration: int, output_file: str):
    """Create an animated webp image """
    webp_images: list[str] = convert_to_webp(images)
    image_timings: list[str] = set_image_timings(webp_images, animation_duration)
    webptools.webpmux_animate(input_images=image_timings, output_image=output_file, loop=0, bgcolor="255,255,255,255")
    print(f"webp_images size = {len(webp_images)}")
    for webp_image in webp_images:
        print(f"checking {webp_image}")
        if os.path.isfile(webp_image):
            print(f"deleting {webp_image}")
            os.remove(webp_image)
