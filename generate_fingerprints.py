import argparse
import csv
import os
import tempfile

from scipy.io.wavfile import read as read_wav

import dsptools
import plottools
import utils
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

def checkForCSV(songName, archiveDir):
	#tmp = os.path.basename(songFile)
	#songName, ext = os.path.splitext(tmp)
	csvName = songName + '.csv'
	for (dirpath, dirnames, filenames) in os.walk(archiveDir):
		if csvName in filenames:
			return True
	return False

def main(args):
	fingerprintMethod = 'STFT'
	makePlots = False
	songLibraryInfo = listSongs(args.library)

	dbtools.createDatabase(args.archive)

	for (songFile, songName) in songLibraryInfo:
		print('Processing {}'.format(songFile))

		# check for song in DB
		if dbtools.getSongID(args.archive, songName):
			continue



		fs, rawData = read_wav(songFile)
		monoData = dsptools.convertToMono(rawData)

		timeSeries = dsptools.dataToTimeSeries(fs, monoData)

		# TODO: make this variable depending on fs
		decimationRate = 4
		(timeSeries, fs) = dsptools.decimateTimeSeries(timeSeries, fs, decimationRate)

		minFreq = 27.5 # A in sub-contra (https://en.wikipedia.org/wiki/Piano_key_frequencies)
		maxFreq = 4186.009 # C8
		(noteFrequencies, noteNames) = dsptools.defineNoteFrequencies(minFreq, maxFreq, 'A')


		if fingerprintMethod == 'CWT':
			if makePlots:
				(cwtT, cwtF, cwtM, noiseEstimateCwtM, noiseRemovedCwtM, peakMapCwtM) = dsptools.cwtAnalysis(timeSeries, fs, noteFrequencies)
				plottools.plotCwt(cwtT, cwtF, cwtM, noteNames, figName='CWT For {}'.format(songName), dest=os.path.join(args.images, songName + 'CWT.png'))
				plottools.plotCwt(cwtT, cwtF, noiseEstimateCwtM, noteNames, figName='CWT Noise Estimate For {}'.format(songName), dest=os.path.join(args.images, songName + 'NoiseEst.png'))
				plottools.plotCwt(cwtT, cwtF, noiseRemovedCwtM, noteNames, figName='Denoised CWT For {}'.format(songName), dest=os.path.join(args.images, songName + 'Denoised.png'))
				plottools.plotCwt(cwtT, cwtF, peakMapCwtM, noteNames, figName='CWT Peak Map For {}'.format(songName), dest=os.path.join(args.images, songName + 'Peaks.png'))
				plottools.plotNoiseEstimator(cwtF, cwtM, noiseEstimateCwtM, noiseRemovedCwtM)
			
			#fullSongPeakLocations = utils.orderPeaks(cwtT, cwtF, peakMapCwtM)
			#fullSongTable = utils.generateAddresses(fullSongPeakLocations)
			#utils.writeToCsv(fullSongTable, songName, args.archive)

		elif fingerprintMethod == 'STFT':
			(stftT, stftF, stftM, noiseEstimateStftM, noiseRemovedStftM, peakMapStftM) = dsptools.stftAnalysis(timeSeries, fs, noteFrequencies)
			if makePlots:
				plottools.plotStft(stftT, stftF, stftM,
								   block=False,
								   logScale=True,
								   noteFrequencies=noteFrequencies,
								   noteNames=noteNames,
								   figName='STFT For {}'.format(songName),
								   dest=os.path.join(args.images, songName + 'STFT.png'))
				plottools.plotStft(stftT, stftF, noiseEstimateStftM,
								   block=False,
								   logScale=True,
								   noteFrequencies=noteFrequencies,
								   noteNames=noteNames,
								   figName='Noise Estimate For {}'.format(songName),
								   dest=os.path.join(args.images, songName + 'NoiseEst.png'))

				plottools.plotStft(stftT, stftF, noiseRemovedStftM,
								   block=False,
								   logScale=True,
								   noteFrequencies=noteFrequencies,
								   noteNames=noteNames,
								   figName='Denoised STFT For {}'.format(songName),
								   dest=os.path.join(args.images, songName + 'Denoised.png'))

				plottools.plotStft(stftT, stftF, peakMapStftM,
								   block=False,
								   logScale=True,
								   noteFrequencies=noteFrequencies,
								   noteNames=noteNames,
								   figName='Peak Map For {}'.format(songName),
								   dest=os.path.join(args.images, songName + 'Peaks.png'))

				# [1:200,229] is a specific timeslice of "When I'm Sixty-Four" w/ bass and clarinets
				plottools.plotNoiseEstimator(stftF, stftM[:,50], noiseEstimateStftM[:,50], noiseRemovedStftM[:,50],
											 block=False,
											 dest=os.path.join(args.images, songName + 'NoiseEstimatorExample.png'))

			sortedPeaks = dsptools.orderPeaks(stftT, stftF, peakMapStftM)
			#fullSongTable = utils.generateAddresses(fullSongPeakLocations, targetGroupSize=targetGroupSize, anchorLag=20)
			#utils.addFingerprintsToDB(args.archive, fullSongTable, songName)
			dbtools.addSongToDB(args.archive, songName)
			dbtools.addPeaksToDB(args.archive, sortedPeaks, songName)
			timeOffset = 5
			timeWindow = 2
			frequencyWindow = 10
			dbtools.generateFingerprints(args.archive, songName, timeOffset, timeWindow, frequencyWindow)

	dtype = [('dTime', int), ('dFrequency', int)]
	testConstellation = [(6, 7), (7, -10), (7, 8)]
	dbtools.searchForConstellation(args.archive, testConstellation)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to match against')
	parser.add_argument('archive', help='Location to store fingerprints from library')
	parser.add_argument('images', help='Location to store images for presentation')
	args = parser.parse_args()
	main(args)