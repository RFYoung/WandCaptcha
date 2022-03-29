import os
import random
from io import BytesIO
from itertools import chain

from wand.color import Color
from wand.drawing import Drawing
from wand.font import Font
from wand.image import Image

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'font')
DEFAULT_FONTS = [os.path.join(DATA_DIR, 'Roboto-Regular.ttf')]


class WandCaptcha(object):

    def __init__(self, width=160, height=60, fonts=None, font_sizes=None):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS
        self._font_sizes = font_sizes or (42, 50, 56)
        self._truefonts = []

    @property
    def truefonts(self):
        if self._truefonts:
            return self._truefonts
        self._truefonts = tuple([
            Font(path=n, size=s)
            for n in self._fonts
            for s in self._font_sizes
        ])
        return self._truefonts

    def generate(self, chars, format='png'):
        """Generate an Image Captcha of the given characters.

        :param chars: text to be generated.
        :param format: image file format
        """
        with self.generate_image(chars) as im:
            out = BytesIO()
            im.format = format
            im.save(file=out)
            out.seek(0)
            return out

    def write(self, chars, output, format='png'):
        """Generate and write an image CAPTCHA data to the output.

        :param chars: text to be generated.
        :param output: output destination.
        :param format: image file format
        """
        with self.generate_image(chars) as im:
            im.format = format
            return im.save(filename=output)

    def generate_image(self, chars):
        """Generate the image of the given characters.

        :param chars: text to be generated.
        """
        background = self.random_color(238, 255)
        color = self.random_color(10, 200, random.randint(220, 255))
        im = self.create_captcha_image(chars, color, background)
        self.create_noise_dots(im, color)
        self.create_noise_curve(im, color)
        # im.gaussian_blur(sigma=1)
        return im

    @staticmethod
    def random_color(start, end, opacity=None):
        red = random.randint(start, end)
        green = random.randint(start, end)
        blue = random.randint(start, end)
        return Color("rgba({},{},{},{})".format(red, green, blue, (opacity or 1)))

    @staticmethod
    def create_noise_dots(image: Image, color: Color, width=3, number=30):
        w, h = image.size
        with Drawing() as draw:
            draw.stroke_color = color
            draw.stroke_width = width
            while number:
                x1 = random.randint(0, w)
                y1 = random.randint(0, h)
                draw.line((x1, y1), (x1 - 1, y1 - 1))
                number -= 1
            draw(image)
        return image

    @staticmethod
    def create_noise_curve(image: Image, color: Color):
        w, h = image.size
        x1 = random.randint(0, int(w / 5))
        x2 = random.randint(w - int(w / 5), w)
        y1 = random.randint(int(h / 5), h - int(h / 5))
        y2 = random.randint(y1, h - int(h / 5))
        end = random.randint(160, 200)
        start = random.randint(0, 20)
        with Drawing() as draw:
            draw.stroke_width = 2
            draw.stroke_color = color
            draw.fill_color = Color("transparent")
            draw.arc(start=(x1, y1), end=(x2, y2), degree=(start, end))
            draw(image)
        return image

    def create_captcha_image(self, chars: str, color, background):
        image = Image(width=self._width, height=self._height, background=background)

        def _draw_character(c: str, ori_im):
            font = random.choice(self.truefonts)
            with Drawing() as draw:
                draw.font = font.path
                draw.font_size = font.size
                draw.fill_color = color
                draw.font_weight = 400
                metrics = draw.get_font_metrics(ori_im, c, False)
                text_w = metrics.text_width
                text_h = metrics.text_height
                ascender = metrics.ascender
                draw.clear()

            im = Image(width=int(text_w), height=int(text_h), background=Color('transparent'))
            with Drawing() as draw:
                draw.font = font.path
                draw.font_size = font.size
                draw.fill_color = color
                draw.font_weight = 400
                draw.text(x=0, y=int(ascender), body=c)
                draw(im)
                draw.clear()

            # trim blank space
            im.trim()

            # get trimmed size
            w = im.width
            h = im.height

            # add random blank boarder
            im.background_color = 'transparent'
            dx = random.randint(-2, 2)
            dy = random.randint(-3, 3)
            im.extent(width=im.width + abs(dx) + 2, height=im.height + abs(dy) + 2, x=dx, y=dy)

            # rotate
            im.rotate(random.uniform(-30, 30))

            # warp
            dx = w * random.uniform(0.1, 0.3)
            dy = h * random.uniform(0.2, 0.3)
            x1 = int(random.uniform(-dx, dx))
            y1 = int(random.uniform(-dy, dy))
            x2 = int(random.uniform(-dx, dx))
            y2 = int(random.uniform(-dy, dy))
            w2 = w + abs(x1) + abs(x2)
            h2 = h + abs(y1) + abs(y2)
            source_points = (
                (0, 0),
                (0, h),
                (w, h),
                (w, 0)
            )
            destination_points = (
                (x1, y1),
                (-x1, h2 - y2),
                (w2 + x2, h2 + y2),
                (w2 - x2, -y1)
            )
            order = chain.from_iterable(zip(source_points, destination_points))
            data = list(chain.from_iterable(order))

            im.sample(width=w2, height=h2)
            im.distort("bilinear_forward", data)
            return im

        images = []
        for c in chars:
            if random.random() > 0.5:
                images.append(_draw_character(" ", image))
            images.append(_draw_character(c, image))

        text_width = sum([im.width for im in images])

        width = max(text_width, self._width)
        image.resize(width, self._height)

        average = int(text_width / len(chars))
        rand = int(0.25 * average)
        offset = int(average * 0.1)

        for im in images:
            w, h = im.size
            # code that has not been implemented (from captcha.ImageCaptcha)
            # im.transform_colorspace('gray')
            # mask = im.convert('L').point(table)
            image.composite(im, left=offset, top=int((self._height - h) / 2))
            offset = offset + w + random.randint(-rand, 0)

        if width > self._width:
            image.resize(self._width, self._height)

        return image
