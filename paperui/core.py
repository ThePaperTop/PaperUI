import os
import math

try:
    from pervasive import PervasiveDisplay
except ImportError:
    # this will allow derived classes that do not depend on
    # PervasiveDisplay
    def PervasiveDisplay():
        return None

from PIL import Image, ImageFont, ImageDraw
from pil2epd import convert
from fc_list import FontList
from enums import enum

directions = enum(x=0, y=1)

char_width = 9.0
char_height = 18.0
line_width = 4.0

def chars_to_pixels(chars, direction=directions.x):
    if direction == directions.x:
        return chars * char_width
    elif direction == directions.y:
        return chars * char_height
    else:
        raise Exception("Direction must be x or y.")

def pixels_to_chars(pixels, direction=directions.x):
    if direction == directions.x:
        return math.floor(pixels / char_width)
    elif direction == directions.y:
        return math.floor(pixels / char_height)
    else:
        raise Exception("Direction must be x or y.")

class ScreenDrawer(object):
    def __init__(self, width=800, height=480):
        self.screen = None
        self.size = (width, height)

        try:
            font = FontList.all().by_partial_name("roboto mono").bold()[0]
        except IndexError:
            raise Exception("You must install the Roboto Mono font.")
        
        self.font = ImageFont.truetype(font["path"], size=15)
        self.display = PervasiveDisplay()
    def columns(self):
        return pixels_to_chars(self.size[0], directions.x)
    def rows(self):
        return pixels_to_chars(self.size[1], directions.y)
    def new_screen(self):
        self.screen = Image.new("1",
                                self.size,
                                1)
        self._drawer = ImageDraw.Draw(self.screen)
    def text(self, x, y, text):
        self._drawer.text((x, y), text, font=self.font)
    def rectangle(self, x, y, x1, y1, fill=False):
        self._drawer.rectangle([x, y, x1, y1],
                               outline=0,
                               fill=fill and 0 or 1)
    def line(self, x, y, x1, y1):
        self._drawer.line([x, y, x1, y1])
    def image(self, x, y, image):
        self.screen.paste(image, (x, y))
    def clear(self):
        self.new_screen()
        self.send()
    def epd(self):
        return convert(self.screen)
    def screenshot(self, fn):
        self.screen.save(fn)
    def send(self):
        self.screen = self.screen.rotate(270)
        self.display.reset_data_pointer()
        self.display.send_image(self.epd())
        self.display.update_display()
