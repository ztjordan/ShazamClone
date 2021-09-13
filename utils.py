import csv
import os
import sqlite3
import itertools

import numpy as np

def writeToCsv(songTable, songName, fingerPrintArchive):
	firstEntry = list(songTable.items())[0]
	k = firstEntry[0]

	archiveFilename = os.path.join(fingerPrintArchive, songName + '.csv')
	targetGroupSize = len(k)
	csvFields = []
	for ptNum in range(targetGroupSize):
		csvFields.append('anchorFreq_' + str(ptNum))
		csvFields.append('pointFreq_' + str(ptNum))
		csvFields.append('deltaTime_' + str(ptNum))
	csvFields.append('anchorTime')

	with open(archiveFilename, 'w', newline='') as csvFile:
		csvWriter = csv.DictWriter(csvFile, fieldnames=csvFields)
		csvWriter.writeheader()

		for groupMetaData in songTable:
			# groupMetaData is an N-tuple (based on target zone size) of 3-tuples (anchorFreq, pointFreq, dTime point to anchor)
			# each N-tuple is a key in a key-value pair with the anchor's time
			csvEntry = {'anchorTime':songTable[groupMetaData]}
			for ptIndex in range(len(groupMetaData)):
				(anchorFreq, pointFreq, deltaT) = groupMetaData[ptIndex]
				csvEntry['anchorFreq_' + str(ptIndex)] = anchorFreq
				csvEntry['pointFreq_' + str(ptIndex)] = pointFreq
				csvEntry['deltaTime_' + str(ptIndex)] = deltaT

			csvWriter.writerow(csvEntry)

def orderPeaks(t, f, peaks):
	peakLocations = []
	flat = peaks.flatten('F') # Fortran style flattening, because column-major
	for ind in range(0,len(flat)):
		if flat[ind]:
			peakLocations.append(np.unravel_index(ind, peaks.shape, order='F'))
	return peakLocations

'''
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
'''


def generateAddresses(peakLocations, numAnchorsPerGroup=1, targetGroupSize=5, anchorLag=20):
	addressTable = []
	for anchorInd in range(0, len(peakLocations)-targetGroupSize-anchorLag): # iterate over all anchorPeaks
		groupInfo = {}
		for anchorNum in range(numAnchorsPerGroup):
			(fAnchor, tAnchor) = peakLocations[anchorInd + anchorNum]
			groupInfo['AF' + str(anchorNum)] = fAnchor
			groupInfo['AT' + str(anchorNum)] = tAnchor

		
		for pointNum in range(targetGroupSize):
			(fPoint, tPoint) = peakLocations[anchorInd + anchorLag + pointNum]
			groupInfo['PF' + str(pointNum)] = fPoint
			for anchorNum in range(numAnchorsPerGroup):
				(fAnchor, tAnchor) = peakLocations[anchorInd + anchorNum]
				groupInfo['DT_' + str(anchorNum) + str(pointNum)] = tPoint - tAnchor

		addressTable.append(groupInfo)
	return addressTable

'''
def matchKeys(dbKey, testKey, matchThreshold=3):
	pointMatches = 0

	for dbKeyPoint in dbKey:
		for testKeyPoint in testKey:
			if matchPoints(dbKeyPoint, testKeyPoint):
				pointMatches += 1
				continue

	if pointMatches >= matchThreshold:
		return True
	else:
		return False

def matchPoints(dbPoint, testPoint, anchorFreqTolerance=1, pointFreqTolerance=1, deltaTTolerance=1):
	(dbAnchorFreq, dbPointFreq, dbDeltaT) = dbPoint
	(testAnchorFreq, testPointFreq, testDeltaT) = testPoint

	anchorFreqGood = False
	pointFreqGood = False
	deltaTGood = False

	if (testAnchorFreq >= dbAnchorFreq - anchorFreqTolerance) and (testAnchorFreq <= dbAnchorFreq + anchorFreqTolerance):
		anchorFreqGood = True
	
	if (testPointFreq >= dbPointFreq - pointFreqTolerance) and (testPointFreq <= dbPointFreq + pointFreqTolerance):
		pointFreqGood = True
	
	if (testDeltaT >= dbDeltaT - deltaTTolerance) and (testDeltaT <= dbDeltaT + deltaTTolerance):
		deltaTGood = True

	if anchorFreqGood and pointFreqGood and deltaTGood:
		return True
	else:
		return False
'''

