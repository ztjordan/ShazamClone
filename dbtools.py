import sqlite3

def createDatabase(dbName):
	con = sqlite3.connect(dbName)

	cur = con.cursor()

	cur.execute("CREATE TABLE IF NOT EXISTS songs (songID integer PRIMARY KEY, songName text)")
	cur.execute("CREATE TABLE IF NOT EXISTS points (pointID integer PRIMARY KEY, time integer, frequency integer, amplitude integer, songID REFERENCES songs(songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellations (constellationID integer PRIMARY KEY, songID REFERENCES songs(songID))")
	cur.execute("CREATE TABLE IF NOT EXISTS constellationGroups (relationshipID integer PRIMARY KEY, constellationID REFERENCES constellations(constellationID), dTime integer, dFrequency integer)")
	cur.execute("CREATE TABLE IF NOT EXISTS constellationAnchors (anchorID integer PRIMARY KEY, constellationID REFERENCES constellations(constellationID), anchorTime REFERENCES points(pointID), anchorFrequency REFERENCES points(pointFrequency)")

	con.commit()

	con.close()

def addSongToDB(dbName, songName):
	con = sqlite3.connect(dbName)
	cur = con.cursor()

	cur.execute('INSERT INTO songs(songName) VALUES (?)', (songName,))
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