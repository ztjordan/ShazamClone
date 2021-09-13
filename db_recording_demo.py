import argparse
import csv
import os
import random
import tempfile

from scipy.io.wavfile import read as read_wav
import dsptools
import plottools
import utils

import numpy as np
import matplotlib.pyplot as plt

import pdb


def main(args):
	songFile = args.testfile
	tmp = os.path.basename(songFile)
	(songName, fileExtension) = os.path.splitext(songFile)
	fs, rawData = read_wav(songFile)
	monoData = dsptools.convertToMono(rawData)
	timeSeries = dsptools.dataToTimeSeries(fs, monoData)

	decimationRate = 4
	(timeSeries, fs) = dsptools.decimateTimeSeries(timeSeries, fs, decimationRate)

	minFreq = 27.5 # A in sub-contra (https://en.wikipedia.org/wiki/Piano_key_frequencies)
	maxFreq = 4186.009 # C8
	(noteFrequencies, noteNames) = dsptools.defineNoteFrequencies(minFreq, maxFreq, 'A')

	method = 'STFT'
	if method == 'CWT':
		(testCwtT, testCwtF, testCwtM, testNoiseEstimateCwtM, testNoiseRemovedCwtM, testPeakMapCwtM) = dsptools.cwtAnalysis(timeSeries, fs, noteFrequencies)
		testPeakLocations = utils.orderPeaks(testCwtT, testCwtF, testPeakMapCwtM)
		testTable = utils.generateAddresses(testPeakLocations)
		plottools.plotCwt(testCwtT, noteFrequencies, testCwtM, noteNames)
	elif method == 'STFT':
		(testStftT, testStftF, testStftM, testNoiseEstimateStftM, testNoiseRemovedStftM, testPeakMapStftM) = dsptools.stftAnalysis(timeSeries, fs, noteFrequencies)
		testPeakLocations = utils.orderPeaks(testStftT, testStftF, testPeakMapStftM)
		testTable = utils.generateAddresses(testPeakLocations)
		#plottools.plotStft(testStftT, testStftF, testStftM, noteFrequencies, noteNames, figName='STFT For {}'.format(songName), dest=os.path.join('C:\\Users\\Zed\\Projects\\ShazamClone\\', songName + 'STFT.png'))
		#plottools.plotStft(testStftT, testStftF, testNoiseEstimateStftM, noteFrequencies, noteNames, figName='Noise Estimate For {}'.format(songName), dest=os.path.join('C:\\Users\\Zed\\Projects\\ShazamClone\\', songName + 'NoiseEst.png'))
		#plottools.plotStft(testStftT, testStftF, testNoiseRemovedStftM, noteFrequencies, noteNames, figName='Denoised STFT For {}'.format(songName), dest=os.path.join('C:\\Users\\Zed\\Projects\\ShazamClone\\', songName + 'Denoised.png'))
		#plottools.plotStft(testStftT, testStftF, testPeakMapStftM, noteFrequencies, noteNames, figName='Peak Map for {}'.format(songName), dest=os.path.join('C:\\Users\\Zed\\Projects\\ShazamClone\\', songName + 'Peaks.png'))
		#plottools.plotStft(testStftT, testStftF, testPeakMapStftM, noteFrequencies, noteNames)

	numAnchorsPerGroup = 1
	targetGroupSize = 5

	bestMatchScore = 0.0
	bestMatchSong = ''

	songScores = []

	numAnchors = 1
	entriesPerPoint = 3

	for fingerprintKey in testTable:
		utils.matchKeys(args.archive, fingerprintKey, targetGroupSize, numAnchorsPerGroup)




	for fingerPrintCSV in os.listdir(args.archive):
		dbName, ext = os.path.splitext(fingerPrintCSV)
		databaseTable = {}
		with open(os.path.join(args.archive, fingerPrintCSV), newline='') as csvFile:
			csvReader = csv.DictReader(csvFile)
			for row in csvReader:
				entry = []
				numPoints = int((len(row) - numAnchors) / entriesPerPoint) # it is very strange that this must be cast to int				
				for ptNum in range(numPoints):
					entry.append(  (int(row['anchorFreq_' + str(ptNum)]), int(row['pointFreq_' + str(ptNum)]), int(row['deltaTime_' + str(ptNum)]))  )
				databaseTable[tuple(entry)] = int(row['anchorTime'])

		positive = 0
		negative = 0
		matchingAnchors = []
		matchingPoints = []

		numKeys = len(testTable.keys())

		print('Checkpoint')
		for testKey in testTable.keys():
			match = False
			for dbKey in databaseTable.keys():
				if utils.matchKeys(dbKey, testKey):
					match = True
					positive += 1
						
					matchAnchorTime = databaseTable[dbKey]
					matchAnchorFreq = testKey[0][0]
					matchingAnchors.append((matchAnchorTime, matchAnchorFreq))

					for i in testKey:
						pointFreq = matchAnchorFreq + i[1]
						pointTime = matchAnchorTime + i[2]
						matchingPoints.append((pointTime, pointFreq))
					
			if not match:
				negative += 1


		accuracy = positive / (positive + negative) * 100
		songScores.append((dbName, accuracy))

		print('{} to {} match: {}%'.format(dbName, songName, accuracy))

		if (accuracy > bestMatchScore):
			bestMatchDB = databaseTable
			bestMatchPlot = (matchingAnchors, matchingPoints)
			bestMatchScore = accuracy
			bestMatchSong = dbName

	print('Best match: {} ({}%)'.format(bestMatchSong, bestMatchScore))
	anchors = bestMatchPlot[0]
	anchorTimes = []
	anchorFreqs = []
	for (aT, aF) in anchors:
		anchorTimes.append(aT)
		anchorFreqs.append(aF)

	points = bestMatchPlot[1]
	pointTimes = []
	pointFreqs = []
	for (pT, pF) in points:
		pointTimes.append(pT)
		pointFreqs.append(pF)

	dbAnchorTimes = []
	dbAnchorFreqs = []
	dbPointTimes = []
	dbPointFreqs = []
	for pointGroup in bestMatchDB:
		(aF, pF, dT) = pointGroup[0]
		for point in pointGroup:
			(aF, pF, dT) = point
			aT = bestMatchDB[pointGroup]
			pT = aT + dT
			dbPointTimes.append(pT)
			dbPointFreqs.append(pF)

		dbAnchorTimes.append(aT)
		dbAnchorFreqs.append(aF)

	#plt.scatter(anchorTimes, anchorFreqs, color='red')
	#plt.scatter(pointTimes, pointFreqs, color='blue')
	#plt.show(block=False)

	plt.scatter(dbAnchorTimes, dbAnchorFreqs, color='red')
	plt.scatter(dbPointTimes, dbPointFreqs, color='blue')
	plt.show(block=False)
	breakpoint()



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('testfile', help='A WAV file containing a short recording to Shazam')
	parser.add_argument('archive', help='Fingerprint Database')
	args = parser.parse_args()
	main(args)
