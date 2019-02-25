import pyaudio
import wave
import sys
#import numpy
import sounddevice as sd

from settings import *

if CURRENT_RECORD_SYSTEM == JACK_RECORD_SYSTEM:
    import jack, numpy
elif CURRENT_RECORD_SYSTEM == ALSA_RECORD_SYSTEM:
    import alsaaudio



CHUNK = 1024
FORMAT = pyaudio.paInt16
#FORMAT = pyaudio.paInt24
CHANNELS = 1
RATE = 44100

if sys.platform == 'darwin':
    CHANNELS = 1


def record_sound(stop, filename):
    if CURRENT_RECORD_SYSTEM == ALSA_RECORD_SYSTEM:
        record_sound_alsa(stop, filename)
    elif CURRENT_RECORD_SYSTEM == PORTAUDIO_RECORD_SYSTEM:
        record_sound_portaudio(stop, filename)
    elif CURRENT_RECORD_SYSTEM == JACK_RECORD_SYSTEM:
        record_sound_jack(stop, filename)
    return 

#@profile_c
def record_sound_portaudio(stop, filename):
    '''Record sound by PortAudio'''
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    print('recording...')
    frames = []
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    while stop.value == 0:
        try:
            data = stream.read(CHUNK)
        except IOError:
            print(str(IOError.message) + str(IOError.strerror))
        wf.writeframes(b''.join(data))
    wf.close()
    stream.stop_stream()
    stream.close()
    p.terminate()
    return 


def record_sound_alsa(stop, filename):
    '''Record sound by ALSA'''
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE)
    inp.setchannels(CHANNELS )
    inp.setrate(RATE)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    inp.setperiodsize(CHUNK)

    w = wave.open(filename, 'w')
    w.setnchannels(CHANNELS )
    w.setsampwidth(2)
    w.setframerate(RATE)

    while stop.value == 0:
        l, data = inp.read()
        a = numpy.fromstring(data, dtype='int16')
        #print numpy.abs(a).mean()
        w.writeframes(data)
    w.close()
        
def record_sound_jack(stop, filename):
    '''Record sound by Jack server ports'''
    w = wave.open(filename, 'w')
    w.setnchannels(CHANNELS )
    w.setsampwidth(2)
    w.setframerate(RATE)
    
    client = jack.Client("PyWheelsClient")
    inpt = client.inports.register("input_1")
    print( 'register input')
    print(client.get_ports())
    client.activate()
    print( 'activate')
    client.connect("system:capture_1", "PyWheelsClient:input_1")
    print( 'connect')
    capture = client.get_ports(is_physical=True, is_output=True)
    print(capture)
    if not capture:
        raise RuntimeError("No physical capture ports")
    while stop.value == 0:
        data = inpt.get_buffer()
        #a = numpy.fromstring( data, dtype='float32')
        #print( numpy.abs(a).mean())
        w.writeframes(b''.join(data))
    w.close()
    client.deactivate()
    
    
def record_sound_pulse_audio(stop,filename):
    '''Record sound  by pulseaudio server '''
    