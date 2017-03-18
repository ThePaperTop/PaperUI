import math
from datetime import date, datetime
from threading import Thread

from paperui.key_events import ExclusiveKeyReader
from paperui.core import *
from enums import enum
from paperui.keyboard import KeyTranslator
from paperui.text_wrapper import TextWrapper

align = enum(left=-1, center=0, right=1)

def visible_text(text, writable_length, alignment=align.left):
    if len(text) < writable_length:
        if alignment == align.left:
            return text.ljust(writable_length)
        elif alignment == align.right:
            return text.rjust(writable_length)
        elif alignment == align.center:
            return text.center(writable_length)
    else:
        return text[0:writable_length]

class WidgetSanityError(Exception):
    pass

class Connectable(object):
    def __init__(self):
        self._events = {}
    def connect(self, event, action):
        try:
            self._events[event].append(action)
        except KeyError:
            self._events[event] = [action]
    def fire(self, event, data=None):
        try:
            for action in self._events[event]:
                try:
                    action(self.owner, self, data)
                except Exception as e:
                    print(e.message)
        except KeyError:
            pass

class Widget(Connectable, object):
    def __init__(self, name=None):
        Connectable.__init__(self)
        self.name = name
        self.focused = False
        self.x = None
        self.y = None
        self.width = None
        self.height = line_width + char_height + line_width
        self.can_focus = True
        self.owner = None
    def draw_outline(self, drawer):
        drawer.rectangle(self.x + 1, self.y + 1,
                         self.width + self.x - 2,
                         self.height + self.y - 1)
    def draw_underline(self, drawer):
        drawer.line(self.x, self.y + self.height - 1,
                    self.x + self.width - 3,
                    self.y + self.height - 1)

    def draw_text(self, drawer, text=None, alignment=align.left):
        if text == None:
            text = self.text

        text = visible_text(text,
                            pixels_to_chars(self.width - line_width * 2),
                            alignment)
            
        drawer.text(self.x + line_width,
                    self.y + line_width,
                    text)
    def redraw(self):
        self.owner.dirty = True
    def handle_key(self, char, code):
        print("Key handler not implemented yet for %s." % type(self))
    def text_value(self):
        try:
            return self.text
        except AttributeError:
            return self.items[self.selected]
        
class Container(Connectable, object):
    def __init__(self, contents=list()):
        Connectable.__init__(self)
        self.contents = contents
        self.tab_order = []
        self.owner = None
        
        for item in self.contents:
            try:
                self.tab_order = self.tab_order + item.tab_order
            except AttributeError:
                if item.can_focus:
                    self.tab_order.append(item)
                    
    def draw_contents(self, drawer):
        for child in self.contents:
            try:
                child.draw(drawer)
            except AttributeError:
                child.draw_contents(drawer)
    def control(self, name):
        for item in self.contents:
            try:
                control = item.control(name)
                if control:
                    return control
            except AttributeError:
                if item.name == name:
                    return item
        return None
    
    def focus(self, control):
        for child in self.tab_order:
            child.focused = False
                
        control.focused = True
        
        self.focused_control = control

        self.owner.dirty = True

    def focus_next(self):
        if self.focused_control == self.tab_order[-1]:
            self.focus(self.tab_order[0])
        else:
            self.focus(self.tab_order[
                self.tab_order.index(self.focused_control) + 1
            ])
        self.owner.dirty = True

    def focus_prev(self):
        if self.focused_control == self.tab_order[0]:
            self.focus(self.tab_order[-1])
        else:
            self.focus(self.tab_order[
                self.tab_order.index(self.focused_control) - 1
            ])
        self.owner.dirty=True

class Spacer(Container):
    def __init__(self, height=9, line=False):
        Container.__init__(self, [])
        self.height = height
        self.owner = None
    def draw(self, drawer):
        pass

class Label(Widget):
    def __init__(self, name=None, text="", alignment=align.left):
        Widget.__init__(self, name)
        self.text = text
        self.alignment = alignment
        self.can_focus = False
    def draw(self, drawer):
        self.draw_text(drawer)

