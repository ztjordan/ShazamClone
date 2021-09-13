import argparse
import csv
import os
import tempfile

from scipy.io.wavfile import read as read_wav
from scipy import signal

import numpy as np

import dsptools

import matplotlib.pyplot as plt

import pdb

import time

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
	songLibraryInfo = listSongs(args.library)

	songScores = []

	fs, testRawData = read_wav(args.testfile)
	testMonoData = dsptools.convertToMono(testRawData)
	testMonoData = testMonoData/ max(testMonoData)
	testTimeSeries = dsptools.dataToTimeSeries(fs, testMonoData)
	
	decimationRate = 4
	(testTimeSeries, fs) = dsptools.decimateTimeSeries(testTimeSeries, fs, decimationRate)

	maxScore = 0

	for (songFile, songName) in songLibraryInfo:
		#print('Processing {}'.format(songFile))

		fs, libRawData = read_wav(songFile)
		libMonoData = dsptools.convertToMono(libRawData)
		libMonoData = libMonoData / max(libMonoData)
		libTimeSeries = dsptools.dataToTimeSeries(fs, libMonoData)

		
		(libTimeSeries, fs) = dsptools.decimateTimeSeries(libTimeSeries, fs, decimationRate)


		libEnergy = np.sum(libTimeSeries[:1])
		corr = signal.correlate(libTimeSeries[:,1], testTimeSeries[:,1], mode='same')
		score = max(corr) / testTimeSeries.shape[0]
		songScores.append((songName, score))
		if score > maxScore:
			maxScore = score
			fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
			fig.suptitle('Time Series XCorr Results', fontsize=16)
			ax1.plot(testTimeSeries[:,0], testTimeSeries[:,1])
			ax1.set_title('Song Snippet + Interference')
			ax1.set_xlabel('Time (s)')
			ax1.set_ylabel('Amplitude')

			ax2.plot(libTimeSeries[:,0], libTimeSeries[:,1])
			ax2.set_title('Full Song')
			ax2.set_xlabel('Time (s)')
			ax2.set_ylabel('Amplitude')

			ax3.plot(libTimeSeries[:,0], corr)
			ax3.set_title('Cross-Correlation')
			ax3.set_xlabel('Time (s)')
			ax3.set_ylabel('Amplitude')
			plt.show(block=True)

	songScores.sort(key=lambda x: x[1])

	print('Best match: {}'.format(songScores[-1]))


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to match against')
	parser.add_argument('testfile', help='A WAV file containing a short recording to Shazam')
	args = parser.parse_args()
	tic = time.perf_counter()
	main(args)
	toc = time.perf_counter()
	print('Time to compute: {} seconds'.format(toc- tic))