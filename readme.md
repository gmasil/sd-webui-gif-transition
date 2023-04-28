# Stable Diffusion GIF Transition

A [stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) addon to generate gifs with a transition.

## Example Result

![example](images/example.webp "Example")

## Install

1. Open "Extensions" tab
2. Click on "Install from URL"
3. Copy `https://github.com/gmasil/sd-webui-gif-transition.git` into "URL for extension's git repository"
4. Click on "Install"
5. Under "Installed" click on "Apply and restart UI"

## Usage

You can add two tags/words that are gradually transitioned between. The minimum and maximum bias of the tags have an impact on the amount of change from first to last frame. Then you can select the amount of frames you want to generate and the total duration of the animation in ms.

![settings](images/settings.png "Settings")

The settings above will generate a ~~gif~~ webp with 12 frames and a total animation length of 1.2 seconds.

The prompt of the first frame will be prepended by `(short hair:1.4), (long hair: 0.6)` and the last frame by `(short hair:0.6), (long hair: 1.4)` with a linear transition in between the frames.

### Animation Types

Currently the animation types **gif**, **webp** and **mp4** are supported. While gif and webp files can be created out of the box, you have to have [ffmpeg](https://ffmpeg.org/) installed and available in your path to create mp4 videos.

Note: Currently it is not possible to show or play the mp4 video in your browser directly. Inside stable diffusion you will see a broken image in the output gallery. You have to right click and select download image, then you can play it with any video player of your likings.

### Recreate Animation

If you want to change the animation duration or the type of animation (gif, webp, mp4) you can check `Only recreate gif/webp` and click the generate button again. This time no image is generated, but the images from the last run are used to create the animation. This way you can quickly adjust the speed of the animation or create a webp in addition to a gif.

### Transition Tags Positioning
 
The transition tags are placed at the beginning by default. This is not ideal, because they receive a higher precedence as they should in some cases. Placing them at the end by default would result in very weak transitions.

Now you are able to select the position of the inserted tags by adding the placeholder `$transition` where you want the tags to appear, for example:

```
realistic, 1girl, $transition, brown hair
```

This would result in:

```
realistic, 1girl, (short hair:1.4), (long hair: 0.6), brown hair
```

If the transition tags were placed at the beginning they would appear in front of some generic tags usually placed at the beginning (`photorealistic, render, hdr` etc.) and result in a significantly worse transition.

### Transition Multiple Tags

Multiple tags seperated by comma are supported as well:

![example](images/example2.webp "Example")

Here as a start tag `cute face, blue eyes` is used, end tag is `demon, red eyes`.

## Development

To get better autocompletion add a `.env` file to the root of this repo and specify the location of your cloned [stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) repository:

```
PYTHONPATH="E:\\AI\\stable-diffusion-webui"
```

Check types with

```bash
mypy .
```

and order imports with

```bash
isort .
```

Run tests using

```bash
python -m unittest tests/test_*.py
```

## License

[GNU GPL v3 License](LICENSE.md)

GIF Transition is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

GIF Transition is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
