from enums import enum

keystates = enum(down=1, up=0, hold=2)

buckies = ["KEY_LEFTSHIFT", "KEY_RIGHTSHIFT",
           "KEY_LEFTCTRL", "KEY_RIGHTCTRL",
           "KEY_CAPSLOCK", "KEY_LEFTALT", "KEY_RIGHTALT"]

alphabet = "abcdefghijklmnopqrstuvwxyz"
numeric_keys = "0123456789)!@#$%^&*("
char_keys = {
    "KEY_GRAVE": "`",
    "S-KEY_GRAVE": "~",
    "KEY_SPACE": " ",
    "KEY_MINUS": "-",
    "S-KEY_MINUS": "_",
    "KEY_EQUAL": "=",
    "S-KEY_EQUAL": "+",
    "KEY_SEMICOLON": ";",
    "S-KEY_SEMICOLON": ":",
    "KEY_APOSTROPHE": "'",
    "S-KEY_APOSTROPHE": '"',
    "KEY_COMMA": ",",
    "S-KEY_COMMA": "<",
    "KEY_DOT": ".",
    "S-KEY_DOT": ">",
    "KEY_SLASH": "/",
    "S-KEY_SLASH": "?",
    "KEY_LEFTBRACE": "[",
    "S-KEY_LEFTBRACE": "{",
    "KEY_RIGHTBRACE": "]",
    "S-KEY_RIGHTBRACE": "}",
    "KEY_BACKSLASH": "\\",
    "S-KEY_BACKSLASH": "|",
    "KEY_TAB": "\t"
}

for c in alphabet:
    char_keys["KEY_%s" % c.upper()] = c
    char_keys["S-KEY_%s" % c.upper()] = c.upper()

for i in range(10):
    char_keys["KEY_%s" % i] = numeric_keys[i]
    char_keys["S-KEY_%s" % i] = numeric_keys[i+10]

class KeyTranslator(object):
    def __init__(self):
        self.alt, self.ctrl, self.shift = False, False, False
    def _prefix(self):
        return "%s%s%s" % (self.alt and "A-" or "",
                           self.ctrl and "C-" or "",
                           self.shift and "S-" or "")
    def translate(self, keycode, keystate):
        if keycode in buckies:
            if keystate in [keystates.down, keystates.up]:
                if keycode in ["KEY_LEFTSHIFT", "KEY_RIGHTSHIFT"]:
                    self.shift = (not keystate == keystates.up)
                elif keycode in ["KEY_LEFTCTRL", "KEY_RIGHTCTRL", "KEY_CAPSLOCK"]:
                    self.ctrl = (not keystate == keystates.up)
                elif keycode in ["KEY_LEFTALT", "KEY_RIGHTALT"]:
                    self.alt = (not keystate == keystates.up)
            return None, None

        elif keystate in [keystates.down, keystates.hold]:
            complete_code = "%s%s" % (self._prefix(), keycode)
            try:
                return char_keys[complete_code], complete_code
            except KeyError:
                return None, complete_code
        else:
            return None, None
    