def matchKeys(dbName, testKey, numPointsPerGroup, numAnchorsPerGroup):
	anchorFreqTolerance = 1
	deltaTimeTolerance = 1
	pointFreqTolerance = 1
	minimumMatches = 3

	con = sqlite3.connect(dbName)
	cur = con.cursor()

	groupKeys = []
	for pointNum in range(numPointsPerGroup):
		pointKeys = []
		pointKeys.append('PF' + str(pointNum))
		
		for anchorNum in range(numAnchorsPerGroup):
			pointKeys.append('DT_' + str(anchorNum) + str(pointNum))

		groupKeys.append(tuple(pointKeys))

	anchorKeys = []
	for anchorNum in range(numAnchorsPerGroup):
		anchorKeys.append('AF' + str(anchorNum))

	queryParams = []
	queryStrings = []
	for anchorKey in anchorKeys:
		anchorFreq = testKey[anchorKey]
		queryStrings.append('SELECT (FingerprintID) FROM fingerprints WHERE {} BETWEEN (?) and (?)'.format(anchorKey))
		queryParams.append( int(anchorFreq-anchorFreqTolerance) )
		queryParams.append( int(anchorFreq+anchorFreqTolerance) )


	qString = 'INTERSECT'.join(queryStrings)
	
	cur.execute(qString, tuple(queryParams))
	anchorFrequencyMatchIDs = cur.fetchall()

	keyCombos = [x for x in itertools.combinations(groupKeys, minimumMatches)]

	for keyCombo in keyCombos:
		(p1, p2, p3) = keyCombo # pick these keys from testKey
		# build a query sort of like this
		# SELECT (FingerprintID, SongID) FROM fingerprints WHERE ....
		# FingerprintID = anchorFrequencyMatchID
		# PF0 BETWEEN testKey[p1[0]] + pointFreqTolerance and testKey[p1[0]] + pointFreqTolerance AND 
		# OR PF1 BETWEEN testKey[p1[0]] + pointFreqTolerance and testKey[p1[0]] + pointFreqTolerance



def createDatabase(dbName, numPointsPerGroup, numAnchorsPerGroup):
	con = sqlite3.connect(dbName)

	cur = con.cursor()

	cur.execute("CREATE TABLE songs (SongID integer PRIMARY KEY, SongName text)")

	columnNames = ['FingerprintID integer PRIMARY KEY']
	for i in range(numAnchorsPerGroup):
		columnNames.append('AF' + str(i) + ' integer')
		columnNames.append('AT' + str(i) + ' integer')

	for i in range(numPointsPerGroup):
		columnNames.append('PF' + str(i) + ' integer')
		for j in range(numAnchorsPerGroup):
			columnNames.append('DT_' + str(j) + str(i) + ' integer')
	columnNames.append('SongID integer REFERENCES songs(SongID)')

	# Create finger print table
	cur.execute("CREATE TABLE fingerprints ({})".format(','.join(columnNames)))

	# Save (commit) the changes
	con.commit()

	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost.
	con.close()

def addSongToDB(dbName, songName):
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute('INSERT INTO songs(SongName) VALUES (?)', (songName,))
	con.commit()
	con.close()

def addFingerprintsToDB(dbName, fingerprints, songName):
	# fingerprints will be a list of dictionaries
	# Get the song ID from the song table
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute("SELECT (SongID) FROM songs WHERE SongName=(?)", (songName,))
	(songID,) = cur.fetchone()

	for fingerprint in fingerprints:
		rowNames = ['SongID']
		values = [songID]
		qMarkStr = ','.join(['?'] * (len(fingerprint.keys()) + 1))
		for k in fingerprint:
			rowNames.append(k)
			values.append(int(fingerprint[k]))

		cur.execute("INSERT INTO fingerprints({}) VALUES ({})".format(','.join(rowNames), qMarkStr), tuple(values))

	con.commit()
	con.close()
