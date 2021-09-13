import argparse
import os

from scipy.io.wavfile import read as read_wav

import dsptools

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

	for (songFile, songName) in songLibraryInfo:
		(filename, fileExtension) = os.path.splitext(songFile)
		if fileExtension != '.wav':
			outFilename = os.path.join(args.library, songName + '.wav')
			dsptools.convertToWav(songFile, outFilename)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Shazam!')
	parser.add_argument('library', help='A directory containing the music files to match against')
	args = parser.parse_args()
	main(args)