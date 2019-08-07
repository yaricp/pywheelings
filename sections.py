# -*- coding: utf-8 -*

import pygame
from pygame import *
from settings import *


class Section(sprite.Sprite):
    count = 0

    def __init__(self, left, top, width, height):

        self.id = Section.count + 1
        Section.count += 1
        self.rect = Rect(left, top, width, height)
        self.focus = False
        self.prev = False
        self.muted = False
        self.loops = []
        
    def check_focus(self, current_sect):

        if self.playing:
            self.prev = True
        else:
            self.prev = False
        if self.id == current_sect:
            self.focus = True
            self.prev = False
            return self.__get_last_loop()
        else:
            self.focus = False
            return False

    @property
    def playing(self):
        for loop in self.loops:
            if loop.playing:
                return True
        return False

    def __get_last_loop(self):
        if self.loops:
            return self.loops[-1]
        else:
            return False

    def mute_unmute(self):

        for loop in self.loops:
            if self.muted:
                loop.event(UNMUTE)
                self.muted = False
            else:
                loop.event(MUTE)
                self.muted = True
                
    def mute(self):
        print ('section mute: ', self.id)
        print('muted: ', self.muted)
        if not self.muted:
            for loop in self.loops:
                loop.mute()
            self.muted = True
    
    def unmute(self):
        print('section unmute: ', self.id)
        print('muted: ', self.muted)
        if self.muted:
            for loop in self.loops:
                loop.unmute()
            self.muted = False
        
                
    def draw(self,screen):

        if self.focus:
            thin = FOCUS_THICKNESS_LINE_SECT
            color = FOCUS_COLOR_SECT
        elif self.prev:
            thin = FOCUS_THICKNESS_LINE_SECT
            color = PREV_COLOR_SECT
        else:
            thin = THICKNESS_LINE_SECT
            color = COLOR_SECT
        pygame.draw.rect(screen, color, self.rect, thin)
