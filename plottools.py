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

def plotStft(x, y, data, **kwargs):#logScale=False, noteFrequencies=None, noteNames=None, figName='', dest=None):

	options = {
		'figName' : None,
		'noteFrequencies' : None,
		'noteNames' : None,
		'logScale' : True,
		'block' : False,
		'dest' : None }

	options.update(kwargs)

	fig = plt.figure()
	if options['figName']:
		plt.suptitle(options['figName'])
	plt.pcolormesh(x, y, data, cmap='viridis', shading='gouraud')
	
	if options['logScale']:
		plt.semilogy(base=2)

	if options['noteFrequencies'] is not None and options['noteNames'] is not None:
		plt.ylabel('Note Name')
		plt.yticks(options['noteFrequencies'], options['noteNames'])
	else:
		plt.ylabel('Frequency (Hz)')



	plt.xlabel('Time (s)')
	
	plt.show(block=options['block'])
	if options['dest']:
		fig.savefig(options['dest'])
	plt.close(fig)

def plotNoiseEstimator(f, data, noiseEstimate, denoised, **kwargs):

	options = {
		'block' : False,
		'dest' : None }

	options.update(kwargs)

	fig = plt.figure()
	
	plt.plot(f, data)
	plt.plot(f, noiseEstimate)
	plt.plot(f, denoised)

	plt.suptitle('Noise Estimator Example (Single Time Slice)')

	plt.xlabel('Frequency (Hz)')
	plt.ylabel('|Amplitude|')

	plt.legend(['Estimate', 'Noise Estimate', 'Noise Removed'])
	
	plt.show(block=options['block'])
	if options['dest']:
		fig.savefig(options['dest'])