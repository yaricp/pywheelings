
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
                        mixer_metro_time, 
                        mixer_tick, 
                        mixer_duration):
        sprite.Sprite.__init__(self)
        
        #print('loop init')
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
        # shared with mixer
        self.mixer_event = mixer_event
        self.mixer_channel = mixer_channel
        self.mixer_tick = mixer_tick
        self.mixer_metro_time = mixer_metro_time
        self.mixer_duration = mixer_duration
        print('self.mixer_metro_time: ', self.mixer_metro_time.value) 
        
        self.delta = 0
        self.__line_delta = 0
        self.length_sound = DEFAULT_LOOP_LENGTH
        self.count_ticks = 0
#        self.filename = str(self.id)+'_file.'
#        self.recfilename = PATH_FILES+self.filename+REC_FILE_EXT
#        self.playfilename = None
        self.has_sound = None
        self.playing = False
        self.__time_start = None
        self.recording = False
        self.muted = False
        
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)

        
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

    def event(self, e, m_pos=None):
        if e == WHEEL_UP and self.rect.collidepoint(m_pos):
            self.__change_volume_sound('+', STEP_VALUE_LOOP)
        elif e == WHEEL_DOWN and self.rect.collidepoint(m_pos):
            self.__change_volume_sound('-', STEP_VALUE_LOOP)
        elif e == CLICK:
            print ('CLICK')
            if self.rect.collidepoint(m_pos):
                if self.has_sound:
                    if self.playing:
                        print('1stop play')
                        self.stop_play()
                    else:
                        print('2start play')
                        self.start_play()
                        
        elif e == REC_PLAY_LOOP_KEY:
            print('ID: ', self.id)
            if not self.has_sound and not self.recording:
                print('loop start record: ', time.time())
                self.start_record()
            else:
                if self.recording:
                    print('loop stop record start play')
                    self.stop_record()
                    #self.start_play()
                elif not self.playing:
                    print('loop start play')
                    self.start_play()
                else:
                    print('loop stop play')
                    self.stop_play()
        elif e == PLAY:
            print('3start play')
            self.start_play()
        elif e == STOP_PLAY:
            print('4stop play')
            self.stop_play()
#        elif e == RECORD:
#            print('plan to record')
#            self.recording = True
#            #self.__start_record()
#        elif e == STOP_RECORD:
#            self.recording = False
#            self.playing = True
#            self.stop_record()
#            #self.__start_play()
        elif e == MUTE:
            if self.muted:
                self.unmute()
            else:
                self.mute()
        elif e == ERASE:
            self.erase_sound()
   
    def start_play(self):
        print('send start play to mixer')
        self.playing = True
        self.__time_start = time.time()
        self.mixer_channel.value = self.id
        self.mixer_event.value = PLAY 
        self.mixer_duration.value = self.length_sound
           
    def stop_play(self):
        print('send stop play to mixer')
        self.playing = False
        self.mixer_channel.value = self.id
        self.mixer_event.value = STOP_PLAY
        self.__time_start = None

    def start_record(self):
        print('send to mixer start loop record: ', self.id)
        self.recording = True
        self.count_ticks = 0
        self.mixer_channel.value = self.id
        self.mixer_duration.value = self.length_sound
        self.mixer_event.value = NEW_LOOP
        self.__time_start = time.time()
    
    def stop_record(self):
        print('send stop record to mixer')
        if self.count_ticks < 1:
            return False
        self.recording = False
        self.playing = True
        #self.length_sound = time.time() - self.__time_start
        full_time = time.time() - self.__time_start
        full_time_by_ticks = self.count_ticks*self.mixer_metro_time.value
        delta =full_time - full_time_by_ticks
        if delta >= HUMAN_FACTOR/100:
            add_tick = 1
        else:
            add_tick = 0
        self.length_sound = (self.count_ticks + add_tick)*self.mixer_metro_time.value
        self.mixer_channel.value = self.id
        self.mixer_duration.value = self.length_sound
        self.mixer_event.value = STOP_RECORD
        self.__time_start = time.time()
        print('stop rec length: ', self.length_sound)
        self.has_sound = True

    def mute(self):
        if self.has_sound and self.playing:
