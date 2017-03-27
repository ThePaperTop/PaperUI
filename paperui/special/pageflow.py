from paperui import ui
from paperui.core import chars_to_pixels

class Page(list):
    def __init__(self, x, y):
        self.height = 0
    def add(self, item):
        self.append(item)
        self.height += item.height

class PageFlow(ui.Column):
    def __init__(self, contents=list(), max_height=480):
        ui.Column.__init__(self, contents)
        
        self.max_height = max_height - 22
        
        self.pages = []
        self.current_page = 0
        self.height = max_height

    @property
    def dirty(self):
        return self.owner.dirty()

    @dirty.setter
    def dirty(self, value):
        self.owner.dirty = value

    def focus_next(self):
        self.owner.focus_next()

    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.owner.dirty = True
            if self.owner.focused_control not in self.pages[self.current_page]:
                self.owner.focus(self.pages[self.current_page][0])
        
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.owner.dirty = True
            if self.owner.focused_control not in self.pages[self.current_page]:
                self.owner.focus(self.pages[self.current_page][-1])

    def handle_key(self, char, code):
        if code in ["C-KEY_F", "KEY_F", "KEY_RIGHT"]:
            self.next_page()
        elif code in ["C-KEY_B", "KEY_B", "KEY_LEFT"]:
            self.prev_page()
        else:
            return False
        return True

    def do_layout(self, x, y, width,  height, owner=None):
        self.x = x
        self.y = y

        self.owner = owner
        self.width = width
        
        self.pages = [Page(x, y),]

        for child in self.contents:
            cur_page = self.pages[-1]
            
            if cur_page.height + child.height <= self.max_height:
                
                try:
                    child.do_layout(x,
                                    y + cur_page.height,
                                    width,
                                    height,
                                    owner=self)
                except AttributeError:
                    child.x = x
                    child.y = y + cur_page.height
                    child.width = width
                    child.owner = self
            
                cur_page.add(child)
            else:
                self.pages.append(Page(x, y))
                cur_page = self.pages[-1]

                try:
                    child.do_layout(x,
                                    y + cur_page.height,
                                    width,
                                    height,
                                    owner=self)
                except AttributeError:
                    child.x = x
                    child.y = y + cur_page.height
                    child.width = width
                    child.owner = self

                cur_page.add(child)
            
    def draw_contents(self, drawer):
        for child in self.contents:
            if child.focused:
                drawer.rectangle(self.x + 1, self.y + 1,
                                 self.width + self.x - 2,
                                 self.height + self.y - 1)

        for child in self.pages[self.current_page]:
            try:
                child.draw(drawer)
            except AttributeError:
                child.draw_contents(drawer)

        message = "(Page %s of %s)" % (self.current_page + 1,
                                     len(self.pages))

        x_offset = chars_to_pixels(len(message) + 1)
        
        drawer.text(self.width - x_offset, self.max_height, message)