class TextArea(Widget):
    def __init__(self, name=None, text="", rows=3, alignment=align.left):
        Widget.__init__(self, name)
        self.text = text
        self.rows = rows
        self.height = line_width + chars_to_pixels(rows, directions.y) + line_width
        self.alignment = alignment
        self.can_focus = False
        self.wrapper = TextWrapper()
    def draw(self, drawer):
        lines, row, col = self.wrapper.wrap(self.text, pixels_to_chars(self.width - line_width * 2))
        y_start = self.y + line_width
        for line in lines:
            if y_start > self.y + self.height - char_height:
                break
            drawer.text(self.x + line_width,
                        y_start,
                        line)
            y_start += char_height

    
class Button(Widget):
    def __init__(self, name=None, text="", alignment=align.center):
        Widget.__init__(self, name)
        self.text = text
        self.alignment = alignment
    def draw(self, drawer):
        self.draw_outline(drawer)
        if self.focused:
            text = "> " + self.text + " <"
        else:
            text = self.text
        self.draw_text(drawer, alignment=self.alignment, text=text)
    def handle_key(self, char, code):
        if code in ["KEY_ENTER", "KEY_SPACE"]:
            self.fire("clicked")
        

class Entry(Widget):
    def __init__(self, name=None, text="", placeholder="", password=False, alignment=align.left):
        Widget.__init__(self, name)
        self._text = text
        self.placeholder = placeholder        
        self.password = password
        self.alignment = alignment
        self.cursor_pos = len(self._text)
    @property
    def text(self):
        return self._text
    @text.setter
    def text(self, new_text):
        self._text = new_text
        if len(self.text) < self.cursor_pos:
            self.cursor_pos = len(self.text)
        self.fire("text-changed", self._text)
    def handle_key(self, char, code):
        if char:
            self.text = (self.text[:self.cursor_pos] +
                         char +
                         self.text[self.cursor_pos:])
            self.cursor_pos += 1
            self.redraw()
            return True
        elif code:
            if code == "KEY_BACKSPACE":
                if self.cursor_pos > 0:
                    self.text = (self.text[:self.cursor_pos - 1] +
                                  self.text[self.cursor_pos:])
                    self.fire("text-changed", self._text)
                    self.cursor_pos -= 1
                    self.redraw()
                return True
            elif code == "KEY_ENTER":
                self.fire("submitted")
                self.owner.focus_next()
            elif code in ["KEY_LEFT", "C-KEY_B"]:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    self.redraw()
            elif code in ["KEY_RIGHT", "C-KEY_F"]:
                if self.cursor_pos < len(self._text):
                    self.cursor_pos += 1
                    self.redraw()
            elif code in ["KEY_HOME", "C-KEY_A"]:
                self.cursor_pos = 0
                self.redraw()
            elif code in ["KEY_END", "C-KEY_E"]:
                self.cursor_pos = len(self._text)
                self.redraw()
            elif code == "C-KEY_K":
                self.text = self.text[:self.cursor_pos]
                self.redraw()
            elif code in ["KEY_DELETE", "C-KEY_D"]:
                self.text = (self.text[:self.cursor_pos] +
                              self.text[self.cursor_pos+1:])
                self.redraw()
        else:
            pass
    def draw(self, drawer):
        self.draw_underline(drawer)
        if self.text != "":
            if self.password:
                text = "*" * len(self.text)
            else:
                text = self.text
        elif self.placeholder != "":
            text="(" + self.placeholder + ")"
        else:
            text = ""

        self.draw_text(drawer, text=text)

        if self.focused:
            drawer.line(
                self.x + line_width + chars_to_pixels(self.cursor_pos),
                self.y + line_width,
                self.x + line_width + chars_to_pixels(self.cursor_pos),
                self.y + self.height - line_width)
            
