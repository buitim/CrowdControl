# %%
import pyaudio
import struct
import numpy as np
import matplotlib.pyplot as plt

%matplotlib tk

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1  # MONO
BITRATE = 44100

# %%
p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=BITRATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

fig, ax = plt.subplots()

x = np.arrange(0, 2 * CHUNK, 2)
line, = ax.plot(x, np.random.rand(CHUNK))
ax.set_ylim(0, 255)
ax.set_xlim(0, CHUNK)


while True:
    data = stream.read(CHUNK)
    data_int = np.array(struct.unpack(
        str(2 * CHUNK) + 'B', data), dtype='b')[::2] + 127
    line.set_ydata(data_int)
    fig.canvas.draw()
    fig.canvas.flush_events()

ax.plot(data_int, '-')
plt.show()
