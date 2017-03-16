import sys
from sqlite3 import connect
from paperui.ui import *

from paperui.core import *
from paperui.fb import FrameBufferDrawer

if "--debug" in sys.argv[1:]:
    debug = True
else:
    debug = False

if debug:
    drawer =  FrameBufferDrawer()
else:
    drawer = ScreenDrawer()

entry_form = Form(
    Row(contents=[Label(text="First name"),
                  Entry(name="first-name")]),
    Row(contents=[Label(text="Last name"),
                  Entry(name="last-name")]),
    Row(contents=[
        Label(text="Security question"),
        Chooser(name="security-question",
                items=["Mother's maiden name",
                       "City of birth",
                       "First pet's name",
                       "First car"])]),
    Row(contents=[Label(text="Answer"),
                  Entry(name="security-answer",
                        password=True)]),
    Label(text="Bio"),
    TextEdit(name="bio", rows=12),
    Spacer(height=10, line=True),
    Row(contents=[Button(text="Save",
                         name="save-button"),
                  Button(text="Done",
                         name="done-button")]),
    debug=debug,
    width=drawer.size[0],
    height=drawer.size[1])

summary_form = Form(
    Label(text="Entries"),
    TextArea(text="",
             name="display-area",
             rows=18),
    Button(text="Done",
           name="done-button"),
    debug=debug,
    width=drawer.size[0],
    height=drawer.size[1])

conn = connect("test.db")
cur = conn.cursor()

try:
    cur.execute("create table data (first_name text, last_name text, question text, answer text, bio text);")
    conn.commit()
except:
    pass

def save_data(f, c, data):
    (fn, ln, q, a, bio) = (entry_form.control("first-name").text_value(),
                           entry_form.control("last-name").text_value(),
                           entry_form.control("security-question").text_value(),
                           entry_form.control("security-answer").text_value(),
                           entry_form.control("bio").text_value())

    cur.execute("insert into data (first_name, last_name, question, answer, bio) values (?, ?, ?, ?, ?);",
                (fn, ln, q, a, bio))
    conn.commit()
    
    entry_form.control("first-name").text = ""
    entry_form.control("last-name").text = ""
    entry_form.control("security-question").selected = 0
    entry_form.control("security-answer").text = ""
    entry_form.control("bio").text = ""
    
    entry_form.focus(entry_form.control("first-name"))

def close_form(f, c, data):
    f.finish()

def next_form(f, c, data):
    f.finish()
    
    
entry_form.control("save-button").connect("clicked", save_data)
entry_form.control("done-button").connect("clicked", close_form)
summary_form.control("done-button").connect("clicked", close_form)
summary_form.control("done-button").connect("clicked", lambda f, c, data: f.drawer.clear())

tmpl = """%s %s
%s: %s
%s"""

from enums import enum

modes = enum(normal=0, debug=1)

class App(object):
    def __init__(self,
                 main_form,
                 keyboard_device="/dev/input/event0",
                 mode=modes.normal):

        self.main_form = main_form
        
        self.keyboard = ExclusiveKeyReader(keyboard_device)
        self.mode = mode
        
        if self.mode == modes.debug:
            self.drawer =  FrameBufferDrawer()
        else:
            self.drawer = ScreenDrawer()

    def run(self, form=None):
        
        if not form:
            form = self.main_form
            
        form.run(self.keyboard, self.drawer)

with ExclusiveKeyReader("/dev/input/event0") as keyboard:

    entry_form.run(keyboard, drawer)
    
    cur.execute("select * from data")
    rows = cur.fetchall()
    
    summary_form.control("display-area").text = "\n".join([tmpl % row
                                                           for row in rows])
    summary_form.run(keyboard, drawer)
