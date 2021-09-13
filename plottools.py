import matplotlib.pyplot as plt
import numpy as np

def plotTimeSeries(timeSeries):
	plt.figure()
	plt.plot(timeSeries[:,0], timeSeries[:,1])
	plt.xlabel("Time [s]")
	plt.ylabel("Amplitude")
	plt.show()

def plotCwt(x, y, data, noteNames, figName='', dest=None):
	fig = plt.figure()
	if figName:
		plt.suptitle(figName)
	plt.pcolormesh(x, y, data, cmap='viridis', shading='gouraud')
	plt.semilogy(base=2)
	plt.yticks(y, noteNames)
	plt.show(block=True)
	if dest:
		fig.savefig(dest)
	plt.close(fig)

def plotStft(x, y, data, noteFrequencies, noteNames, figName='', dest=None):
	fig = plt.figure()
	if figName:
		plt.suptitle(figName)
	plt.pcolormesh(x, y, data, cmap='viridis', shading='gouraud')
	#plt.semilogy(base=2)
	plt.xlabel('Time (s)')
	plt.ylabel('Frequency (Hz)')
	#plt.yticks(noteFrequencies, noteNames)
	plt.show(block=True)
	if dest:
		fig.savefig(dest)
	plt.close(fig)

def plotNoiseEstimator(f, data, noiseEstimate, denoised):
	plt.plot(f[1:200], data[1:200,229])
	plt.plot(f[1:200], noiseEstimate[1:200,229])
	plt.plot(f[1:200], denoised[1:200,229])
	plt.suptitle('Noise Estimator Example (Single Time Slice)')
	plt.xlabel('Frequency (Hz)')
	plt.ylabel('|Amplitude|')

	plt.legend(['Estimate', 'Noise Estimate', 'Noise Removed'])
	plt.show(block=True)