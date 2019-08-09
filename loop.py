
from pygame import *

import time, os
from math import sin, cos, radians

try:
    from multiprocessing import Value, Process, Condition
except ImportError:
    from processing import Value,  Process,  Condition


from settings import *


class Loop(sprite.Sprite):
    count = 0
    sync_start = 0
    sync_time = 0
    
    def __init__(self, rad,  x, y, 
                        mixer_channel, 
                        mixer_event, 
                        mixer_tick, 
                        mixer_duration, 
                        dur_loops ):
        sprite.Sprite.__init__(self)
        
        self.focus = False
        self.id = Loop.count + 1
        Loop.count += 1
        self.x = x
        self.y = y
        self.rad = rad 
        self.tick_checked = False
        self.main_color = COLOR_LOOP
        self.rad_vol = int(NORMAL_VALUE_LOOP*rad)
        self.current_vol = NORMAL_VALUE_LOOP
        self.sync_length = 1
        count_sync_length = DEFAULT_LOOP_LENGTH
        if str(self.id) in dur_loops:
            count_sync_length = dur_loops[str(self.id)]
        self.count_sync_length = count_sync_length
        self.delta = 0
        self.__line_delta = 0
        self.length_sound = 0
        self.count_ticks = 0
        self.has_sound = None
        self.playing = False
        self.__time_start = None
        self.recording = False
        self.muted = False
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
        
        # shared with mixer
        
        self.mixer_event = mixer_event
        self.mixer_channel = mixer_channel
        self.mixer_tick = mixer_tick
        self.mixer_duration = mixer_duration
        
    
    def check_focus(self, key, m_pos, focus_loop_id):

        if key == 1 and self.rect.collidepoint(m_pos):
            if focus_loop_id != self.id:
                self.focus = True
                return True
        if self.id == focus_loop_id:
            self.focus = True
            return True
        else:
            self.focus = False
            return False

    def event(  self, e, m_pos=None, 
                sect_focus=None, 
                loop_for_rec=None):
        if e in [WHEEL_UP, WHEEL_DOWN, CLICK, LENGTH_INC, LENGTH_DEC]:
            if self.rect.collidepoint(m_pos):
                if e == WHEEL_UP:
                    self.__change_volume_sound('+', STEP_VALUE_LOOP)
                elif e == WHEEL_DOWN:
                    self.__change_volume_sound('-', STEP_VALUE_LOOP)
                elif e == CLICK:
                    if self.has_sound:
                        print('self.muted: ', self.muted)
                        if not self.muted:
                            self.mute()
                        else:
                            self.unmute()
                elif e == LENGTH_INC:
                    self.__change_length('+')
                
                elif e == LENGTH_DEC:
                    self.__change_length('-')
                            
        if e == REC_PLAY_LOOP:
            
            if self.id == loop_for_rec:
                if not self.has_sound and not self.recording:
                    self.start_record()
                else:
                    if self.recording:
                        self.stop_record()
                    elif self.has_sound:
                        if not self.playing:
                            self.start_play()
                        else:
                            self.stop_play()
        elif e == PLAY:
            self.start_play()
        elif e == STOP_PLAY:
            self.stop_play()
        elif e == MUTE:
            print('self.muted: ', self.muted)
            if self.muted:
                self.unmute()
            else:
                self.mute()
        elif e == MUTE_ALL:
            if sect_focus:
                if self.muted:
                    self.unmute()
                else:
                    self.mute()
        elif e == ERASE_ALL:
            print('loop erase all')
            if self.id == 1:
                print('send erase all to mixer')
                self.mixer_event.value = ERASE_ALL
            self.erase_all()
        elif e == ERASE:
            self.erase_sound()
        elif e == TOGGLE_SECTION:
            if self.id == 1:
                self.mixer_event.value = TOGGLE_SECTION
            if sect_focus:
                print('unmute_show')
                self.unmute_show()
            else:
                self.mute_show()
            
    def __change_length(self, direct):
        if direct == '+':
            self.count_sync_length += 1
        else:
            self.count_sync_length -= 1
        self.length_sound = self.count_sync_length * self.sync_length
        print('self.sync_length: ', self.id, self.sync_length)
        print('self.length_sound: ', self.id, self.length_sound)
        
    def start_play(self):
        print('send start play to mixer')
        self.playing = True
        self.__time_start = time.time()
        self.mixer_event.value = PLAY
        self.mixer_channel.value = self.id
        self.mixer_duration.value = self.length_sound
           
    def stop_play(self):
        print('send stop play to mixer')
        self.playing = False
        self.mixer_event.value = STOP_PLAY
        self.mixer_channel.value = self.id
        self.__time_start = None

    def start_record(self):
        print('start loop record: ', self.id)
        self.recording = True
        self.count_ticks = 0
        self.mixer_event.value = NEW_LOOP
        self.mixer_channel.value = self.id
        self.mixer_duration.value = self.count_sync_length * self.sync_length
        print('send duration to mixer: ', self.count_sync_length * self.sync_length)
        self.__time_start = time.time()
    
    def stop_record(self):
        print('send stop record to mixer')
        if self.count_ticks < 1:
            return False
        self.recording = False
        self.playing = True
        full_time = time.time() - self.__time_start
        full_time_by_ticks = self.count_ticks*self.sync_length
        delta =full_time - full_time_by_ticks
        if delta >= HUMAN_FACTOR/100:
            add_tick = 1
        else:
            add_tick = 0
        self.length_sound = (self.count_ticks + add_tick)*self.sync_length
        print('length: ', self.length_sound)
        if self.length_sound > self.sync_length * self.count_sync_length:
            self.length_sound = self.sync_length * self.count_sync_length
        print('send length: ', self.length_sound)
        self.mixer_duration.value = self.length_sound
        self.mixer_event.value = STOP_RECORD
        self.mixer_channel.value = self.id
        self.__time_start = time.time()
        print('stop rec length: ', self.length_sound)
        self.has_sound = True

    def mute(self):
        #print('loop mute:', self.id)
        if self.has_sound and not self.muted:
            self.mixer_event.value = MUTE
            self.mixer_channel.value = self.id
            self.playing = False
