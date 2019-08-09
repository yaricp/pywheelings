import os, json, pygame
from os import listdir
from os.path import isfile, join

from pygame import *

from settings import *


class ListFiles(sprite.Sprite):

    def __init__(   self,
                    x, y,
                    home_dir
                    ):
        sprite.Sprite.__init__(self)
        self.setting_dir = os.path.join(home_dir,'settings')
        self.default_file = join(self.setting_dir, 'default.json')
        self.files = [f for f in listdir(self.setting_dir) if isfile(join(self.setting_dir, f))]
        self.x = x
        self.y = y
        self.height = SIZE_FONT_LOOP * len(self.files) + 10
        self.width = len(max(self.files)) * SIZE_FONT_LOOP + 20
        
    def draw(self, screen):
        bg_files = Rect(self.x , self.y, self.width, self.height)
        pygame.draw.rect(screen, FILES_BACKGROUND_COLOR, bg_files, 2)
        
    def event(self, e):
        return True
        
    def get_personal_settings(self, f):
        """Get Personal settings from file"""
        with open(os.path.join(HOME_DIR,'%s.json' % f), 'r') as file:
            text = file.read()
            objects = json.loads(text)
            print(objects)
            return objects
            
    def get_default_settings(self):
        with open(self.default_file , 'r') as file:
            text = file.read()
            objects = json.loads(text)
            print('OBJECTS: ', objects)
            return objects
            
            
