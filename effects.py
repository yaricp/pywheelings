#!/usr/bin/env python3

from pyo import *

from settings import *

def comp(input):
    comp = Compress(input, thresh=-30, ratio=10, risetime=0.1,
                    falltime=0.1, knee=0.5).out()
    return comp
    

def gate(input):
    print('Gate')
    
    comp = Compress(input, thresh=-20, ratio=7, risetime=0.1,
                    falltime=0.1, knee=0.7)
    gate = Gate(comp,    
            thresh=-50, 
            risetime=2, 
            falltime=0.1, 
            lookahead=9, 
            mul=1.1).out()
    return gate
    
def pad2(input):
    gt = gate(input)
    freqs = [.254, .465, .657, .879, 1.23, 1.342, 1.654, 1.879]
    cdelay = [.0087, .0102, .0111, .01254, .0134, .01501, .01707, .0178]
#    # Modulation depths in seconds.
    adelay = [.001, .0012, .0013, .0014, .0015, .0016, .002, .0023]
    lfos = Sine(freqs, mul=adelay, add=cdelay)
    chorus = Delay(gt, lfos, feedback=.3, mul=1)
    b = STRev(chorus, inpos=0.7, revtime=7, cutoff=3000, bal=0.6, roomSize=300).out()
    return b
    

def pad1(input):
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
    
NOTES = [
          {'note': +5, 'amp': 0.7 },
          {'note': +12, 'amp': 0.7 },
          {'note': +17, 'amp': 0.2 },
          {'note': +24, 'amp': 0.4 }
        ]
        
def voices(input, notes=NOTES):
    
    wintables = [ WinTable(1) for i in notes ]
    # Length of the window in seconds.
    wsize = .1
    # Compute the transposition ratio.
    # Two reading heads out-of-phase.
    indexes = [Phasor(freq=-(pow(2.,row['note']/12.)-1)/wsize ,phase=[0,0.5]) for row in notes]
    # Each head reads the amplitude envelope...
    pointers = [Pointer(table=wintable, index=index, mul=.7) for wintable,index in zip(wintables,indexes)]
#    # Compressed input
#    comp = Compress(input, thresh=-29, ratio=3, risetime=0.1, 
#                    falltime=0.01, knee=0.5).mix(2)
#    # Gate with slow attack
#    gate = Gate(comp,
#                thresh=-80,
#                risetime=2,
#                falltime=0.01,
#                lookahead=5,
#                mul=0.8)
    voices = [Delay(input, delay=index*wsize, mul=pointer) for pointer,index in zip(pointers,indexes)]
    mm = Mixer(outs=1, chnls=len(voices), time=.025)
    mm.addInput(0, input)
    mm.setAmp(0,0,.7)
    count = 0
    for voice in voices:
        print('add voice: ', voice)
        count += 1
        mm.addInput(count, voice)
        mm.setAmp(count,0,notes[count-1]['amp'])
#    # Sets values for 8 LFO'ed delay lines (you can add more if you want!).
#    # LFO frequencies.
#    freqs = [.254, .465, .657, .879, 1.23, 1.342, 1.654, 1.879]
#    # Center delays in seconds.
#    cdelay = [.0087, .0102, .0111, .01254, .0134, .01501, .01707, .0178]
#    # Modulation depths in seconds.
#    adelay = [.001, .0012, .0013, .0014, .0015, .0016, .002, .0023]
#    # Create 8 sinusoidal LFOs with center delays "cdelay" and depths "adelay".
#    lfos = Sine(freqs, mul=adelay, add=cdelay)
#    # Create 8 modulated delay lines with a little feedback and send the signals
#    # to the output. Streams 1, 3, 5, 7 to the left and streams 2, 4, 6, 8 to the
#    # right (default behaviour of the out() method).
#    chorus = Delay(mm[0], lfos, feedback=.5, mul=.7)
#    output = STRev(mm[0], inpos=0.05, revtime=5, cutoff=5000, 
#                    bal=0.85, roomSize=5,firstRefGain=-2)
    return mm[0]
    
    
