import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

import struct
import pyaudio
from scipy.fftpack import fft
from scipy.stats import stats

import sys
import time

# CREDIT: Mark Jay #


class AudioStream(object):
    # Local Variables #
    averageValue = np.zeros(2048)
    # dataHistory = np.zeros((50, 2048))
    dataHistory = np.zeros(50)
    iteratorCount = 0
    previousamplitudeAverage = 0

    def __init__(self):

        # pyqtgraph stuff
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='CrowdControl')
        self.win.setWindowTitle('CrowdControl')
        self.win.setGeometry(5, 115, 1910, 1070)

        wf_xlabels = [(0, '0'), (2048, '2048'),
                      (4096, '4096')]  # (Integer, Label)
        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setTicks([wf_xlabels])  # Set labels to ticks

        wf_ylabels = [(0, '0'), (128, '128'), (255, '255')]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        sp_xlabels = [
            (np.log10(10), '10'), (np.log10(100), '100'),
            (np.log10(1000), '1000'), (np.log10(22050), '22050')
        ]
        sp_xaxis = pg.AxisItem(orientation='bottom')
        sp_xaxis.setTicks([sp_xlabels])

        self.waveform = self.win.addPlot(
            title='WAVEFORM', axisItems={'bottom': wf_xaxis, 'left': wf_yaxis},
            # title='WAVEFORM', row=1, col=1, axisItems={'bottom': wf_xaxis, 'left': wf_yaxis},
        )
        # self.average = self.win.addPlot(
        #     title='AVERAGE', row=2, col=1)
        # self.spectrum = self.win.addPlot(
        #     title='SPECTRUM', row=2, col=1, axisItems={'bottom': sp_xaxis},
        # )

        # pyaudio stuff
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024 * 2

        # PyAudio stream
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            output=True,
            frames_per_buffer=self.CHUNK,
        )
        # waveform and spectrum x points
        self.x = np.arange(0, 2 * self.CHUNK, 2)  # Samples
        self.f = np.linspace(0, self.RATE / 2, self.CHUNK / 2)  # Frequencies

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

        # Show the plot
    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.waveform.plot(pen='c', width=3)
                self.waveform.setYRange(0, 255, padding=0)
                self.waveform.setXRange(0, 2 * self.CHUNK, padding=0.005)
            if name == 'average':
                self.traces[name] = self.average.plot(pen='m', width=3)
                self.average.setYRange(128, 165, padding=0)
                self.average.setXRange(0, 2 * self.CHUNK, padding=0.005)
            # if name == 'average':
            #     self.traces[name] = self.average.plot(pen='m', width=3)
            #     # Logarithmic plot for both axes
            #     self.average.setLogMode(x=True, y=True)
            #     self.average.setYRange(-4, 0, padding=0)
            #     self.average.setXRange(
            #         np.log10(20), np.log10(self.RATE / 2), padding=0.005)

    # Python doesn't like it when I don't have self as the first arg. Maybe because I'm declaring this as a method?
    def approximateRollingAverage(self, wf_data):
        # Change this threshold depending on the equipment. Tested using MacBook mic so YMMV
        amplitudeThreshold = 10
        dataAmplitude = abs(np.median(abs(wf_data)) - 128)

        # Each index will be a continuing sum from the last wf_data
        # currentIndex used modulo method to make a pseudo-circular array
        currentIndex = self.iteratorCount % len(self.dataHistory)
        self.dataHistory[currentIndex] = dataAmplitude

        amplitudeAverage = float('%.3f' % (np.average(self.dataHistory)))

        print("== Amplitude Average: ", amplitudeAverage,
              "\t Current Amplitude: ", dataAmplitude)

        if (dataAmplitude - self.previousamplitudeAverage) >= amplitudeThreshold:
            print("\n== Significant change detected\n")

        # Sidenote... I hate how python doesnt have the increment shorthand...
        self.iteratorCount += 1
        self.previousamplitudeAverage = amplitudeAverage

    def update(self):

        wf_data = self.stream.read(self.CHUNK)
        wf_data = struct.unpack(str(2 * self.CHUNK) + 'B', wf_data)
        wf_data = np.array(wf_data, dtype='b')[::2] + 128
        self.set_plotdata(name='waveform', data_x=self.x, data_y=wf_data)

        self.approximateRollingAverage(wf_data=wf_data)

        # sp_data = fft(np.array(wf_data, dtype='int8') - 128)
        # sp_data = np.abs(sp_data[0:int(self.CHUNK / 2)]
        #                  ) * 2 / (128 * self.CHUNK)
        # self.set_plotdata(name='spectrum', data_x=self.f, data_y=sp_data)

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


if __name__ == '__main__':

    audio_app = AudioStream()
    audio_app.animation()
