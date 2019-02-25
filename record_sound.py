
#import argparse
#import tempfile
import queue
import sys
import os
from pathlib import Path

#def int_or_str(text):
#    """Helper function for argument parsing."""
#    try:
#        return int(text)
#    except ValueError:
#        return text

def record(stop, filename):
    """ Recording in the file of loop"""

    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy  # Make sure NumPy is loaded before it is used in the callback
        assert numpy  # avoid "imported but unused" message (W0611)
        
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        print(cur_dir)
        print(os.path.join(cur_dir, filename))
        device = None
        device_info = sd.query_devices(device, 'input')
        channels = 1
        samplerate = int(device_info['default_samplerate'])
        if Path(os.path.join(cur_dir, filename)).exists():
            os.remove(os.path.join(cur_dir, filename))
        file = open(filename, 'wb')
#        file = tempfile.mktemp(prefix=filename,
#                                        suffix='.wav', dir='')
        print(file)
        q = queue.Queue()

        def callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(file, mode='x', samplerate=samplerate,
                          channels=channels) as file:
            with sd.InputStream(samplerate=samplerate, device=device,
                                channels=channels, callback=callback):
                while stop.value == 0:
                    file.write(q.get())

    except Exception as e:
        sys.exit(type(e).__name__ + ': ' + str(e))
