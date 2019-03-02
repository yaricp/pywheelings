import time, random, multiprocessing
from pyo import *

from settings import *


def mixer_loops(event, channel):
    server = Server(audio='jack', nchnls=2)
    server.deactivateMidi()
    server.boot().start()
    bufsize = server.getBufferSize()
    mixer = Mixer(outs=1, chnls=COUNT_IN_ROW * COUNT_ROWS, time=.025).out()
    e = event.value
    ch = channel.value
    rec_tables = {}
    print('mixer e: ', e)
    print('mixer ch: ', ch)
    
    while True:
        e = event.value
        ch = channel.value
        if e == NEW_LOOP and ch and not (ch in rec_tables):
            name = "/audio-%d" % ch
            print('name: ', name)
            newTable = NewTable(length=8, chnls=1, feedback=0.5)
            tab = SharedTable(  name, 
                                create=True, 
                                size=bufsize)
            
            #print('tab in mixer: ', tab)
            out = TableScan(tab)
            table_rec = TableRec(out, table=newTable, fadetime=0.05).play()
            mixer.addInput(ch, out)
            mixer.setAmp(ch,0,.1)
            #print('mixer: ',  mixer.__dict__)
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_RECORD or e == PLAY:
            print('mixer stop record')
            table_rec.stop()
            mixer.delInput(ch)
            if not ch in rec_tables:
                rec_tables.update({ch:newTable})
            soundTable = rec_tables[ch]
            dur = soundTable.getDur()
            out = Looper(soundTable, start=0, dur=dur, mul=0.3)
            print('out: ', out)
            mixer.addInput(ch, out)
            mixer.setAmp(ch,0,.1)
            #freq = soundTable.getRate()
            #out = Osc(table=soundTable, freq=freq, phase=[0, 0.5], mul=0.4).out()
            #mixer.addInput(ch, out)
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_PLAY:
            play_table.stop()
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_UP:
            value = mixer._base_players[ch].gains[str(ch)][0]
            print('mixer._base_players ', mixer._base_players[ch].gains[str(ch)][0])
            if value < 1.0:
                mixer.setAmp(ch,0, value + STEP_VALUE_LOOP)
            event.value = 1000
            channel.value = 0
            
            
        elif e == WHEEL_DOWN:
            value = mixer._base_players[ch].gains[str(ch)][0]
            if value > 0:
                mixer.setAmp(ch,0, value - STEP_VALUE_LOOP)
            event.value = 1000
            channel.value = 0
            
        elif e == MUTE:
            mixer.setAmp(ch,0,0)
#        elif event == INC_VOLUME:
#            mixer.setAmp(channel,0,.5)
        if e == QUIT:
            server.stop()
            return true

    
def loop_sound_process(loop_id, event):
    print('start loop sound process')
    e = event.value
    id = loop_id.value
    print('e: ', e)
    print('id: ', id)
    
    soundTable = None
    name = "/audio-%d" % id
    
    while True:
        e = event.value
        id = loop_id.value
        if e == RECORD:
            server = Server(audio='jack',  ichnls=1)
            server.deactivateMidi()
            server.boot().start()
            bufsize = server.getBufferSize()
            soundTable = NewTable(length=8, chnls=1, feedback=0.5)
            share_tab = SharedTable(name, create=False, size=bufsize)
            inp = Input(chnl=0)
            #
            # Rack of effects
            #
            res_out = Delay(inp, delay=.1, feedback=0.8, mul=0.2)
            res = TableFill(res_out, share_tab)
            event.value = 1000
            loop_id.value = 0
        elif e == STOP_RECORD:
            print('stop record')
            inp.stop()
            res.stop()
            res_out.stop()
            server.stop()
            return True
#   
        if e == QUIT:
            server.stop()
        
        
        
