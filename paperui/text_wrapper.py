class TextWrapper(object):
    def __init__(self):
        self._wrap_chars = " "
        self.unwrapped = ""
        self.cursor_loc = [0, 0]
        self.prev_line_break = 0
        self.rows = []
    def add_line(self, end):

        new_line = self.unwrapped[self.prev_line_break:end].replace("\n", " ")
        self.rows.append(new_line)
        
        if 0 <= self.chars_to_cursor <= len(new_line):
            self.cursor_loc[0] = len(self.rows) - 1
            self.cursor_loc[1] = self.chars_to_cursor

        self.chars_to_cursor -= len(new_line)

        self.prev_line_break = end

    def wrap(self, s, cursor_pos, width=80):
        self.unwrapped = s
        self.cursor_loc = [0, 0]
        self.prev_line_break = 0
        self.rows = []
        
        maybe_break_at = 0
        
        self.chars_to_cursor = cursor_pos
        
        for i in range(len(s)):

            if s[i] == "\n":
                self.add_line(i+1)
            elif i - self.prev_line_break == width:
                if maybe_break_at <= self.prev_line_break:
                    self.add_line(i)
                else:
                    self.add_line(maybe_break_at)
            else:
                if s[i] in self._wrap_chars:
                    maybe_break_at = i + 1
        self.add_line(len(s))
        return self.rows, self.cursor_loc[0], self.cursor_loc[1]

if __name__ == "__main__":
    tw = TextWrapper()
    
    text = """This is a test.  I have a very long piece of text here, and I'd like to wrap it to various widths and see if I have wrapping and cursor positioning right.  This text allows me to test that; at least it _will_, if I get enough text in here.   Luckily I'm a fairly swift and accurate typist, so I don't have to struggle too much to get this done; some people are much better, and get less distracted --- stop hitting your sister! --- than I do.  At any rate, this should be enough.

This is a test.  I have a very long piece of text here, and I'd like to wrap it to various widths and see if I have wrapping and cursor positioning right."""


    
    rows, row, col = tw.wrap(text, 0, 87)
    print("\n".join(rows))

    for cursor_pos in range(len(text)):
        rows, row, col = tw.wrap(text, cursor_pos, 87)
        print(text[cursor_pos].replace("\n", " "), rows[row][col], cursor_pos, "(%s, %s)" % (row, col))
