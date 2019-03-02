
from pygame import *

import time, os
from math import sin, cos, radians
from pyo_test import loop_sound_process


try:
    from multiprocessing import Value, Process, Condition
except ImportError:
    from processing import Value,  Process,  Condition

from record_sound import record 
from pyo_test import *


from settings import *


class Loop(sprite.Sprite):
    count =0
    sync_start = 0
    sync_time = 0
    
    def __init__(self, rad,  x, y, mixer_channel, mixer_event):
        sprite.Sprite.__init__(self)
        
        #print('loop init')
        self.focus = False
        self.id = Loop.count + 1
        Loop.count += 1
        self.x = x
        self.y = y
        self.rad = rad 
        self.rad_vol = int(NORMAL_VALUE_LOOP*rad)
        self.current_vol = NORMAL_VALUE_LOOP
        self.mixer_event = mixer_event
        self.mixer_channel = mixer_channel
        self.delta = 0
        self.__line_delta = 0
        self.length_sound = 0
#        self.filename = str(self.id)+'_file.'
#        self.recfilename = PATH_FILES+self.filename+REC_FILE_EXT
#        self.playfilename = None
        self.has_sound = None
#        self.__stream = None
#        self.__channel = None
        self.playing = False
        self.__time_start_play = None
        self.__time_start_record = None
        self.recording = False
        self.loop_event = Value('i', 100)
        self.loop_proc_id = Value('i', self.id)
        
        self.muted = False
        
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
#        self.__stop_record_event = False
#        self.__start_record_event = False
#        self.__stop_rec = Value('i', 1)
        
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
                if self.has_sound:
                    if self.playing:
                        self.__stop_play()
                    else:
                        self.__start_play()
        elif e == PLAY:
            self.__start_play()
        elif e == STOP_PLAY:
            self.__stop_play()
        elif e == RECORD:
            self.__start_record()
        elif e == STOP_RECORD:
            self.__stop_record()
            self.__start_play()
        elif e == MUTE:
            if self.muted:
                self.unmute()
            else:
                self.mute()
        elif e == ERASE:
            self.erase_sound()
   
    def __start_play(self):
        if not self.playing:
            self.mixer_event.value = PLAY          
            self.playing = True
            self.__time_start_play = time.time()
           
    def __stop_play(self):
        
        if self.playing:
            #self.sound.stop()
            self.mixer_event.value = STOP_PLAY
            self.playing = False
            self.__time_start_play = None

    def __start_record(self):
        if self.focus:
            if not self.recording:
                #self.__stop_rec.value = 0
                #print('loop_event: ', self.loop_event.value)
                self.mixer_channel.value = self.id
                self.mixer_event.value = NEW_LOOP
                self.rec_process = Process( target = loop_sound_process, 
                                            args = (self.loop_proc_id,
                                                    self.loop_event)
                                            ).start()
                #print('loop_event: ', self.loop_event.value)                            
                self.loop_event.value = RECORD
                self.__time_start_record = time.time()
                self.recording = True
    
    def __stop_record(self):
        if self.focus:
            if self.recording:
                self.recording = False
                self.mixer_event.value = STOP_RECORD
                self.mixer_channel.value = self.id
                self.loop_event.value = STOP_RECORD
                print('rec_process: ', self.rec_process)
                self.length_sound = time.time() - self.__time_start_record
                self.has_sound = True
                self.__time_start_play = time.time()

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
            self.rad_vol = new_rad
            if new_rad >= 3:
                self.rad_vol = new_rad
            

            
    def __end_point(self):
        now = time.time()
        length = self.length_sound
        time_begin = None
        delta_circle = 0
        if self.playing:
            #print('length: ', length)
            time_begin = self.__time_start_play
            delta_circle = (now - time_begin) - length * ((now - time_begin)//length)
            #print('delta_circle: ',  delta_circle)
        if self.recording:
            time_begin = self.__time_start_record
            delta_circle = now - time_begin
            length = 5 + delta_circle
        if not time_begin:
            time_begin = now
        if round(delta_circle, 1) == 0:
            self.__line_delta = 0
        self.__line_delta += 1
        angle = 360*delta_circle/length
        x = self.x + sin(radians(angle))*self.rad
        y = self.y - cos(radians(angle))*self.rad

        return (x, y)
   
    def draw(self, screen): 
        if self.focus:
            thin = FOCUS_THICKNESS_LINE_LOOP
        else:
            thin = THICKNESS_LINE_LOOP
        draw.circle(screen, COLOR_LOOP, (self.x, self.y), self.rad,thin)
        if self.has_sound:
            draw.circle(screen, COLOR_VOL_LOOP, (self.x, self.y), self.rad_vol, thin)
        if self.recording:
            draw.line(screen, COLOR_VOL_LOOP, (self.x, self.y), self.__end_point(), thin)
        elif self.playing:
            if self.__line_delta <= 5:
                thin = FOCUS_THICKNESS_LINE_LOOP_SYNC+5
            else:
                thin = THICKNESS_LINE_LOOP_SYNC
            draw.line(screen, COLOR_VOL_LOOP, (self.x, self.y), self.__end_point(), thin)
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        height_font = font_loop.get_height()
        width_font = font_loop.get_linesize()
        text = font_loop.render(str(self.id), True, COLOR_FONT_LOOP)
        screen.blit(text, [self.x - width_font/2, self.y - height_font/2])


class LoopSync(Loop):

    def __init__(self, rad,  x, y, mixer_channel, mixer_event):
        super(LoopSync, self).__init__(rad, x, y, mixer_channel, mixer_event)
        self.rad_vol = int(NORMAL_VALUE_LOOP_SYNC * rad)
        self.__playfilename = PATH_FILES+SOUND_SYNC_LOOP
        self.time_sync = 0
        self.__prev_time_sound = 0
        self.delta = None
        self.__line_delta = 0
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.__playfilename)
        self.sound = mixer.Sound(filename)
        self.sound.set_volume(NORMAL_VALUE_LOOP_SYNC)
        self.__length_sound = self.sound.get_length()
        
    def erase_sound(self):
        self.__stop_play()
        self.recording = False
        self.time_sync = 0
        self.__prev_time_sound = 0
        self.delta = None
        self.__line_delta = 0
        self.playing = False
        
    def start_stop(self):
        
        if self.recording:
            self.__stop_record()
            self.__start_play()
        elif self.playing:
            self.__stop_play()
        else:
            if self.time_sync != 0:
                self.__start_play()
            else:
                self.__start_record()
            
    def __start_play(self):
        self.playing = True
        self.sound.play(0)
        self.__prev_time_sound = time.time()
        
    def play_sound(self):
        if self.playing:
            prev_delta = time.time()-self.__prev_time_sound
            self.delta = round(prev_delta-self.time_sync, CORRECT_TIME_SYNC)
            if self.delta and self.delta >= 0:
                self.sound.play(0)
                self.__prev_time_sound = time.time()
        
    def __stop_play(self):
        self.playing = False
        
    def __start_record(self):
        self.start_time = time.time()
        #print(gmtime)
        self.recording = True
        
    def __stop_record(self):
        self.time_sync = time.time() - self.start_time-self.__length_sound
        self.recording = False
        
    def __end_point(self):
        time_cur = self.delta/self.time_sync
        angle = round(360*time_cur)
        x = self.x+sin(radians(angle))*self.rad
        y = self.y - cos(radians(angle))*self.rad
        return (x, y)
        
    def draw(self, screen): 
        if self.playing or self.recording:
            thin = FOCUS_THICKNESS_LINE_LOOP_SYNC
        else:
            thin = THICKNESS_LINE_LOOP_SYNC
        #print(screen,self.x,self.y,self.rad,thin,COLOR_LOOP_SYNC)
        draw.circle(screen, COLOR_LOOP_SYNC, (self.x, self.y), self.rad, thin)
        if self.playing:
            self.__line_delta += 1
            if self.delta and self.delta >= 0:
                self.__line_delta = 0
            if self.__line_delta <= 50:
                thin = FOCUS_THICKNESS_LINE_LOOP_SYNC+5
            else:
                thin = THICKNESS_LINE_LOOP_SYNC
            draw.line(screen, COLOR_VOL_LOOP_SYNC, (self.x, self.y), self.__end_point(), thin)
            draw.circle(screen, COLOR_VOL_LOOP_SYNC, (self.x, self.y), self.rad_vol, THICKNESS_LINE_LOOP_SYNC)

