import argparse
import csv
import os
import random
import tempfile

from scipy.io.wavfile import read as read_wav

import dsptools
import plottools

import numpy as np

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

		(filename, fileExtension) = os.path.splitext(songFile)
		if fileExtension != '.wav':
			# if it's not a wav, convert it to wav to read it
			tmpFilename = os.path.join(tmpDir.name, songName + '.wav')
			dsptools.convertToWav(songFile, tmpFilename)
		else:
			tmpFilename = songFile

		snippetLength = 10
		fs, rawData = read_wav(tmpFilename)
		monoData = dsptools.convertToMono(rawData)
		timeSeries = dsptools.dataToTimeSeries(fs, monoData)

		maxStartTime = timeSeries[-1,0] - snippetLength
		sampleTimes = timeSeries[:,0]
		# np.random.choice is fussy about the random number seed. Just generate random choices until one is acceptable
		startTime = maxStartTime
		while startTime >= maxStartTime:
			startSample = random.randint(0, sampleTimes.shape[0]-1)
			startTime = sampleTimes[startSample]
		endTime = startTime + 10

		snippet = timeSeries[np.nonzero((timeSeries[:,0] >= startTime) & (timeSeries[:,0] < endTime))]
		snippet[:,0] -= startTime

		minFreq = 27.5 # A in sub-contra (https://en.wikipedia.org/wiki/Piano_key_frequencies)
		maxFreq = 4186.009 # C8
		(noteFrequencies, noteNames) = dsptools.defineNoteFrequencies(minFreq, maxFreq, 'A')

		method = 'STFT'
		if method == 'CWT':
			(testCwtT, testCwtF, testCwtM, testNoiseEstimateCwtM, testNoiseRemovedCwtM, testPeakMapCwtM) = dsptools.cwtAnalysis(snippet, fs, noteFrequencies)
			testPeakLocations = dsptools.orderPeaks(testCwtT, testCwtF, testPeakMapCwtM)
			testTable = dsptools.generateAddresses(testPeakLocations)
			plottools.plotCwt(testCwtT, noteFrequencies, testCwtM, noteNames)
		elif method == 'STFT':
			(testStftT, testStftF, testStftM, testNoiseEstimateStftM, testNoiseRemovedStftM, testPeakMapStftM) = dsptools.stftAnalysis(snippet, fs, noteFrequencies)
			testPeakLocations = dsptools.orderPeaks(testStftT, testStftF, testPeakMapStftM)
			testTable = dsptools.generateAddresses(testPeakLocations)
			#plottools.plotStft(testStftT, testStftF, testPeakMapStftM, noteFrequencies, noteNames, figName='Ten Second Snippet from {}'.format(songName))

		bestMatchScore = 0.0
		bestMatchSong = ''

		songScores = []

		for fingerPrintCSV in os.listdir(args.archive):
			dbName, ext = os.path.splitext(fingerPrintCSV)
			databaseTable = {}
			with open(os.path.join(args.archive, fingerPrintCSV), newline='') as csvFile:
				csvReader = csv.DictReader(csvFile)
				for row in csvReader:
					entry = []
					numAnchors = 1
					entriesPerPoint = 3
					numPoints = int((len(row) - numAnchors) / entriesPerPoint) # it is very strange that this must be cast to int
					for ptNum in range(numPoints):
						entry.append(  (int(row['anchorFreq_' + str(ptNum)]), int(row['pointFreq_' + str(ptNum)]), int(row['deltaTime_' + str(ptNum)]))  )
					databaseTable[tuple(entry)] = row['anchorTime']

			positive = 0
			negative = 0
			#breakpoint()
			for testGroup in testTable.keys():
				if testGroup in databaseTable:
					positive += 1
				else:
					negative += 1

			accuracy = positive / (positive + negative) * 100
			songScores.append((dbName, accuracy))

			#print('{} to {} match: {}%'.format(dbName, songName, accuracy))

			if (accuracy > bestMatchScore):
				bestMatchScore = accuracy
				bestMatchSong = dbName


		if bestMatchSong == songName:
			match = True
		else:
			match = False

		print('Best match: {} : {} ({}%)'.format(bestMatchSong, match, bestMatchScore))

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to use for testing')
	parser.add_argument('archive', help='Location of fingerprints for matching')
	args = parser.parse_args()
	main(args)