#            self.sound.set_volume(0.0)
            self.sync_pipe[0].send(self.id, MUTE)
            self.rad_vol = 3
            self.muted = True
            
    def unmute(self):
        if self.has_sound  and self.playing:
            self.sound.set_volume(self.current_vol)
            self.rad_vol = int(self.current_vol*self.rad)
            self.muted = False
            
    def __change_volume_sound(self, direct, value):
        if self.playing:
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
            if new_rad <= 0:
                new_rad = 0
            self.rad_vol = new_rad
            
    def erase_sound(self):
        if self.has_sound:
            print(' erase self :', self.id)
            self.mixer_channel.value = self.id
            self.mixer_event.value = ERASE
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
        #print('loop length; ', length)
        time_begin = None
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
        #print('tick: ', self.mixer_tick.value)
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
        # line of time of loop
#        if self.id ==  1:
#            print('playing: ', self.playing)
#            print('recording: ', self.recording)
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
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        height_font = font_loop.get_height()
        width_font = font_loop.get_linesize()
        
        text = font_loop.render(str(self.id), True, COLOR_FONT_LOOP)
        screen.blit(text, [self.x - 30, self.y - 30])
        font_loop_length = font.Font(None, SIZE_FONT_LOOP_LENGTH)
        text = font_loop_length.render(str(self.length_sound), True, COLOR_FONT_LOOP_LENGTH)
        screen.blit(text, [self.x , self.y ])


class LoopSync(sprite.Sprite):

    def __init__(self, rad,  x, y, 
                mixer_channel, 
                mixer_event, 
                mixer_metro_time, 
                mixer_tick):
        sprite.Sprite.__init__(self)
        self.id = COUNT_IN_ROW * COUNT_ROWS + 1 
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
        self.rad_vol = int(NORMAL_VALUE_LOOP*rad)
        self.current_vol = NORMAL_VALUE_LOOP
        self.__line_delta = 0
        self.focus = None
        self.__time_start_play = None
        self.playing = False
        self.x = x
        self.y = y
        self.rad = rad
        self.muted = False
        self.length_loop = DEFAULT_METRO_TIME
        self.mixer_channel = mixer_channel
        self.mixer_event = mixer_event
        self.mixer_metro_time = mixer_metro_time
        self.mixer_tick = mixer_tick
        
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

    def event(self, e, m_pos=None):
        if e == WHEEL_UP and self.rect.collidepoint(m_pos):
            self.__change_volume_sound('+', STEP_VALUE_LOOP)
        elif e == WHEEL_DOWN and self.rect.collidepoint(m_pos):
            self.__change_volume_sound('-', STEP_VALUE_LOOP)
        elif e == CLICK:
            if self.rect.collidepoint(m_pos):
                self.start_stop()
        elif e == MUTE:
            if self.muted:
                self.unmute()
            else:
                self.mute()
        elif e == LENGTH_INC and self.rect.collidepoint(m_pos):
            self.__change_length('+', STEP_VALUE_LOOP)
        elif e == LENGTH_DEC and self.rect.collidepoint(m_pos):
            self.__change_length('-', STEP_VALUE_LOOP)
                
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
            #self.__time_start_play = None
        else:
            self.playing = True
            self.__time_start_play = time.time()
            
            
    def play(self):
        self.__line_delta = 0
        self.__time_start_play = time.time()
        
        
    def __change_length(self, delta):
        self.length_sound += delta
        

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
#            self.__line_delta += 1
#            if self.delta and self.delta >= 0:
#                self.__line_delta = 0
            if self.__line_delta <= 5:
                thin = FOCUS_THICKNESS_LINE_LOOP_SYNC+5
            else:
                thin = THICKNESS_LINE_LOOP_SYNC
            draw.line(screen, COLOR_VOL_LOOP_SYNC, (self.x, self.y), self.__end_point(), thin)
            #draw volume circle
            thin_vol = THICKNESS_LINE_LOOP_SYNC
            if THICKNESS_LINE_LOOP_SYNC > self.rad_vol:
                thin_vol = self.rad_vol
                
            draw.circle(screen, COLOR_VOL_LOOP_SYNC, (self.x, self.y), self.rad_vol, thin_vol)

