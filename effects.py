#!/usr/bin/env python3

from pyo import *

from settings import *


def gate(input):
    print('Start Gate')
    env = WinTable(8)
    env1 = WinTable(8)
    # Length of the window in seconds.
    wsize = .1
    wsize1 = .1
    # Amount of transposition in semitones.
    trans = +5
    trans1 = +10
    # Compute the transposition ratio.
    ratio = pow(2., trans/12.)
    ratio1 = pow(2., trans1/12.)
    # Compute the reading head speed.
    rate = -(ratio-1) / wsize
    rate1 = -(ratio1-1) / wsize1
    # Two reading heads out-of-phase.
    ind1 = Phasor(freq=rate, phase=[0,0.5])
    ind2 = Phasor(freq=rate1, phase=[0,0.3])
    # Each head reads the amplitude envelope...
    win = Pointer(table=env, index=ind1, mul=.7)
    win1 = Pointer(table=env1, index=ind2, mul=.7)
    gate = Gate(input,    
            thresh=-75, 
            risetime=1, 
            falltime=0.01, 
            lookahead=5, 
            mul=.4)
    voice1 = Delay(gate, delay=ind1*wsize, mul=win).mix(1)
    voice2 = Delay(gate, delay=ind2*wsize1, mul=win1).mix(2)
    output = voice2
    
    return output
    

def voices(input):
    notes = [
          {'note': +5, 'amp': 0.7 },
          {'note': +12, 'amp': 0.7 },
          {'note': +17, 'amp': 0.5 },
          {'note': +24, 'amp': 0.4 }
        ]
    wintables = [ WinTable(1) for i in notes ]
    # Length of the window in seconds.
    wsize = .1
    # Compute the transposition ratio.
    # Two reading heads out-of-phase.
    indexes = [Phasor(freq=-(pow(2.,row['note']/12.)-1)/wsize ,phase=[0,0.5]) for row in notes]
    # Each head reads the amplitude envelope...
    pointers = [Pointer(table=wintable, index=index, mul=.7) for wintable,index in zip(wintables,indexes)]
    # Compressed input
    comp = Compress(input, thresh=-29, ratio=3, risetime=0.1, 
                    falltime=0.01, knee=0.5).mix(2)
    # Gate with slow attack
    gate = Gate(comp,
                thresh=-80,
                risetime=2,
                falltime=0.01,
                lookahead=5,
                mul=0.8)
    voices = [Delay(gate, delay=index*wsize, mul=pointer) for pointer,index in zip(pointers,indexes)]
    mm = Mixer(outs=1, chnls=len(voices), time=.025)
    mm.addInput(0, gate)
    mm.setAmp(0,0,.7)
    count = 0
    for voice in voices:
        print('add voice: ', voice)
        count += 1
        mm.addInput(count, voice)
        mm.setAmp(count,0,notes[count-1]['amp'])
    # Sets values for 8 LFO'ed delay lines (you can add more if you want!).
    # LFO frequencies.
    freqs = [.254, .465, .657, .879, 1.23, 1.342, 1.654, 1.879]
    # Center delays in seconds.
    cdelay = [.0087, .0102, .0111, .01254, .0134, .01501, .01707, .0178]
    # Modulation depths in seconds.
    adelay = [.001, .0012, .0013, .0014, .0015, .0016, .002, .0023]
    # Create 8 sinusoidal LFOs with center delays "cdelay" and depths "adelay".
    lfos = Sine(freqs, mul=adelay, add=cdelay)
    # Create 8 modulated delay lines with a little feedback and send the signals
    # to the output. Streams 1, 3, 5, 7 to the left and streams 2, 4, 6, 8 to the
    # right (default behaviour of the out() method).
    chorus = Delay(mm[0], lfos, feedback=.5, mul=.7)
    output = STRev(mm[0], inpos=0.05, revtime=5, cutoff=5000, 
                    bal=0.85, roomSize=5,firstRefGain=-2)
    return output
    
    
def bass(input):
    pva = PVAnal(inp, size=1024)
    pvt = PVTranspose(pva, transpo=0.5)
    output = PVSynth(pvt)
    return output
    
    
def pitch_bass(input, type='fast_bass'):
    
    settings = {
        'slow_bass':{'wsize': 0.1, 'phase': 0.5}, 
        'fast_bass': {'wsize': 0.07, 'phase': 0.4}
        }
    comp = Compress(input, thresh=-29, ratio=6, risetime=0.01,
                    falltime=0.01, knee=0.5)
    env = WinTable(8)
    wsize = settings[type]['wsize']
    trans = -12
    ratio = pow(2., trans/12.)
    rate = -(ratio-1) / wsize
    ind = Phasor(freq=rate, phase=[0,settings[type]['phase']])
    win = Pointer(table=env, index=ind, mul=.9)
    output = Delay(comp, delay=ind*wsize, mul=win)
    return output
    
