import argparse
import csv
import os
import tempfile

from scipy.io.wavfile import read as read_wav

import dsptools
import plottools
import utils

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
	fingerprintMethod = 'CWT'
	makePlots = True
	songLibraryInfo = listSongs(args.library)


	numAnchorsPerGroup = 1
	targetGroupSize = 5
	#utils.createDatabase(args.archive, targetGroupSize, numAnchorsPerGroup)

	for (songFile, songName) in songLibraryInfo:

		#utils.addSongToDB(args.archive, songName)

		#if checkForCSV(songName, args.archive):
		#	continue

		print('Processing {}'.format(songFile))

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
			fullSongPeakLocations = utils.orderPeaks(cwtT, cwtF, peakMapCwtM)
			fullSongTable = utils.generateAddresses(fullSongPeakLocations)
			#utils.writeToCsv(fullSongTable, songName, args.archive)

		elif fingerprintMethod == 'STFT':
			(stftT, stftF, stftM, noiseEstimateStftM, noiseRemovedStftM, peakMapStftM) = dsptools.stftAnalysis(timeSeries, fs, noteFrequencies)
			if makePlots:
				plottools.plotStft(stftT, stftF, stftM, noteFrequencies, noteNames, figName='STFT For {}'.format(songName), dest=os.path.join(args.images, songName + 'STFT.png'))
				plottools.plotStft(stftT, stftF, noiseEstimateStftM, noteFrequencies, noteNames, figName='Noise Estimate For {}'.format(songName), dest=os.path.join(args.images, songName + 'NoiseEst.png'))
				plottools.plotStft(stftT, stftF, noiseRemovedStftM, noteFrequencies, noteNames, figName='Denoised STFT For {}'.format(songName), dest=os.path.join(args.images, songName + 'Denoised.png'))
				plottools.plotStft(stftT, stftF, peakMapStftM, noteFrequencies, noteNames, figName='Peak Map For {}'.format(songName), dest=os.path.join(args.images, songName + 'Peaks.png'))
				plottools.plotNoiseEstimator(stftF, stftM, noiseEstimateStftM, noiseRemovedStftM)

			fullSongPeakLocations = utils.orderPeaks(stftT, stftF, peakMapStftM)
			fullSongTable = utils.generateAddresses(fullSongPeakLocations, targetGroupSize=targetGroupSize, anchorLag=20)
			#utils.writeToCsv(fullSongTable, songName, args.archive)
			#utils.addFingerprintsToDB(args.archive, fullSongTable, songName)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to match against')
	parser.add_argument('archive', help='Location to store fingerprints from library')
	parser.add_argument('images', help='Location to store images for presentation')
	args = parser.parse_args()
	main(args)