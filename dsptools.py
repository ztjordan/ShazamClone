from scipy import signal
from scipy.io.wavfile import read as read_wav

import math
import subprocess

import numpy as np


def convertToWav(infile, outfile):
	# convert an audio file into a wav file temporarily
	transcode_process = subprocess.Popen(['ffmpeg', '-i', infile, outfile])
	transcode_process.wait()

def convertToMono(rawData):
	if len(rawData.shape) == 1:
		monoData = rawData
	elif rawData.shape[1] == 2:
		monoData = np.average(rawData, 1)
	else:
		monoData = rawData
	return monoData
		
def dataToTimeSeries(fs, monoData):
	endTime = monoData.shape[0] / fs
	sampleTimes = np.linspace(0., endTime, monoData.shape[0])
	return np.transpose(np.array([sampleTimes, monoData]))

def decimateTimeSeries(data, fs, decimationRate):
	decimatedData = signal.decimate(data[:,1], decimationRate, ftype='fir')
	fs /= decimationRate
	timeSeries = dataToTimeSeries(fs, decimatedData)
	return (timeSeries, fs)

def defineNoteFrequencies(startFreq, stopFreq, startNote):
	toneNames = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
	toneCounter = toneNames.index(startNote)

	noteNames = []
	noteFrequencies = []
	currentFreq = startFreq
	currentNote = toneNames[toneCounter] + str(math.floor(toneCounter / 12))
	while currentFreq < stopFreq:
		noteNames.append(currentNote)
		noteFrequencies.append(currentFreq)
		toneCounter += 1
		currentNote = toneNames[toneCounter % 12] + str(math.floor(toneCounter / 12))
		currentFreq *= math.pow(2, 1/12)

	noteNames.append(currentNote)
	noteFrequencies.append(currentFreq)

	return (np.array(noteFrequencies), noteNames)

def computeNoiseEstimate(mat, nbands, nguards):
	noise_estimate = np.zeros(mat.shape)

	norm_filter = np.concatenate( (np.array([1/(2*nbands)]*nbands), np.array([0]*(2*nguards+1)), np.array([1/(2*nbands)]*nbands)) )

	for timeslice in range(mat.shape[-1]):
		noise_estimate[:,timeslice] = np.convolve(mat[:,timeslice], norm_filter, 'same')

	return noise_estimate

def denoiser(estimate, noise_estimate, threshold=0.1):
	denoised = np.zeros(estimate.shape)
	for timeslice in range(estimate.shape[-1]):
		for scale_index in range(estimate.shape[0]):
			if threshold*estimate[scale_index,timeslice] > noise_estimate[scale_index,timeslice]:
				denoised[scale_index,timeslice] = estimate[scale_index,timeslice] / noise_estimate[scale_index,timeslice]
	return denoised

def findPeaks(arr):
	peaks = np.zeros(len(arr),dtype=bool)
	for i in range(1, (len(arr)-1)):
		if (arr[i] > arr[i-1]) and (arr[i] > arr[i+1]):
			peaks[i] = True
	return peaks

def findPeaksInScale(cwtM):
	peaks = np.zeros(cwtM.shape, dtype=bool)
	for timeslice in range(cwtM.shape[-1]):
		peaks[:,timeslice] = findPeaks(cwtM[:,timeslice])
	return peaks

def orderPeaks(t, f, peaks):
	peakLocations = []
	flat = peaks.flatten('F') # Fortran style flattening, because column-major
	for ind in range(0,len(flat)):
		if flat[ind]:
			peakLocations.append(np.unravel_index(ind, peaks.shape, order='F'))
	return peakLocations

def generateAddresses(peakLocations, targetGroupSize=5, anchorLag=20):
	addressTable = {}
	for anchorInd in range(0, len(peakLocations)-targetGroupSize-anchorLag):
		(fAnchor, tAnchor) = peakLocations[anchorInd]
		groupInfo = []
		for groupMemberInd in range(anchorInd+anchorLag,anchorInd+targetGroupSize+anchorLag):
			(fMember, tMember) = peakLocations[groupMemberInd]
			tDelta = tMember - tAnchor
			groupInfo.append((fAnchor, fMember, tDelta))
		addressTable[tuple(groupInfo)] = tAnchor

	return addressTable

def cwtAnalysis(timeSeries, fs, noteFrequencies):
	(cwtF, cwtT, cwtM) = computeCWT(timeSeries, fs, noteFrequencies)
	(cwtT, cwtM) = decimateCWT(cwtT, cwtM, 8)
	(cwtT, cwtM) = decimateCWT(cwtT, cwtM, 4)

	# attempt to demean the signal before denoising
	#cwtM = signal.detrend(cwtM, type='constant')
	noiseEstimateCwtM = computeNoiseEstimate(cwtM, 4, 1)
	noiseRemovedCwtM = denoiser(cwtM, noiseEstimateCwtM)
	peakMapCwtM = findPeaksInScale(noiseRemovedCwtM)

	return (cwtT, cwtF, cwtM, noiseEstimateCwtM, noiseRemovedCwtM, peakMapCwtM)

def computeCWT(data, fs, frequencies):
	w = 6 * (2 * np.pi)
	widths = (w * fs) / (2 * np.pi * frequencies)
	#print('{}:{}'.format(frequencies, widths))
	cwtm = np.abs(signal.cwt(data[:,1], signal.morlet2, widths, w=w))
	#cwtm = np.abs(signal.cwt(data[:,1], signal.morlet2, widths))
	return (frequencies, data[:,0], cwtm)

def decimateCWT(cwtT, cwtM, decimationRate):
	dec_cwtM = signal.decimate(cwtM, decimationRate, ftype='fir', axis=1)
	return (cwtT[::decimationRate], dec_cwtM)

def computeSTFT(data, fs):
	dFreq = 10
	minWindowSize = fs / dFreq
	w = 2 ** math.ceil(math.log2(minWindowSize))
	overlap = w / 16
	f, t, stftm = signal.stft(data[:,1], fs, nperseg=w, noverlap=overlap)
	return (f, t, np.abs(stftm))

def sparsifyStft(stftT, stftF, stftM, noteFrequencies):
	sparseStftM = np.zeros((len(noteFrequencies), len(stftT)))

	for noteIndex in range(0, len(noteFrequencies)):
		binNumber = np.max(np.where(stftF < noteFrequencies[noteIndex]))
		sparseStftM[noteIndex,:] = stftM[binNumber,:]

	return (noteFrequencies, sparseStftM)

def stftAnalysis(timeSeries, fs, noteFrequencies):
	(stftF, stftT, stftM) = computeSTFT(timeSeries, fs)
	# attempt to demean the signal before denoising
	#demeanedStftM = signal.detrend(stftM, type='constant')
	# pick only actual note frequencies
	#(sparseStftF, sparseStftM) = sparsifyStft(stftT, stftF, stftM, noteFrequencies)
	noiseEstimateStftM = computeNoiseEstimate(stftM, 5, 1)
	noiseRemovedStftM = denoiser(stftM, noiseEstimateStftM, threshold=0.3)
	peakMapStftM = findPeaksInScale(noiseRemovedStftM)

	return (stftT, stftF, stftM, noiseEstimateStftM, noiseRemovedStftM, peakMapStftM)