class Chooser(Widget):
    def __init__(self, name=None, items=list(), placeholder="", selected=0, on_change=None, alignment=align.left):
        Widget.__init__(self, name)
        self.items = items
        self.placeholder = placeholder
        self.selected = selected
        self.on_change = on_change
        self.alignment = alignment
    def draw_interaction(self, drawer):
        if self.focused:
            drawer.rectangle(self.x,
                             15,
                             self.x + self.width - char_width - line_width * 2,
                             self.owner.height - 15,
                             fill=True)
            self.draw(drawer)

            for i in range(len(self.items)):
                text_y = self.y + chars_to_pixels(i - self.selected, directions.y) + line_width
                if 15 < text_y < 480 - 15 - char_height:
                    drawer.text(self.x + line_width, text_y, self.items[i])

    def draw(self, drawer):
        self.draw_outline(drawer)
        drawer.rectangle(self.x + self.width - char_width - line_width * 2,
                         self.y + 1,
                         self.width,
                         self.y + self.height - 1)
        drawer.text(self.x + self.width - char_width - line_width,
                    self.y,
                    "v")

        text_pos = (self.x + line_width,
                    self.y + line_width)
        display_chars = pixels_to_chars(self.width - char_width - line_width * 3)
        
        if self.selected == None:
            display_text = self.placeholder
        else:
            display_text = self.items[self.selected]
            
        drawer.text(text_pos[0],
                    text_pos[1],
                    visible_text(display_text,
                                 display_chars))

    def handle_key(self, char, code):
        if code:
            if code in ["KEY_UP", "KEY_LEFT", "C-KEY_P"]:
                if self.selected > 0:
                    self.selected -= 1
                    self.redraw()
            elif code in ["KEY_DOWN", "KEY_RIGHT", "C-KEY_N"]:
                if self.selected < len(self.items) - 1:
                    self.selected += 1
                    self.redraw()
            elif code in ["KEY_PAGEDOWN", "C-KEY_V"]:
                self.selected += pixels_to_chars(480 - 30, directions.y) - 2
                if self.selected >= len(self.items):
                    self.selected = len(self.items) - 1
                self.redraw()
            elif code in ["KEY_PAGEUP", "A-KEY_V"]:
                self.selected -= pixels_to_chars(480 - 30, directions.y) + 2
                if self.selected < 0:
                    self.selected = 0
                self.redraw()
            elif code in ["KEY_HOME", "A-S-KEY_COMMA"]:
                self.selected = 0
                self.redraw()
            elif code in ["KEY_END", "A-S-KEY_DOT"]:
                self.selected = len(self.items) - 1
                self.redraw()
            elif code == "KEY_ENTER":
                self.owner.focus_next()

