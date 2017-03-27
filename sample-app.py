import os
import sys
from sqlite3 import connect
from paperui.ui import *
from paperui.special.pageflow import PageFlow

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

form = Form(PageFlow(
    contents=[Button(text=text,
                     name="test-button")
              for text in
              "Here is a whole bunch of text that I'll split up by space until I have enough buttons to fill more than one page. I think that will work out well for me.".split(" ")]))

form.control("test-button").connect("clicked",
                                    lambda f, c, data: form.finish())

# if we're on x86[_64], we're on my laptop?  TODO: make this portable
# to other machines
if "x86" in os.popen("uname -m").read():
    keyboard = "/dev/input/event4"
else:
    keyboard = "/dev/input/event0"
    
with ExclusiveKeyReader(keyboard) as keyboard:
    form.run(keyboard, drawer)
