

import pyaudio
import wave
import sys


CHUNK = 1024
FORMAT = pyaudio.paInt16
#FORMAT = pyaudio.paInt24
CHANNELS = 1
RATE = 44100

if sys.platform == 'darwin':
    CHANNELS = 1


#@profile_c
def record_sound(stop, filename):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    while stop.value == 0:
        try:
            data = stream.read(CHUNK)
        except IOError:
            print str(IOError.message) + str(IOError.strerror)
        wf.writeframes(b''.join(data))
    wf.close()
    stream.stop_stream()
    stream.close()
    p.terminate()
    return 

