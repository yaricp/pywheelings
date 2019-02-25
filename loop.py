
from pygame import *

import time
from math import sin, cos, radians
from pyo_test import SoundLoop


try:
    from multiprocessing import Value, Process, Condition
except ImportError:
    from processing import Value,  Process,  Condition

from record_sound import record

from settings import *


class Loop(sprite.Sprite):
    count =0
    sync_start = 0
    sync_time = 0
    
    def __init__(self, rad,  x, y, sync_pipe):
        sprite.Sprite.__init__(self)
        self.focus = False
        self.id = Loop.count + 1
        Loop.count += 1
        self.sync_pipe = sync_pipe
        self.x = x
        self.y = y
        self.rad = rad 
        self.rad_vol = int(NORMAL_VALUE_LOOP*rad)
        self.current_vol = NORMAL_VALUE_LOOP
        self.filename = str(self.id)+'_file.'
        self.recfilename = PATH_FILES+self.filename+REC_FILE_EXT
        self.playfilename = None
        self.sound = None
        self.__stream = None
        self.__channel = None
        self.playing = False
        self.__time_start_play = None
        self.__time_start_record = None
        self.recording = False
        self.rec_process = None
        self.play_process = None
        self.soundTable = None
        self.muted = False
        
        self.rect = Rect(x-rad, y-rad, 2*rad, 2*rad)
        self.__stop_record_event = False
        self.__start_record_event = False
        self.__stop_rec = Value('i', 1)
        
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
                if self.sound:
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
            
    def erase_sound(self):
        if self.recording:
            self.__stop_record()
        self.__stop_play()
        self.sound = None
        self.playfilename = None
        self.current_vol = NORMAL_VALUE_LOOP
   
#    def __delete_files(self):
#        if self.__class__.__name__!='Loop_Sync':
#            print( 'del file ')
#            os.system(' rm '+self.playfilename)
#        return True
            
    def __init_sound(self):
        if self.playfilename and not self.sound:
            self.sound = mixer.Sound(self.playfilename)
        
    def __start_play(self):
        if self.soundTable:
            self.play_proccess = PlayProc(self.id, self.soundTable)
#        self.__init_sound()
#        if not self.playing:
#            if self.sound:
#                self.playing = True
#                self.play_sound()

    def __stop_play(self):
        
        if self.playing:
                self.sound.stop()
                self.playing = False
                self.__time_start_play = None

    def play_sound(self, delta=0, time_sync=None):
        if self.playing:
            if delta >= 0 and self.is_last_period(time_sync):
                if self.__channel and self.__channel.get_busy():
                    self.sound.stop()
                self.__channel = self.sound.play()
                self.__time_start_play = time.time()

    #@profile_c
    def __start_record(self):
        if self.focus:
            if not self.recording:
                self.__stop_rec.value = 0
                self.sync_pipe[0].send((None, NEW_LOOP))
                self.rec_process = SoundLoop( self.id, 
                                            self.sync_pipe[1]
                                            )
                self.rec_process.start()
                self.sync_pipe[0].send([self.id, RECORD])
                self.__time_start_record = time.time()
                self.recording = True
    
    def __stop_record(self):
        if self.focus:
            if self.recording:
                self.recording = False
                self.sync_pipe[0].send([self.id, STOP_RECORD])
#                self.__stop_rec.value = 1
#                
#                self.playfilename = PATH_FILES+self.filename+PLAY_FILE_EXT

    def mute(self):
        if self.sound and self.playing:
#            self.sound.set_volume(0.0)
            self.sync_pipe[0].send(self.id, MUTE)
            self.rad_vol = 3
            self.muted = True
            
    def unmute(self):
        if self.sound  and self.playing:
            self.sound.set_volume(self.current_vol)
            self.rad_vol = int(self.current_vol*self.rad)
            self.muted = False
            
    def __change_volume_sound(self, direct, value):
        if self.playing:
            if direct == '+':
                val = self.sound.get_volume()+value
            else:
                val = self.sound.get_volume()-value
            self.sound.set_volume(val)
            new_rad = int(round(val*self.rad))
            self.current_vol = val
            if new_rad >= 3:
                self.rad_vol = new_rad
    
    def is_last_period(self, time_sync):
        if time_sync:
            if self.__length_sound<=time_sync or not self.__time_start_play:
                return True
            else:
                curr_time_to_end = self.__length_sound - (time()-self.__time_start_play)
                if curr_time_to_end <= 0:
                    return True
            return False
   
    @property
    def __length_sound(self):
        if self.sound:
            length_s = self.sound.get_length()
        else:
            length_s = time.time()-self.__time_start_record
        return length_s
            
    def __end_point(self):
        now = time.time()
        time_begin = None
        if self.playing:
            time_begin = self.__time_start_play
        if self.recording:
            time_begin = self.__time_start_record
        if not time_begin:
            time_begin = now
        time_cur = now - time_begin
        angle = (360 * time_cur)/self.__length_sound
        x = self.x + sin(radians(angle))*self.rad
        y = self.y - cos(radians(angle))*self.rad
        return (x, y)
   
    def draw(self, screen): 
        if self.focus:
            thin = FOCUS_THICKNESS_LINE_LOOP
        else:
            thin = THICKNESS_LINE_LOOP
        draw.circle(screen, COLOR_LOOP, (self.x, self.y), self.rad,thin)
        if self.sound:
            draw.circle(screen, COLOR_VOL_LOOP, (self.x, self.y), self.rad_vol, thin)
        if self.recording or self.playing:
            draw.line(screen, COLOR_VOL_LOOP, (self.x, self.y), self.__end_point(), thin)
        font_loop = font.Font(None, SIZE_FONT_LOOP)
        height_font = font_loop.get_height()
        width_font = font_loop.get_linesize()
        text = font_loop.render(str(self.id), True, COLOR_FONT_LOOP)
        screen.blit(text, [self.x - width_font/2, self.y - height_font/2])


class LoopSync(Loop):

    def __init__(self, rad,  x, y, sync_pipe):
        super(LoopSync, self).__init__(rad, x, y, sync_pipe)
        self.rad_vol = int(NORMAL_VALUE_LOOP_SYNC * rad)
        self.__playfilename = PATH_FILES+SOUND_SYNC_LOOP
        self.time_sync = 0
        self.__prev_time_sound = 0
        self.delta = None
        self.__line_delta = 0
        self.sound = mixer.Sound(self.__playfilename)
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