class TextEdit(Widget):
    def __init__(self, name=None, text="", rows=None, allow_newlines=True):
        Widget.__init__(self, name)
        self._text = text
        self.rows = rows
        self.height = line_width + chars_to_pixels(rows, directions.y) + line_width
        self.allow_newlines = allow_newlines
        self.cursor_pos = 0
        self.cursor_loc = [0, 0]
        self.wrapper = TextWrapper()

    def wrap(self):
        self.lines, self.cursor_loc[0], self.cursor_loc[1] = self.wrapper.wrap(self._text, self.cursor_pos, pixels_to_chars(self.width - line_width * 2))
        
    def draw(self, drawer):
        self.draw_outline(drawer)

        self.wrap()

        y_start = self.y + line_width

        for line in self.lines:
            if y_start > self.y + self.height - char_height:
                break
            drawer.text(self.x + line_width,
                        y_start,
                        line)
            y_start += char_height

        if self.focused:
            drawer.line(
                self.x + chars_to_pixels(self.cursor_loc[1]) + line_width,
                self.y + chars_to_pixels(self.cursor_loc[0], directions.y) + line_width,
                self.x + chars_to_pixels(self.cursor_loc[1]) + line_width,
                self.y + chars_to_pixels(self.cursor_loc[0] + 1, directions.y) + line_width)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, newtext):
        self._text = newtext

        if len(self._text) < self.cursor_pos:
            self.cursor_pos = len(self._text)
            
        self.redraw()

    def insert_char(self, char):
        self._text = (self.text[:self.cursor_pos] +
                     char +
                     self.text[self.cursor_pos:])
        self.cursor_pos += 1
        self.redraw()

    def prev_line(self):
        self.wrap()
        if self.cursor_loc[0] > 0:
            self.cursor_pos -= len(self.lines[self.cursor_loc[0] -1])
            self.redraw()
        
    def next_line(self):
        self.wrap()
        if self.cursor_loc[0] < len(self.lines) - 1:
            self.cursor_pos += len(self.lines[self.cursor_loc[0]])
            if self.cursor_pos > len(self._text):
                self.cursor_pos = len(self._text)
            self.redraw()
            
    def handle_key(self, char, code):
        if char:
            self.insert_char(char)
            return True
        elif code:
            if code == "KEY_BACKSPACE":
                if self.cursor_pos > 0:
                    self._text = (self.text[:self.cursor_pos - 1] +
                                  self.text[self.cursor_pos:])
                    self.cursor_pos -= 1
                    self.redraw()
                    self.fire("text-changed", self._text)
                return True
            elif code == "KEY_ENTER":
                if self.allow_newlines:
                    self.insert_char("\n")
                else:
                    self.fire("submitted")
                    self.owner.focus_next()
            elif code in ["KEY_UP", "C-KEY_P"]:
                self.prev_line()
            elif code in ["KEY_DOWN", "C-KEY_N"]:
                self.next_line()
            elif code in ["KEY_LEFT", "C-KEY_B"]:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
                    self.redraw()
            elif code in ["C-KEY_LEFT", "A-KEY_B"]:
                if self.cursor_pos > 0:
                    for i in range(self.cursor_pos - 2, 0, -1):
                        if self.text[i] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
                            self.cursor_pos = i + 1
                            self.redraw()
                            break
            elif code in ["KEY_RIGHT", "C-KEY_F"]:
                if self.cursor_pos < len(self._text):
                    self.cursor_pos += 1
                    self.redraw()
            elif code in ["C-KEY_RIGHT", "A-KEY_F"]:
                if self.cursor_pos < len(self.text) - 1:
                    for i in range(self.cursor_pos + 2, len(self.text)):
                        if self.text[i] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
                            self.cursor_pos = i
                            self.redraw()
                            break
            elif code in ["KEY_HOME", "C-KEY_A"]:
                self.wrap()
                self.cursor_pos -= self.cursor_loc[1]
                self.redraw()
            elif code in ["KEY_END", "C-KEY_E"]:
                self.wrap()
                self.cursor_pos -= self.cursor_loc[1]
                self.cursor_pos += len(self.lines[self.cursor_loc[0]]) - 1
                self.redraw()
            elif code in ["C-KEY_HOME", "A-S-KEY_COMMA"]:
                self.cursor_pos = 0
                self.redraw()
            elif code in ["C-KEY_END", "A-S-KEY_DOT"]:
                self.cursor_pos = len(self._text)
                self.redraw()
            elif code == "C-KEY_K":
                self._text = self.text[:self.cursor_pos]
                self.cursor_pos = len(self.text)
                self.redraw()
            elif code in ["KEY_DELETE", "C-KEY_D"]:
                self.text = (self.text[:self.cursor_pos] +
                              self.text[self.cursor_pos+1:])
        else:
            pass
class DateTimePicker(Widget):
    def __init__(self, name=None, init_val=datetime.now(), show_date=True, show_time=False):
        Widget.__init__(self, name)
        self.init_date = init_date
        if not (show_date or show_time):
            raise WidgetSanityError("DateTimePicker must show either date or time.")
        self.show_date = show_date
        self.show_time = show_time

class Row(Container):
    def __init__(self, contents=list()):
        Container.__init__(self, contents)

    def do_layout(self, x, y, width, height, owner=None):
        self.owner = owner
        item_width = math.floor(width / len(self.contents))
        
        for child_index in range(len(self.contents)):
            child = self.contents[child_index]
            
            try:
                child.do_layout(x + item_width * child_index, y, item_width, height, owner=owner)
            except AttributeError:
                child.x = x + item_width * child_index
                child.y = y
                child.width = item_width
                child.owner = owner

        self.height = max([child.height for child in self.contents])
        self.width = width

class Column(Container):
    def __init__(self, contents=list()):
        Container.__init__(self, contents)

    def do_layout(self, x, y, width, height, owner=None):
        self.owner = owner
        self.width = width
        self.height = 0
        for child in self.contents:
            
            try:
                child.do_layout(x, y + self.height, width, height, owner=owner)
            except AttributeError:
                child.x = x
                child.y = y + self.height
                child.width = width
                child.owner = owner
                
            self.height += child.height

