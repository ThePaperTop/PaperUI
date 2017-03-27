from paperui import ui

class Page(list):
    def __init__(self):
        self.height = 0
    def add(self, item):
        self.append(item)
        self.height += item.height

class PageFlow(ui.Column):
    def __init__(self, contents=list(), max_height=480):
        Column.__init__(self, contents)
        
        self.max_height = max_height
        
        self.pages = []
        self.current_page = 0

    def do_layout(self, x, y, height, owner=None):
        self.owner = owner
        self.width = width
        
        self.pages = [Page(),]
        
        for child in self.contents:
            cur_page = self.pages[-1]
            
            if cur_page.height + child.height <= self.max_height:
                cur_page.add(child)
            else:
                self.pages.append(Page())
                self.pages[-1].add(child)
