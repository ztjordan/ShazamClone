import sqlite3

def createDatabase(dbName):
	con = sqlite3.connect(dbName)

	cur = con.cursor()

	# Some notes:
	# Need some way to enforce uniqueness in constellations
	#	- Partial solution: add songID to constellationAnchors, UNIQUE(anchorTime, anchorFrequency, songID)
	#	- However, constellations is a joining table for constellationGroups and constellationAnchors
	'''
	cur.execute("CREATE TABLE IF NOT EXISTS songs (songID integer PRIMARY KEY, songName text, UNIQUE(songName))")
	cur.execute("CREATE TABLE IF NOT EXISTS points (pointID integer PRIMARY KEY, pTime integer, frequency integer, amplitude real, songID REFERENCES songs(songID), UNIQUE(pTime, frequency, songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellations (constellationID integer PRIMARY KEY, songID REFERENCES songs(songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellationGroups (relationshipID integer PRIMARY KEY, constellationID REFERENCES constellations(constellationID), dTime integer, dFrequency integer)")
	cur.execute("CREATE TABLE IF NOT EXISTS constellationAnchors (anchorID integer PRIMARY KEY, constellationID REFERENCES constellations(constellationID), anchorTime REFERENCES points(pointID), anchorFrequency REFERENCES points(frequency))")
	'''

	# Temporary fix: only one anchor per constellation eliminates circular dependency between constellations and constellationAnchors
	cur.execute("CREATE TABLE IF NOT EXISTS songs (songID integer PRIMARY KEY, songName text, UNIQUE(songName))")
	cur.execute("CREATE TABLE IF NOT EXISTS points (pointID integer PRIMARY KEY, pTime integer, frequency integer, amplitude real, songID REFERENCES songs(songID), UNIQUE(pTime, frequency, songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellations (constellationID integer PRIMARY KEY, anchorID REFERENCES points(pointID), numPoints integer, songID REFERENCES songs(songID), UNIQUE(anchorID, songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellationGroups (relationshipID integer PRIMARY KEY, constellationID REFERENCES constellations(constellationID), anchorID REFERENCES points(pointID), dTime integer, dFrequency integer, UNIQUE(constellationID, anchorID, dTime, dFrequency))")
	con.commit()

	con.close()

def addSongToDB(dbName, songName):
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute('INSERT OR IGNORE INTO songs(songName) VALUES (?)', (songName,))
	con.commit()
	con.close()

def getSongID(dbName, songName):
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute("SELECT (songID) FROM songs WHERE songName=(?)", (songName,))

	result = cur.fetchone()
	con.close()

	if result:
		return result[0]
	else:
		return None

def getConstellationID(dbName, songName, anchorID):
	songID = getSongID(dbName, songName)
	if not songID:
		print('Song not in database... what do?')
		raise ValueError

	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute("SELECT (constellationID) FROM constellations WHERE songID=(?) AND anchorID=(?)", (songID,anchorID))

	result = cur.fetchone()
	con.close()

	if result:
		return result[0]
	else:
		return None

def generateFingerprints(dbName, songName, timeOffset, timeWindow, frequencyWindow):
	# Require timeOffset > timeWindow

	songID = getSongID(dbName, songName)
	if not songID:
		print('Song not in database... what do?')
		raise ValueError

	con = sqlite3.connect(dbName)
	cur = con.cursor()

	# I suspect only pTime and frequency will be useful here, saving old query for reference
	#cur.execute("SELECT pointID, pTime, frequency, amplitude, songID FROM points WHERE songID=(?) ORDER BY amplitude DESC", (songID,))
	cur.execute("SELECT pTime, frequency, amplitude, pointID FROM points WHERE songID=(?) ORDER BY amplitude DESC", (songID,))
	songPoints = cur.fetchall()
	for (aTime, aFreq, anchorID) in songPoints:
		# need to find all points in songID where pTime is between pTime +/- constellationTimeOffset and frequency is between frequency +/- constellationFrequencyWindow
		cur.execute("SELECT pTime, frequency FROM points WHERE songID=(?) AND pTime BETWEEN (?) and (?) AND frequency BETWEEN (?) and (?)", (songID, aTime+(timeOffset-timeWindow), aTime+(timeOffset+timeWindow), aFreq-frequencyWindow, aFreq+frequencyWindow))
		constellationPoints = cur.fetchall()
		numPoints = len(constellationPoints)
		# TODO/IDEA: set some minimum number of points to justify creating a constellation
		if len(constellationPoints) > 0:
			cur.execute("INSERT OR IGNORE INTO constellations(anchorID, numPoints, songID) VALUES (?, ?)", (anchorID, numPoints, songID))


			# Is there a way to get the constellation ID as a result of the INSERT? I would prefer that to this
			#constellationID = getConstellationID(dbName, songName, anchorID)
			constellationID = cur.lastrowid
			if not constellationID:
				print('Constellation not in database... what do?')
				raise ValueError

			for (pTime, pFreq) in constellationPoints:
				dTime = pTime - aTime
				dFreq = pFreq - aFreq
				cur.execute("INSERT OR IGNORE INTO constellationGroups(constellationID, anchorID, dTime, dFrequency) VALUES (?, ?, ?)", (constellationID, anchorID, dTime, dFreq))

	con.commit()
	con.close()

