import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft

import pdb

fs = 20
f1 = 5
f2 = 5.5

t = 1

sampleTimes = np.arange(1 * fs) / fs
fullSampleTimes = np.arange(10 * fs) / fs
frequencies = np.linspace(0, fs, 20)
highResFrequencies = np.linspace(0, fs, 200)

sig = np.sin(2 * np.pi * f1 * sampleTimes) + np.sin(2 * np.pi * f2 * sampleTimes)
paddedSig = np.pad(sig, (0,180), mode='constant')


fullSig = np.sin(2 * np.pi * f1 * fullSampleTimes) + np.sin(2 * np.pi * f2 * fullSampleTimes)

shortFreq = fft(sig)
paddedFreq = fft(paddedSig)
fullFreq = fft(fullSig)

fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
fig.suptitle('Sequence Padding and FFT Resolution (5 Hz + 5.5 Hz)', fontsize=16)

ax1.plot(sampleTimes, sig)
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Amplitude')

ax2.plot(frequencies, np.abs(shortFreq))
ax2.set_xlabel('Frequency (Hz)')
ax2.set_ylabel('|Amplitude|')

ax3.plot(fullSampleTimes, paddedSig)
ax3.set_xlabel('Time (s)')
ax3.set_ylabel('Amplitude')

ax4.plot(highResFrequencies, np.abs(paddedFreq))
ax4.set_xlabel('Frequency (Hz)')
ax4.set_ylabel('|Amplitude|')

ax5.plot(fullSampleTimes, fullSig)
ax5.set_xlabel('Time (s)')
ax5.set_ylabel('Amplitude')

ax6.plot(highResFrequencies, np.abs(fullFreq))
ax6.set_xlabel('Frequency (Hz)')
ax6.set_ylabel('|Amplitude|')

fig.savefig('test.jpg')
plt.show(block=True)

