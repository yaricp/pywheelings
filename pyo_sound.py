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
    play_tables = {}
    sh_tables = {}
    print('mixer e: ', e)
    print('mixer ch: ', ch)
    
    while True:
        e = event.value
        ch = channel.value
        if ch == COUNT_IN_ROW * COUNT_ROWS+1:
            e = 1000
            ch = 0
            continue
        if e == NEW_LOOP and ch and not (ch in rec_tables):
            name = "/audio-%d" % ch
            print('name: ', name)
            newTable = NewTable(length=1, chnls=1, feedback=0.5)
            if not ch in sh_tables:
                share_tab = SharedTable(  name, 
                                    create=True, 
                                    size=bufsize)
                sh_tables.update({ch: share_tab})
            else:
                share_tab = sh_tables[ch]
            
            print('create shared tab: ', share_tab.__dict__)
            #print('tab in mixer: ', tab)
            scan_tab = TableScan(share_tab)
            table_rec = TableRec(scan_tab, table=newTable, fadetime=0.05).play()
            mixer.addInput(ch, scan_tab)
            mixer.setAmp(ch,0,NORMAL_VALUE_LOOP/2)
            #print('mixer: ',  mixer.__dict__)
            event.value = 1000
            channel.value = 0
            
        elif (e == STOP_RECORD or e == PLAY) and ch:
            print('mixer stop record')
            table_rec.stop()
            mixer.delInput(ch)
            if not ch in rec_tables:
                rec_tables.update({ch:newTable})
            soundTable = rec_tables[ch]
            dur = soundTable.getDur()
            print('duration: ',  dur)
            looper = Looper(soundTable, start=0, dur=dur, mul=0.3)
            play_tables.update({ch: looper})
            mixer.addInput(ch, looper)
            mixer.setAmp(ch,0,.1)
            #freq = soundTable.getRate()
            #out = Osc(table=soundTable, freq=freq, phase=[0, 0.5], mul=0.4).out()
            #mixer.addInput(ch, out)
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_PLAY and ch:
            play_tables[ch].stop()
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_UP and ch:
            #print(ch)
            value = mixer._base_players[ch].gains[str(ch)][0]
            #print('mixer._base_players ', mixer._base_players[ch].gains[str(ch)][0])
            if value < 1.0:
                mixer.setAmp(ch,0, value + STEP_VALUE_LOOP)
            event.value = 1000
            channel.value = 0
            
            
        elif e == WHEEL_DOWN and ch:
            #print(ch)
            value = mixer._base_players[ch].gains[str(ch)][0]
            if value > 0:
                mixer.setAmp(ch,0, value - STEP_VALUE_LOOP)
            event.value = 1000
            channel.value = 0
            
        elif e == MUTE and ch:
            mixer.setAmp(ch,0,0)
            event.value = 1000
            channel.value = 0
            
        elif e == UNMUTE and ch:
            mixer.setAmp(ch,0,NORMAL_VALUE_LOOP)
            event.value = 1000
            channel.value = 0
            
        elif e == ERASE and ch:
            #print('erase ', ch)
            play_tables[ch].stop()
            mixer.delInput(ch)
            del play_tables[ch]
            del rec_tables[ch]
            #print(play_tables)
            #print(rec_tables)
            event.value = 1000
            channel.value = 0
            
            
        if e == QUIT:
            server.stop()
            return True

    
def loop_sound_process(loop_id, event):
    print('start loop sound process')
    e = event.value
    id = loop_id.value
    #print('e: ', e)
    #print('id: ', id)
    
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
            print('connect to shared_tab: ', name)
            share_tab = SharedTable(name, create=False, size=bufsize)
            print('share_tab: ', dir(share_tab._base_objs))
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

        
        
