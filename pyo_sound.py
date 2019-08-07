import os, sys, time, random, multiprocessing, json
from pyo import *

from settings import *
from effects import *

HOME_DIR = os.path.dirname(os.path.abspath(__file__))

def get_personal_settings():
    """Get Persoaln settings from file"""
    with open(os.path.join(HOME_DIR,'settings/personal.json'), 'r') as file:
        text = file.read()
        objects = json.loads(text)
        print(objects)
        return objects

def vocoder(input):
    print('start vocoder')
    # Second sound - rich and stable spectrum.
    excite = Noise(0.2)

    # LFOs to modulated every parameters of the Vocoder object.
    lf1 = Sine(freq=0.1, phase=random.random()).range(60, 100)
    lf2 = Sine(freq=0.11, phase=random.random()).range(1.05, 1.5)
    lf3 = Sine(freq=0.07, phase=random.random()).range(1, 20)
    lf4 = Sine(freq=0.06, phase=random.random()).range(0.01, 0.99)

    output = Vocoder(input, excite, freq=lf1, spread=lf2, q=lf3, slope=lf4, stages=32)
    return output
    
    
def echo(input):
    print('start echo')
    output = STRev(input, inpos=0.5, revtime=1.5, cutoff=5000, bal=1, roomSize=.8, firstRefGain=-3)
    return output
    
def pads(input):
    print('start pads')
    output = input
    return output
    
dict_effects_by_loops = {
        1: pads, 
        #2: voices, 
        #3: viola, 
        #4: strings
}

def load_effects(input, channel):
    print('start effects')
    output = input
    if channel in dict_effects_by_loops:
        output = dict_effects_by_loops[channel](input)
    return output
    
    
def toggle_section(mixer, play_tables, list_loops, direct=None):
    for k, i in list_loops.items():
        if not i:
            if direct == '>':
                mute(mixer, play_tables, int(k))
            else:
                unmute(mixer, play_tables, int(k))
        else:
            if direct == '>':
                unmute(mixer, play_tables, int(k))
            else:
                mute(mixer, play_tables, int(k))
            
    
def record(mixer, play_tables, rec_play_dur, inp_after_effects, list_loops):
    newTable = NewTable(length=rec_play_dur, chnls=1, feedback=0)
    print('mixer start rec:', time.time(), 'duration: ', rec_play_dur)
    table_rec = TableRec(inp_after_effects, table=newTable, fadetime=0).play()
    print('list_loops: ', list_loops)
    toggle_section(mixer, play_tables, list_loops, '>')
    return table_rec
   
   
def stop_record(mixer, inp_main, table_rec, play_tables, rec_play_dur, ch):
    print('mixer stop record and start play ', ch)
    table_rec.stop()
    print('max duration: ',  table_rec.table.getDur())
    print('real duration: ', rec_play_dur)
    mixer.delInput('main')
    inp_after_effects = load_effects(inp_main, ch+1)
    mixer.addInput('main', inp_after_effects)
    mixer.setAmp('main',0,NORMAL_VALUE_LOOP*1.3)
    #dur = 0
    if not ch in play_tables:
        looper = Looper( table=table_rec.table, 
                        start=0.05,
                        dur=rec_play_dur, 
                        xfade=0, 
                        interp=1, 
                        mul=1).out()
        play_tables.update({ch: [looper, 0, rec_play_dur, time.time()]})

    mixer.addInput(ch, looper)
    mixer.setAmp(ch,0,.5)
    return mixer, play_tables
   
   
def mute(mixer, play_tables, ch):
    print('mixer MUTE:', ch)
    mixer.setAmp(ch,0,0)
    play_tables[ch][0].mul = 0
    
    
def unmute(mixer, play_tables, ch):
    print('mixer UNMUTE:', ch)
    mixer.setAmp(ch,0,NORMAL_VALUE_LOOP)
    play_tables[ch][0].mul = 1
   
   
def volume(mixer, metro_id, amp_metro, ch, direct):
    #print('mixer wheel_up: ', ch)
    
    if ch == metro_id:
        value = amp_metro.mul
        if direct == '+':
            if value < 1.0: 
                amp_metro.mul = value + STEP_VALUE_LOOP
            else:
                amp_metro.mul = 1.0
        else:
            if value > 0: 
                amp_metro.mul = value - STEP_VALUE_LOOP
            else:
                amp_metro.mul = 0
    else:
        value = mixer._base_players[ch].gains[str(ch)][0]
        if direct == '+':
            if value < 1.0:
                mixer.setAmp(ch, 0, value + STEP_VALUE_LOOP)
            else: 
                mixer.setAmp(ch, 0, 1.0)
        else:
            if value > 0:
                mixer.setAmp(ch, 0, value - STEP_VALUE_LOOP)
            else:
                mixer.setAmp(ch, 0, 0)
                

