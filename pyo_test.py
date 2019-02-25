import time, random, multiprocessing
from pyo import *

from settings import *


class MixerLoops(multiprocessing.Process):
    def __init__(self, connection):
        super(MixerLoops, self).__init__()
        self.daemon = True
        self.connection = connection
        self.mixer = None

    def run(self):
        self.server = Server(audio="jack")
        self.server.deactivateMidi()
        self.server.boot().start()
        bufsize = self.server.getBufferSize()
        self.mixer = Mixer(outs=1, chnls=COUNT_IN_ROW * COUNT_ROWS, time=.025)
        
        event = self.connection[1]
        loop_id = self.connection[0]
        tables
        if event == NEW_LOOP:
#            self.tables.update({'id': loop_id,  
#                                'table': SharedTable("/audio-"+str(loop_id), 
#                                                    create=False, 
#                                                    size=bufsize)
#                                })
            tab = SharedTable("/audio-"+str(loop_id), 
                                create=False, 
                                size=bufsize)
            out = TableScan(tab).out()
            self.mixer.addInput(loop_id, out)
            self.mixer.setAmp(loop_id,0,.5)
        elif event == MUTE:
            self.mixer.setAmp(loop_id,0,0)
        elif event == INC_VOLUME:
            self.mixer.setAmp(loop_id,0,.5)

        self.server.stop()
        

class SoundLoop(multiprocessing.Process):
    """ Process of record sound in loop processing and play realtime"""
    
    def __init__(self, loop, connection):
        super(SoundLoop, self).__init__()
        self.loop = loop
        self.daemon = True
        self.connection = connection
        self.mixer = None
        self.rec = None
        self.play = None
        self.filename = "/files/%d_file.wav" % loop
        
    def processing(self, table):
        """ Filters, effects and other processing with sound """
        
        self.mixer = Mixer(outs=3, chnls=2, time=.025)
        # Processing with sound
        return table
        
    def run(self):
        print(self.connection.poll())
        id  = self.connection.poll()[0]
        e = self.connection.poll()[1]
        while 1:
            if id == self.loop :

                if e == PLAY:
                    if self.rec:
                        self.__play_sound()
                elif e == STOP_PLAY:
                    if self.play:
                        self.server.stop()
                elif e == RECORD:
                    self.__start_record()
                elif e == STOP_RECORD:
                    self.server.stop()
                
    def __play_sound(self):
        self.server = Server().boot()
        self.server.start()
        name = "/audio-%d" % self.loop
        play_tab = SharedTable(name, create=True, size=bufsize)
        self.play = TablePut(self.rec, play_tab).play()
        
    def __start_record(self):
        self.server = Server(audio='jack', nchnls=1).boot()
        inp = Input(chnl=0).out()
        self.server.deactivateMidi()
        self.server.boot()
        self.server.start()
        bufsize = self.server.getBufferSize()
        t = NewTable(length=8, chnls=1, feedback=0.5)
        #
        # Send sound to processor
        #
        
        #
        # Get sound after processor
        #
        self.rec = TableRec(inp, table=t, fadetime=0.05)
        