#            self.rad_vol = 3
            self.muted = True
            
    def mute_show(self):
        #print('loop mute_show:', self.id)
        if self.has_sound:
            self.playing = False
            self.muted = True
            
    def unmute(self):
        #print('loop unmute:', self.id)
        if self.has_sound and self.muted and not self.playing :
            self.mixer_event.value = UNMUTE
            self.mixer_channel.value = self.id
            self.playing = True
#            self.rad_vol = int(self.current_vol*self.rad)
        self.muted = False
            
    def unmute_show(self):
        #print('loop unmute_show:', self.id)
        if self.has_sound:
            self.playing = True
            self.muted = False
            
    def __change_volume_sound(self, direct, value):
        if self.playing:
            if direct == '+':
                self.mixer_event.value = WHEEL_UP
                self.mixer_channel.value = self.id
                self.current_vol = self.current_vol + value
            else:
                self.mixer_event.value = WHEEL_DOWN
                self.mixer_channel.value = self.id
                self.current_vol = self.current_vol - value
            new_rad = int(round(self.current_vol*self.rad))
            if new_rad >= self.rad:
                new_rad = self.rad
            if new_rad <= 0:
                new_rad = 0
            self.rad_vol = new_rad
            
    def erase_all(self):
        if self.has_sound:
            print('loop erase all self :', self.id)
            self.rad_vol = int(NORMAL_VALUE_LOOP*self.rad)
            self.main_color = COLOR_LOOP
            self.current_vol = NORMAL_VALUE_LOOP
            self.delta = 0
            self.__line_delta = 0
            self.length_sound = DEFAULT_LOOP_LENGTH
            self.has_sound = False
            self.playing = None
            self.recording = None
            self.__time_start = None
            
    def erase_sound(self):
        if self.has_sound:
            print('loop erase self :', self.id)
            self.mixer_event.value = ERASE
            self.mixer_channel.value = self.id
            self.rad_vol = int(NORMAL_VALUE_LOOP*self.rad)
            self.main_color = COLOR_LOOP
            self.current_vol = NORMAL_VALUE_LOOP
            self.delta = 0
            self.__line_delta = 0
            self.length_sound = DEFAULT_LOOP_LENGTH
            self.has_sound = False
            self.playing = None
            self.recording = None
            self.__time_start = None
        
            
    def __end_point(self):
        
        now = time.time()
        length = self.length_sound
        delta_circle = 0
        time_begin = self.__time_start
        delta_circle = (now - time_begin) - length * ((now - time_begin)//length)
        if round(delta_circle, 1) == 0:
            self.__line_delta = 0
        angle = 360*delta_circle/length
        x = self.x + sin(radians(angle))*self.rad
        y = self.y - cos(radians(angle))*self.rad

        return (x, y)
        
    def next_for_rec(self, loop_id):
        if self.id == loop_id:
            self.main_color = COLOR_FOR_NEXT_REC
        else:
            self.main_color = COLOR_LOOP
            
    def check_tick(self):
        if self.mixer_tick.value == 1:
            if self.recording:
                #print('recording')
                self.count_ticks += 1
                print('count+ ', self.count_ticks)
            self.tick_checked = True

    def draw(self, screen): 
        self.check_tick()
        if self.focus:
            thin = FOCUS_THICKNESS_LINE_LOOP
        else:
            thin = THICKNESS_LINE_LOOP
        if self.rad_vol < thin:
            self.rad_vol = thin
        color_loop = self.main_color
        color_vol_loop = COLOR_VOL_LOOP
        if self.recording:
            color_loop = COLOR_RECORDING
            color_vol_loop = COLOR_RECORDING
        # circle of volume
        if self.has_sound:
            
            draw.circle(screen, 
                        color_vol_loop, 
                        (self.x, self.y), 
                        self.rad_vol,
                        thin)
        # main circle
        draw.circle(screen, color_loop, (self.x, self.y), self.rad,thin)

        if (self.playing or self.recording):
            if self.__line_delta <= 10:
                thin = FOCUS_THICKNESS_LINE_LOOP_SYNC+5
            else:
                thin = THICKNESS_LINE_LOOP_SYNC
            self.__line_delta += 1
            
            draw.line(  screen, 
                        color_vol_loop, 
                        (self.x, self.y), 
                        self.__end_point(), 
                        thin)
        #Font of loop and other
        # number of loop
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        text = font_loop.render(str(self.id), True, COLOR_FONT_LOOP)
        screen.blit(text, [self.x - 30, self.y - 30])
        # volume of loop
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        text = font_loop.render(str(self.rad_vol/self.rad),
                                True, 
                                COLOR_FONT_LOOP)
        screen.blit(text, [self.x - 1, self.y - 30])
        # length of loop
        font_loop_length = font.Font(None, SIZE_FONT_LOOP_LENGTH)
        text = font_loop_length.render(str(self.count_sync_length), True, COLOR_FONT_LOOP_LENGTH)
        screen.blit(text, [self.x-5 , self.y-5 ])


class LoopSync(sprite.Sprite):

    def __init__(self, rad,  x, y, 
                loops, 
                mixer_channel, 
                mixer_event, 
                mixer_metro_time, 
                mixer_tick, 
                total_dict_loops):
        sprite.Sprite.__init__(self)
        self.id = COUNT_IN_ROW * COUNT_ROWS + 1 
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
        self.rad_vol = int(NORMAL_VALUE_LOOP*rad)
        self.current_vol = NORMAL_VALUE_LOOP
        self.loops = loops
        self.__line_delta = 0
        self.focus = None
        self.__time_start_play = None
        self.playing = False
        self.x = x
        self.y = y
        self.rad = rad
        self.muted = False
        self.started = False
        self.length_loop = DEFAULT_METRO_TIME
        self.mixer_channel = mixer_channel
        self.mixer_event = mixer_event
        self.mixer_metro_time = mixer_metro_time
        self.mixer_tick = mixer_tick
        self.total_dict_loops = total_dict_loops
        self.adjust_loops_length()
        
    def adjust_loops_length(self):
        for id, loop in self.total_dict_loops.items():
            loop.length_sound = loop.count_sync_length * self.length_loop
            loop.sync_length = self.length_loop
            print('loop.sync_length: ', loop.id, loop.sync_length)
            print('loop.length_sound: ', loop.id, loop.length_sound)
        
    def mute(self):
        self.start_stop()
        
    def check_focus(self, key, m_pos, focus_loop_id):

        if key == 1 and self.rect.collidepoint(m_pos):
            if focus_loop_id != self.id:
                self.focus = True
                return True
        if self.id == focus_loop_id:
            self.focus = True
            return True
        else:
            self.focus = False
            return False

    def event(self, e, m_pos=None, list_loops=None):
        if e == MUTE:
            if self.muted:
                self.unmute()
            else:
                self.mute()
        if self.rect.collidepoint(m_pos):
            if e == WHEEL_UP:
                self.__change_volume_sound('+', STEP_VALUE_LOOP)
            elif e == WHEEL_DOWN:
                self.__change_volume_sound('-', STEP_VALUE_LOOP)
            elif e == CLICK:
                self.start_stop()
            elif e == LENGTH_INC:
                self.__change_length('+', DEFAULT_DELTA_LENGTH_SYNTH, list_loops)
            elif e == LENGTH_DEC:
                self.__change_length('-', DEFAULT_DELTA_LENGTH_SYNTH, list_loops)
                
    def __change_volume_sound(self, direct, value):
        if self.playing:
            if direct == '+':
                #print('loop send wheel_up')
                self.mixer_channel.value = self.id
                self.mixer_event.value = WHEEL_UP
                self.current_vol = self.current_vol + value
            else:
                self.mixer_channel.value = self.id
                self.mixer_event.value = WHEEL_DOWN
                self.current_vol = self.current_vol - value
            new_rad = int(round(self.current_vol*self.rad))
            if new_rad >= self.rad:
                new_rad = self.rad
            self.rad_vol = new_rad
        
    def start_stop(self):
        self.mixer_event.value = METRO_STOP_PLAY_KEY
        if self.playing:
            self.playing = False
            self.started = False
            self.__line_delta = 0
            #self.__time_start_play = None
        else:
            self.started = True
            
    def check_started(self):
        
        if self.mixer_tick.value == 1:
            if self.started: 
                self.__line_delta = 0
                self.playing = True
                self.__time_start_play = time.time()
            
    def play(self):
        self.__line_delta = 0
        self.__time_start_play = time.time()
        
        
    def __change_length(self, direct,  delta, total_dict_loops):
        if direct == '+':
            self.length_loop -= delta
        else:
            self.length_loop += delta
        self.mixer_metro_time.value = self.length_loop
        self.mixer_event.value = CHANGE_METRO_TIME
        self.adjust_loops_length()
                
        
    def __end_point(self):
        now = time.time()
        length = self.length_loop
        time_begin = self.__time_start_play
        delta_circle = (now - time_begin) - length * ((now - time_begin)//length)
        self.__line_delta += 1
        angle = 360*delta_circle/length
        x = self.x+sin(radians(angle))*self.rad
        y = self.y - cos(radians(angle))*self.rad
        return (x, y)
        
    def draw(self, screen): 
        #print('mixer tick: ', self.mixer_tick.value)
        if self.playing:
            thin = FOCUS_THICKNESS_LINE_LOOP_SYNC
        else:
            thin = THICKNESS_LINE_LOOP_SYNC
        #print(screen,self.x,self.y,self.rad,thin,COLOR_LOOP_SYNC)
        draw.circle(screen, COLOR_LOOP, (self.x, self.y), self.rad, thin)
        if self.playing:

            if self.__line_delta <= 10:
                thin = FOCUS_THICKNESS_LINE_LOOP_SYNC+5
            else:
                thin = THICKNESS_LINE_LOOP_SYNC
            draw.line(  screen, 
                        COLOR_VOL_LOOP_SYNC, 
                        (self.x, self.y), 
                        self.__end_point(), 
                        thin)
            #draw volume circle
            thin_vol = THICKNESS_LINE_LOOP_SYNC
            #draw length of loop
            font_loop_length = font.Font(None, SIZE_FONT_LOOP_LENGTH)
            tick_per_min = round(60 / self.length_loop)
            text = font_loop_length.render(str(tick_per_min), True, COLOR_FONT_LOOP_LENGTH)
            screen.blit(text, [self.x , self.y ])
            if THICKNESS_LINE_LOOP_SYNC > self.rad_vol:
                thin_vol = self.rad_vol
                
            draw.circle(screen, COLOR_VOL_LOOP_SYNC, (self.x, self.y), self.rad_vol, thin_vol)



class LoopMain(sprite.Sprite):

    def __init__(self, rad,  x, y, 
                mixer_channel, 
                mixer_event):
        sprite.Sprite.__init__(self)
        self.id = MAIN_LOOP_ID 
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
        self.rad = rad
        self.rad_vol = rad
        self.current_vol = 0.99
        self.x = x
        self.y = y
        
        self.mixer_channel = mixer_channel
        self.mixer_event = mixer_event
        
    def __change_volume_sound(self, direct, value):
        if direct == '+':
            self.mixer_channel.value = self.id
            self.mixer_event.value = WHEEL_UP
            self.current_vol = self.current_vol + value
        else:
            self.mixer_channel.value = self.id
            self.mixer_event.value = WHEEL_DOWN
            self.current_vol = self.current_vol - value
        new_rad = int(round(self.current_vol*self.rad))
        if new_rad >= self.rad:
            new_rad = self.rad
        self.rad_vol = new_rad
            
    def event(self, e, m_pos=None):
        if self.rect.collidepoint(m_pos):
            if e == WHEEL_UP:
                self.__change_volume_sound('+', STEP_VALUE_LOOP)
            elif e == WHEEL_DOWN:
                self.__change_volume_sound('-', STEP_VALUE_LOOP)
        
    def draw(self, screen): 
        thin = THICKNESS_LINE_LOOP
        if self.rad_vol < thin:
            self.rad_vol = thin
        draw.circle(screen, COLOR_LOOP, 
                    (self.x, self.y), self.rad, thin)
        draw.circle(screen, COLOR_VOL_LOOP_SYNC, 
                    (self.x, self.y), self.rad_vol, thin)
        #TEXT
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        text = font_loop.render("Main Volume", True, COLOR_FONT_LOOP)
        screen.blit(text, [self.x - 30, self.y])
        
        # volume of loop
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        text = font_loop.render(str(self.rad_vol/self.rad),
                                True, 
                                COLOR_FONT_LOOP)
        screen.blit(text, [self.x - 1, self.y - 30])

