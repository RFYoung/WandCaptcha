# WandCaptcha

A python image CAPCTCHA generator based on wand.

This project is modified from [captcha](https://github.com/lepture/captcha/), with the image processing library changed
to [wand](https://github.com/emcconville/wand).

The project is still in the preliminary development stage.

To run this code, you need to find a copy of "Roboto-Regular.ttf" font (may
from [google fonts](https://fonts.google.com/specimen/Roboto)) and put it under the `font` directory, or provide
the `fonts` argument when initiating WandCaptcha.

For example:

```python
from WandCaptcha import WandCaptcha

captcha = WandCaptcha(fonts=['/path/to/FontA.ttf', '/path/to/FontB.ttf'])
captcha.write("textBody", "demo.png")
```

### TODO:

- [ ] Roughly revise the project and fix small bugs
- [ ] Implement other text-based captcha enhance method, like some
  from [Text-based captcha strengths and weaknesses](https://elie.net/publication/text-based-captcha-strengths-and-weaknesses/)
