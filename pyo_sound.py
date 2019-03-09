import sys, time, random, multiprocessing
from pyo import *

from settings import *


def send_tick(tick):
    tick.value = 1
    

def mixer_loops(event, channel, metro_time, tick, duration):
    server = Server(audio='jack', nchnls=2)
    server.deactivateMidi()
    server.boot().start()
    bufsize = server.getBufferSize()
    mixer = Mixer(outs=1, chnls=COUNT_IN_ROW * COUNT_ROWS, time=.025).out()
    metro_id = COUNT_IN_ROW * COUNT_ROWS + 1
    print('metro_id: ', metro_id)
    e = event.value
    ch = channel.value
    rec_tables = {}
    play_tables = {}
    sh_tables = {}
    temp_tables = {}
    list_for_del = []
    print('mixer e: ', e)
    print('mixer ch: ', ch)
    metro_playing = False
    t = metro_time.value
    m = Metro(time=t)
    print('m: ', m)
    def send_tick():
        print('tick:',  time.time())
        tick.value = 1
    tf = TrigFunc(m, send_tick)
    start_play_metro = Trig()
    cos_t = CosTable([(0,0), (50,1), (250,.3), (8191,0)])
    amp_metro = TrigEnv(m, table=cos_t, dur=.25, mul=.1)
    a = Sine(freq=1000, mul=amp_metro).out()
    print('define metronome')
    
    
    while True:
        e = event.value
        ch = channel.value
        rec_play_dur = duration.value
       
        
        if ch == 0 and e == 1000:
#            list_for_del = []
#            for tmp_ch in temp_tables:
#                dur = play_tables[tmp_ch][2]
#                if (dur - round(time.time() - temp_tables[tmp_ch], 5)) < float(t):
#                    list_for_del.append(tmp_ch)
#                    #print('for del : ', tmp_ch, time.time())
#            for id_for_del in list_for_del:
#                if id_for_del in temp_tables:
#                    #print('del')
#                    del temp_tables[id_for_del]
            for play_t in play_tables:
                if play_tables[play_t][1] == 0 and tick.value == 1:
                    print('change start time')
                    print('delta: ',0)
                    play_tables[play_t][1] = 1
                    play_tables[play_t][0].stop()
                    play_tables[play_t][0].setStart(0)
                    play_tables[play_t][0].play()
#                    temp_tables.update({play_t: time.time()})

        if e == NEW_LOOP and ch and not (ch in rec_tables):
            name = "/audio-%d" % ch
            length_loop = rec_play_dur
            print('mixer create shared table : ', name, length_loop )
            newTable = NewTable(length=length_loop, chnls=1, feedback=0)
            if not ch in sh_tables:
                share_tab = SharedTable( name, 
                                        create=True, 
                                        size=bufsize)
                sh_tables.update({ch: share_tab})
            else:
                share_tab = sh_tables[ch]
            scan_tab = TableScan(share_tab)
            print('start rec:', time.time())
            table_rec = TableRec(scan_tab, table=newTable, fadetime=0).play()
            mixer.addInput(ch, scan_tab)
            mixer.setAmp(ch,0,NORMAL_VALUE_LOOP*0.6)
            event.value = 1000
            channel.value = 0
            
        elif (e == STOP_RECORD or e == PLAY) and ch:
            print('mixer stop record and start play')
            table_rec.stop()
            mixer.delInput(ch)
            dur = 0
            if not ch in play_tables:
                looper = Looper( table=newTable, 
                                start=2 * 0.073913, dur=rec_play_dur, 
                                mul=1).out()
                play_tables.update({ch: [looper, 0]})
#                looper = TrigEnv(play_tables[ch][1], 
#                                table=play_tables[ch][0], 
#                                dur=play_tables[ch][0].getDur(),
#                                mul=1)
                print('mixer start table with duration: ', rec_play_dur)
                print('t:', time.time())
                print('delta: ',  2 * 0.073913)

            mixer.addInput(ch, looper)
            mixer.setAmp(ch,0,.5)
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_PLAY and ch:
            print('mixer stop play')
            play_tables[ch].stop()
            del play_tables[ch]
            del temp_tables[ch]
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_UP and ch:
            #print('mixer wheel_up: ', ch)
            if ch == metro_id:
                value = amp_metro.mul
                if value < 1.0: 
                    amp_metro.mul = value + STEP_VALUE_LOOP
                else:
                    amp_metro.mul = 1.0
            else:
                value = mixer._base_players[ch].gains[str(ch)][0]
                #print('mixer._base_players ', mixer._base_players[ch].gains[str(ch)][0])
                if value < 1.0:
                    mixer.setAmp(ch, 0, value + STEP_VALUE_LOOP)
                else: 
                     mixer.setAmp(ch, 0, 1.0)
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_DOWN and ch:
            #print('mixer wheel_down: ', ch)
            if ch == metro_id:
                value = amp_metro.mul
                if value > 0: 
                    amp_metro.mul = value - STEP_VALUE_LOOP
                else:
                    amp_metro.mul = 0
            else:
                value = mixer._base_players[ch].gains[str(ch)][0]
                if value > 0:
                    mixer.setAmp(ch, 0, value - STEP_VALUE_LOOP)
                else:
                    mixer.setAmp(ch, 0, 0)
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
            print('erase ', ch)
            #play_tables[ch][0].stop()
            mixer.delInput(ch)
            del play_tables[ch]
            del temp_tables[ch]
            #del rec_tables[ch]
            #print(play_tables)
            #print(rec_tables)
            event.value = 1000
            channel.value = 0
            
        elif e == METRO_STOP_PLAY_KEY:
            print('metro event')
            if metro_playing:
                m.stop()
                metro_playing = False
            else:
                m.play()
                metro_playing = True
            event.value = 1000
            channel.value = 0
            
        elif e == CHANGE_METRO_TIME:
            print('change time metro')
            t = metro_time.value
            m.setTime(t)
            event.value = 1000
            channel.value = 0
            
        if e == QUIT:
            print('Mixer Quit')
            m.stop()
            server.stop()
            return True
            sys.exit()

    
def rec_process(loop_id, event, duration):   #, mixer_tick ):
    
    print('start record process')
    e = event.value
    id = loop_id.value
    ready_to_record = False
    soundTable = None
    name = "/audio-%d" % id
    
    while True:
        e = event.value
        id = loop_id.value
        #tick = mixer_tick.value
        rec_play_dur = duration.value
        
#        if tick == 1 and ready_to_record:
#            print('rec proc real start fiil shared table')
#            print('rec proc time: ', time.time())
#            res = TableFill(res_out, share_tab)
#            ready_to_record = False
        
        if e == RECORD:
            length = rec_play_dur
            server = Server(audio='jack',  ichnls=1)
            server.deactivateMidi()
            server.boot().start()
            bufsize = server.getBufferSize()
            soundTable = NewTable(length=length, chnls=1, feedback=0.5)
            print('rec proc connect to shared_tab: ', name, length)
            share_tab = SharedTable(name, create=False, size=bufsize)
            #print('share_tab: ', dir(share_tab._base_objs))
            inp = Input(chnl=0)
            #
            # Rack of effects
            #
            res_out = Delay(inp, delay=.1, feedback=0.8, mul=0.2)
            #ready_to_record = True
            res = TableFill(res_out, share_tab)
            event.value = 1000
            loop_id.value = 0
        elif e == STOP_RECORD:
            print('rec proc stop record')
            print('length soundTable: ', soundTable.getDur())
            inp.stop()
            res.stop()
            res_out.stop()
            server.stop()
            return True

