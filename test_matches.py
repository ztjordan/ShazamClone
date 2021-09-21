import argparse
import os
import random

from scipy.io.wavfile import read as read_wav
import numpy as np

import dsptools
import plottools
import dbtools



import pdb

def listSongs(musicDir):
	songs = []
	for (dirpath, dirnames, filenames) in os.walk(musicDir):
		for f in filenames:
			songFullPath = os.path.join(dirpath, f)
			tmp = os.path.basename(songFullPath)
			songName, fileExtension = os.path.splitext(tmp)
			if fileExtension in ['.wav', '.flac', '.mp3']:
				songs.append((songFullPath, songName))
	return songs

def main(args):
	fingerprintMethod = 'STFT'
	songLibraryInfo = listSongs(args.library)

	#tmpDir = tempfile.TemporaryDirectory()
	while True:
		(songFile, songName) = random.choice(songLibraryInfo)

		print('Performing match test with {}'.format(songName))

		fs, rawData = read_wav(songFile)
		monoData = dsptools.convertToMono(rawData)
		timeSeries = dsptools.dataToTimeSeries(fs, monoData)

		snippetLength = 10
		maxStartTime = timeSeries[-1,0] - snippetLength
		sampleTimes = timeSeries[:,0]
		# np.random.choice is fussy about the random number seed. Just generate random choices until one is acceptable
		startTime = maxStartTime
		while startTime >= maxStartTime:
			startSample = random.randint(0, sampleTimes.shape[0]-1)
			startTime = sampleTimes[startSample]
		endTime = startTime + snippetLength

		snippet = timeSeries[np.nonzero((timeSeries[:,0] >= startTime) & (timeSeries[:,0] < endTime))]
		snippet[:,0] -= startTime

		decimationRate = 4
		(snippet, fs) = dsptools.decimateTimeSeries(snippet, fs, decimationRate)

		minFreq = 27.5 # A in sub-contra (https://en.wikipedia.org/wiki/Piano_key_frequencies)
		maxFreq = 4186.009 # C8
		(noteFrequencies, noteNames) = dsptools.defineNoteFrequencies(minFreq, maxFreq, 'A')

		method = 'STFT'
		if method == 'CWT':
			(testCwtT, testCwtF, testCwtM, testNoiseEstimateCwtM, testNoiseRemovedCwtM, testPeakMapCwtM) = dsptools.cwtAnalysis(snippet, fs, noteFrequencies)
			testPeakLocations = dsptools.orderPeaks(testCwtT, testCwtF, testPeakMapCwtM)
			testTable = dsptools.generateConstellations(testPeakLocations, testPeakMapCwtM)
			#plottools.plotCwt(testCwtT, noteFrequencies, testCwtM, noteNames)
		elif method == 'STFT':
			(testStftT, testStftF, testStftM, testNoiseEstimateStftM, testNoiseRemovedStftM, testPeakMapStftM) = dsptools.stftAnalysis(snippet, fs, noteFrequencies)
			testPeakLocations = dsptools.orderPeaks(testStftT, testStftF, testPeakMapStftM)

			timeOffset = 5
			timeWindow = 2
			frequencyWindow = 10
			testConstellations = dsptools.generateConstellations(testPeakLocations, testPeakMapStftM, timeOffset, timeWindow, frequencyWindow)
			#plottools.plotStft(testStftT, testStftF, testPeakMapStftM, noteFrequencies, noteNames, figName='Ten Second Snippet from {}'.format(songName))

		dbtools.songMatch(args.dbfile, testConstellations)


		bestMatchScore = 0.0
		bestMatchSong = ''

		songScores = []

		if bestMatchSong == songName:
			match = True
		else:
			match = False

		print('Best match: {} : {} ({}%)'.format(bestMatchSong, match, bestMatchScore))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to use for testing')
	parser.add_argument('dbfile', help='Location of fingerprints for matching')
	args = parser.parse_args()
	main(args)