def addPeaksToDB(dbName, peaks, songName):
	songID = getSongID(dbName, songName)
	if not songID:
		print('Song not in database... what do?')
		raise ValueError

	con = sqlite3.connect(dbName)
	cur = con.cursor()

	# assume "peaks" is a list of (time, frequency, amplitude) tuples
	# TODO: use executemany - make sure values are of the right types
	'''
	# This almost works, but insertionList is a list of ((time, freq, amp), songID)
	insertionList = [x for x in zip(peaks, [songID] * len(peaks))]
	cur.executemany("INSERT OR IGNORE INTO points(pTime, frequency, amplitude, songID) VALUES (?, ?, ?, ?)", insertionList)
	'''
	insertionList = []
	for p in peaks:
		insertionList.append(int(p[0]), int(p[1]), float(p[2]), songID)

	cur.execute("INSERT OR IGNORE INTO points(pTime, frequency, amplitude, songID) VALUES (?, ?, ?, ?)", insertionList)

	con.commit()
	con.close()
	
def searchForConstellation(dbName, constellationPoints):
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	# create a temporary table and store all of the matches for each point
	cur.execute("CREATE TEMPORARY TABLE search (constellationID integer, anchorID integer, dTime integer, dFrequency integer, songID integer, UNIQUE(constellationID, anchorID, dTime, dFrequency, songID))") # no foreign keys in tempdb

	nPoints = len(constellationPoints)
	for  (dTime, dFreq) in constellationPoints:
		# join this into the temporary table
		cur.execute("INSERT OR IGNORE INTO temp.search SELECT constellations.constellationID, constellations.anchorID, constellationGroups.dTime, constellationGroups.dFrequency, constellations.songID FROM constellations INNER JOIN constellationGroups ON constellations.constellationID = constellationGroups.constellationID WHERE constellationGroups.dTime BETWEEN (?) and (?) AND constellationGroups.dFrequency BETWEEN (?) and (?)", (dTime-1, dTime+1, dFreq-1, dFreq+1))

	# at this point, temp.search will contain A LOT of entries that consist of every databse constellation that contains any point that matches any point in the constellation we are searching for
	# SELECT constellationID, COUNT(constellationID) FROM temp.search GROUP BY constellationID ORDER BY COUNT(constellationID) DESC; # get a list of constellation IDs and the count of points they have that match
	cur.execute("SELECT constellationID, songID FROM temp.search HAVING COUNT(constellationID)=(?)", (nPoints)) # need to use leq (less than or equal to) here - assumming snippets have more points than database

	cur.execute("DROP TABLE temp.search")

	con.close()

def songMatch(dbName, constellations):
	#constellations = [((anchorTime, anchorFreq), [(dTime, dFreq), (dTime, dFreq), (dTime, dFreq)]), ((aT, aF), [(dT, dF), (dT, dF), (dT, dF))]
	breakpoint()
	# we will have a list of constellations from the snippet
	# find the first peak and build the constellation hash around it
	# find the next peak outside of the constellation window and build the constellation hash around it
	# compute the time and frequency differences between the two peaks, and only keep songs with constellation matches that are those distances apart
	# those songs are matches - use a temporary table to keep a count of the matches
	return


	
	