def mixer_loops(event, 
                channel, 
                metro_time, 
                tick, 
                duration, 
                list_loops):
    print("Start Mixer")
    #print("Audio host APIS:")
    pa_list_host_apis()
    pa_list_devices()
    print("Default input device: %i" % pa_get_default_input())
    print("Default output device: %i" % pa_get_default_output())
    server = Server(audio=AUDIO_SYSTEM, nchnls=2)
    server.deactivateMidi()
    server.boot().start()
    bufsize = server.getBufferSize()
    mixer = Mixer(outs=1, chnls=COUNT_IN_ROW * COUNT_ROWS, time=.025).out()
    metro_id = COUNT_IN_ROW * COUNT_ROWS + 1
    #print('metro_id: ', metro_id)
    #
    #Load Personal settings from file
    #
    #pers_settings = get_personal_settings()
    #dur_loops = pers_settings['dur_loops']
    e = event.value
    ch = channel.value
    rec_tables = {}
    play_tables = {}
    #temp_tables = {}
    metro_playing = False
    t = metro_time.value
    m = Metro(time=t)
    #print('m: ', m)
    def send_tick():
        #print('tick:',  time.time())
        tick.value = 1
    tf = TrigFunc(m, send_tick)
    #start_play_metro = Trig()
    cos_t = CosTable([(0,0), (50,1), (250,.3), (8191,0)])
    amp_metro = TrigEnv(m, table=cos_t, dur=.25, mul=.1)
    a = Sine(freq=1000, mul=amp_metro).out()
    print('define metronome')
    #First channel baypass
    inp_main = Input(chnl=0)
    
    #loading first effect
    inp_after_effects = load_effects(inp_main, 1)
    
    mixer.addInput('main', inp_after_effects)
    mixer.setAmp('main',0,NORMAL_VALUE_LOOP*1.4)
    
    #Start main cyrcle
    
    while True:
        e = event.value
        ch = channel.value
        rec_play_dur = duration.value
        
        
        if ch == 0 and e == 1000 :

            for play_t in play_tables:
                #last_period = False

                delta = round(play_tables[play_t][2]-time.time()-play_tables[play_t][3], 3)
                if play_tables[play_t][1] == 0 and delta <= 0.05:
                    #print('change start time')
                    #print('delta: ',0)
                    play_tables[play_t][1] = 1
                    play_tables[play_t][0].setStart(0.01)
                    play_tables[play_t][0].setXfade(0)
                    play_tables[play_t][0].loopnow()


        if e == NEW_LOOP and ch and not (ch in rec_tables):
            table_rec = record( mixer,
                                play_tables, 
                                rec_play_dur,
                                inp_after_effects, 
                                list_loops )
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_RECORD and ch:
            mixer, play_tables = stop_record(mixer, 
                                            inp_main, 
                                            table_rec, 
                                            play_tables, 
                                            rec_play_dur,
                                            ch)
            event.value = 1000
            channel.value = 0
            
        elif e == STOP_PLAY and ch:
            print('mixer stop play')
            play_tables[ch][0].stop()
            event.value = 1000
            channel.value = 0
        
        elif e == PLAY and ch:
            print('mixer start play')
            play_tables[ch][0].out()
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_UP and ch:
            volume(mixer, metro_id, amp_metro, ch, '+')
            event.value = 1000
            channel.value = 0
            
        elif e == WHEEL_DOWN and ch:
            volume(mixer, metro_id, amp_metro, ch, '-')
            event.value = 1000
            channel.value = 0
            
        elif e == MUTE and ch:
            mute(mixer, play_tables, ch)
            event.value = 1000
            channel.value = 0
            
        elif e == UNMUTE and ch:
            unmute(mixer, play_tables, ch)
            event.value = 1000
            channel.value = 0
            
#        elif e == MUTE_ALL and ch:
#            mute
            
        elif e == TOGGLE_SECTION:
            print('Mixer toggle')
            toggle_section(mixer, play_tables, list_loops)
            event.value = 1000
            channel.value = 0
            
        elif e == ERASE and ch:
            print('Mixer erase ', ch)
            mixer.delInput(ch)
            play_tables[ch][0].stop()
            del play_tables[ch]
            event.value = 1000
            channel.value = 0
            
        elif e == ERASE_ALL:
            print('Mixer erase all:')
            #for k, i list_loops.items():
            for k, i in play_tables.items():
                i[0].stop()
            play_tables = {}
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