class Popup(Column):
    def __init__(self, width, height, contents=list(), owner=None):
        Column.__init__(self, contents=contents)
        self.width = width
        self.height = height
        self.owner = owner
        try:
            self.focus(self.tab_order[0])
        except AttributeError:
            pass

    def do_layout(self, x, y, width, height, owner=None):
        self.owner = owner
        self.x = math.floor(owner.width / 2 - self.width / 2)
        self.y = math.floor(owner.height / 2 - self.height / 2)
        
        Column.do_layout(self, self.x, self.y, self.width, self.height, owner=self)

    def draw_contents(self, drawer):
        drawer.rectangle(self.x + 1, self.y + 1,
                         self.width + self.x - 2,
                         self.height + self.y - 1)
        Container.draw_contents(self, drawer)
        try:
            self.focused_control.draw_interaction(drawer)
        except AttributeError:
            pass

        
        
class Form(Container):
    def __init__(self, *contents, **kwargs):
        Container.__init__(self, contents)
        self.key_translator = KeyTranslator()

        try:
            self.debug = kwargs["debug"]
        except KeyError:
            self.debug = False
        
        try:
            self.width = kwargs["width"]
        except KeyError:
            self.width = 800
        
        try:
            self.height = kwargs["height"]
        except KeyError:
            self.height = 480

        self.do_layout()

        self.finished = False
        self.focus(self.tab_order[0])

        self._dirty = True
        self._dirty_time = datetime.fromordinal(1)
        self._last_draw = datetime.fromordinal(1)

        self._popup = None
        self._show_popup = False

    @property
    def popup(self):
        return self._popup

    @popup.setter
    def popup(self, new_popup):
        new_popup.do_layout(0, 0, self.width, self.height, self)
        self._popup = new_popup

    @property
    def show_popup(self):
        return self._show_popup

    @show_popup.setter
    def show_popup(self, value):
        if value and not self._popup:
            raise Exception("Form has no popup to show.")
            
        if value != self._show_popup:
            self.dirty = True    
        
        self._show_popup = value
        
    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value=True):
        self._dirty = value
        self._dirty_time = datetime.now()

    def finish(self):
        self.finished = True
        self.keyboard.stop()
        
    def do_layout(self):
        self.owner = self
        next_y = 0

        for child in self.contents:
            try:
                child.do_layout(0, next_y, self.width, self.height, owner=self)
            except AttributeError:
                child.x = 0
                child.y = next_y
                child.width = self.width
                child.owner = self
                
            next_y += child.height

    def _time_to_redraw(self):
        if self.debug:
            return True
        else:
            return ((datetime.now() - self._dirty_time).total_seconds() > 0.75 or
                    (datetime.now() - self._last_draw).total_seconds() > 5.75)
    def _draw(self, drawer):
        while not self.finished:
            if self.dirty and self._time_to_redraw():
                self.dirty = False
                self._last_draw = datetime.now()
                drawer.new_screen()
                self.draw_contents(drawer)
                try:
                    self.focused_control.draw_interaction(drawer)
                except AttributeError:
                    pass

                if self.show_popup:
                    self.popup.draw_contents(drawer)
                
                drawer.send()
        exit()

    def draw(self, drawer):
        display_thread = Thread(target=self._draw,
                                args=(drawer,))
        display_thread.daemon = True
        display_thread.start()

    def handle_key(self, keycode, keystate):
        char, code = self.key_translator.translate(keycode, keystate)

        focused_form = self.show_popup and self.popup or self
            
        if code == "KEY_F12":
            self.finish()
        elif code == "KEY_PAUSE":
            exit()
        elif char == "\t":
            focused_form.focus_next()
        elif code == "S-KEY_TAB":
            focused_form.focus_prev()
        elif char or code:
            focused_form.focused_control.handle_key(char, code)

    def run(self, keyboard, screen):
        self.keyboard = keyboard
        self.drawer = screen
        self.draw(screen)
        keyboard.event_loop(self.handle_key)
