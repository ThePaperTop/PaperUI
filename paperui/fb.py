import os
import pygame
import math
from paperui.core import ScreenDrawer

class FrameBufferDrawer(ScreenDrawer):
    def __init__(self):
        pygame.display.init()

        self.size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        ScreenDrawer.__init__(self, width=self.size[0], height=self.size[1])
        

        self.display = pygame.display.set_mode(self.size, pygame.FULLSCREEN)
        
        # Clear the screen to start
        self.display.fill((255, 255, 255))
        pygame.display.update()

    def __del__(self):
        pass

    def send(self):
        self.display.fill((255, 255, 255))
        
        scrn = self.screen.convert("RGB").tobytes()
        
        img = pygame.image.fromstring(scrn, self.size, "RGB")
        self.display.blit(img, (0,0))
        
        pygame.display.update()
        
    def clear(self):
        self.new_screen()
        self.send()
