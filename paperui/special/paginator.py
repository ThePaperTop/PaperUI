from PIL import Image, ImageFont, ImageDraw
from enums import enum
from paperui import ui
from paperui.core import *
from threading import Thread
import math

orientations = enum(landscape=0,
                    portrait=1)

class Line(object):
    def __init__(self, text, size):
        self.text = text
        self.size = size

class Page(list):
    def __init__(self, size):
        list.__init__(self)
        self.size = size
        if self.size[0] < self.size[1]:
            self.orientation = orientations.portrait
        else:
            self.orientation = orientations.landscape
    def to_image(self, font, margin):
        image = Image.new("1", self.size, 1)
        drawer = ImageDraw.Draw(image)

        x, y = margin, 0

        for line in self:
            drawer.text((x, y),
                        line.text,
                        font=font)
            y += line.size[1]
                
        return image
    
    def to_string(self):
        return "\n".join([line.text
                          for line in self])
        
def max_char_width(font):
    max_width = 0
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-={}[]\\|:;\"'<>,.~`":
        width = font.getsize(c)[0]
        if width > max_width:
            max_width = width

    return max_width

class Paginator(object):
    def __init__(self, font, size, margin=20):
        self.font = font
        self.max_char_width = max_char_width(self.font)
        self.size = size
        self.pages = []
        self.page = Page(self.size)
        self.margin = margin
        self.finished = False
    def wrap(self, line):
        max_width = self._page_size()[0] - self.margin * 2
        
        lines = []

        if line:
            words = line.strip().split(" ")
        else:
            words = [" "]
        
        acc = []
        lastsize, newsize = (0, 0), (0, 0)

        for word in words:
            # if the line would fit if all characters were as big as
            # the widest, just add the word
            if len(" ".join(acc + [word])) < math.floor(self.size[0] / self.max_char_width):
                acc.append(word)
            else:
                # otherwise, test for fit
                newsize = self.font.getsize(" ".join(acc + [word]))
                if newsize[0] > max_width:
                    offsets = self.font.getoffset(" ".join(acc))
                    lastsize = (lastsize[0], lastsize[1] + offsets[1])
                    lines.append(Line(" ".join(acc), lastsize))
                    acc = [word]
                    lastsize, newsize = (0,0), (0,0)
                else:
                    acc.append(word)
                    lastsize = newsize

        if acc: # if there is a partial line left
            lines.append(Line(" ".join(acc),
                              self.font.getsize(" ".join(acc))))

        return lines

    def _new_page(self):
        self.page = Page(self._page_size())

    def _page_size(self):
        return (math.floor(self.size[0] - line_width * 2),
                math.floor(self.size[1] - line_width * 2))

    def paginate(self, text):
        self._new_page()
        self.finished = False
        
        y = 0

        for line in text.split("\n"):
            for row in self.wrap(line):
                text, size = row.text, row.size
                if y + size[1] > self._page_size()[1]:
                    self.pages.append(self.page)
                    self._new_page()
                    self.page.append(row)
                    y = size[1]
                else:
                    y += size[1]
                    self.page.append(row)

        if self.page.to_string():
            self.pages.append(self.page)

        self.finished = True

class PaginatorWidget(Paginator, ui.Widget):
    def __init__(self, font, name=None, text="", rows=3, margin=20):
        height = math.floor(ui.char_height * rows + ui.line_width * 2)
        width = 800

        Paginator.__init__(self, font, [width, height], margin)
        ui.Widget.__init__(self, name=name)

        self.size = [width, height]
        self._text = ""
        self.text = text

    def begin_pagination(self):
        paginate_thread = Thread(target=self.paginate,
                                 args=[self._text],
                                 daemon=True)
        paginate_thread.start()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.page_index = 0
        self.begin_pagination()

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, value):
        if value and value != self.size[0]:
            self.size[0] = value
            self.begin_pagination()
        
    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, value):
        self.size[1] = value

    def prev_page(self):
        if self.page_index > 0:
            self.page_index -= 1
            self.redraw()

    def next_page(self):
        if self.page_index < len(self.pages) - 1:
            self.page_index += 1
            self.redraw()

    def first_page(self):
        self.page_index = 0
        self.redraw()

    def last_page(self):
        self.page_index = len(self.pages) - 1
        self.redraw()
        
    def handle_key(self, char, code):
        if code == "KEY_LEFT":
            self.prev_page()
        elif code == "KEY_RIGHT":
            self.next_page()
        elif code in ["C-KEY_LEFT", "KEY_HOME", "C-KEY_HOME"]:
            self.first_page()
        elif code in ["C-KEY_RIGHT", "KEY_END", "C-KEY_END"]:
            self.last_page()
        
    def draw(self, drawer):
        self.draw_outline(drawer)
        
        while len(self.pages) <= self.page_index:
            pass

        try:

            page_image = self.pages[self.page_index].to_image(
                font=self.font,
                margin=self.margin)

            drawer.image(math.floor(self.x + line_width),
                         math.floor(self.y + line_width),
                         page_image)

        except IndexError:
            pass


if __name__ == "__main__":
    import sys, codecs
    from fontlist import FontList
    
    fonts = FontList.all().by_partial_name("dejavu serif").regular()
    font = ImageFont.truetype(fonts[1]["path"])
    paginator = Paginator(font, (800, 480))
    text = codecs.open(sys.argv[1], "r", "utf-8").read()
    paginator.paginate(text)
    print(len(paginator.pages))