def bass(input):
    pva = PVAnal(input, size=1024)
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
    
    
def strings(input=None):
    
    comp = Compress(input, thresh=-29, ratio=6, risetime=0.01,
                    falltime=0.01, knee=0.5)
    dist = distortion(comp)
    gate = Gate(dist,    
            thresh=-75, 
            risetime=1, 
            falltime=0.01, 
            lookahead=5, 
            mul=.4)
    notes = [
          {'note': +5, 'amp': 0.7 },
          {'note': +12, 'amp': 0.7 },
          {'note': +17, 'amp': 0.5 },
          {'note': +24, 'amp': 0.4 }
        ]
    v = voices(comp, notes)
    output = STRev(v, inpos=0.05, revtime=5, cutoff=5000, 
                    bal=0.85, roomSize=5,firstRefGain=-2)
    
    return v
    
    
def viola(input):
    
    BP_CENTER_FREQ = 300        # Bandpass filter center frequency.
    BP_Q = 3                    # Bandpass Q (center_freq / Q = bandwidth).
    BOOST = 25                # Pre-boost (linear gain).
    LP_CUTOFF_FREQ = 3000       # Lowpass filter cutoff frequency.
    BALANCE = 0.8               # Balance dry - wet.

    # The transfert function is build in two phases.

    # 1. Transfert function for signal lower than 0.
    ##table = SawTable(order=7)
    table = ChebyTable([1,1,.33,0,.2,0,.143,0,.111])
    # 2. Transfert function for signal higher than 0.
    # First, create an exponential function from 1 (at the beginning of the table)
    # to 0 (in the middle of the table).
    ##high_table = SawTable(order=1)
    # Then, reverse the table’s data in time, to put the shape in the second
    # part of the table.
    ##high_table.reverse()

    # Finally, add the second table to the first, point by point.
    ##table.add(high_table)

    # Show the transfert function.
    table.view(title="Transfert function")

    # Bandpass filter and boost gain applied on input signal.
    bp = ButBP(input, freq=BP_CENTER_FREQ, q=BP_Q)
    boost = Sig(bp, mul=BOOST)
    
    # Apply the transfert function.
    sig = Lookup(table, boost)

    # Lowpass filter on the distorted signal.
    lp = ButLP(sig, freq=LP_CUTOFF_FREQ, mul=.7)
    # Balance between dry and wet signals.
    mixed = Interp(input, lp, interp=BALANCE)
    return mixed
     
    
    
def distortion(input):
    
    BP_CENTER_FREQ = 300        # Bandpass filter center frequency.
    BP_Q = 3                    # Bandpass Q (center_freq / Q = bandwidth).
    BOOST = 25                # Pre-boost (linear gain).
    LP_CUTOFF_FREQ = 3000       # Lowpass filter cutoff frequency.
    BALANCE = 0.8               # Balance dry - wet.

    # The transfert function is build in two phases.

    # 1. Transfert function for signal lower than 0.
    table = ExpTable([(0,-.25),(4096,0),(8192,0)], exp=30)

    # 2. Transfert function for signal higher than 0.
    # First, create an exponential function from 1 (at the beginning of the table)
    # to 0 (in the middle of the table).
    high_table = ExpTable([(0,1),(3000,2),(4096,0),(4598,0),(8192,0)],
                          exp=5, inverse=False)
    # Then, reverse the table’s data in time, to put the shape in the second
    # part of the table.
    high_table.reverse()

    # Finally, add the second table to the first, point by point.
    table.add(high_table)

    # Show the transfert function.
    table.view(title="Transfert function")

    # Bandpass filter and boost gain applied on input signal.
    bp = ButBP(input, freq=BP_CENTER_FREQ, q=BP_Q)
    boost = Sig(bp, mul=BOOST)
    
    # Apply the transfert function.
    sig = Lookup(table, boost)

    # Lowpass filter on the distorted signal.
    lp = ButLP(sig, freq=LP_CUTOFF_FREQ, mul=.7)
    # Balance between dry and wet signals.
    mixed = Interp(input, lp, interp=BALANCE)
    return mixed
    

if __name__ == "__main__":
    s = Server(audio='jack').boot().start()
    input = Input(0)
    #sin = Sine(freq=200)
    mixer = Mixer(outs=1, chnls=1, time=.025).out()
    out = viola(input)
    mixer.addInput('main', out)
    mixer.setAmp('main',0,0.5)
    s.gui(locals())
    sys.exit(0)
