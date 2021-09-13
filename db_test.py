import sqlite3


if __name__ == "__main__":
	numPointsPerGroup = 3
	numAnchorsPerGroup = 1

	con = sqlite3.connect('example.db')

	cur = con.cursor()

	columnNames = []
	for i in range(numAnchorsPerGroup):
		columnNames.append('AF' + str(i))
		columnNames.append('AT' + str(i))

	for i in range(numPointsPerGroup):
		columnNames.append('PF' + str(i))
		for j in range(numAnchorsPerGroup):
			columnNames.append('DT_' + str(j) + str(i))

	# Create table
	cur.execute("CREATE TABLE test ({})".format(','.join(columnNames)))

	# Insert a row of data
	cur.execute("INSERT INTO test VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10))

	# Save (commit) the changes
	con.commit()

	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost.
	con.close()
