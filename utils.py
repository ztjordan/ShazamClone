import csv
import os
import sqlite3
import itertools

import numpy as np

def orderPeaks(t, f, peaks):
	peakVals = []
	flat = peaks.flatten('F') # Fortran style flattening, because column-major
	dtype = [('time', int), ('frequency', int), ('amplitude', float)]
	for ind in range(0,len(flat)):
		if flat[ind]:
			(freq, time) = np.unravel_index(ind, peaks.shape, order='F')
			amp = peaks[freq][time]
			peakVals.append((time, freq, amp))

	tmp = np.array(peakVals, dtype=dtype)
	sortedPeaks = np.sort(tmp, order='amplitude') 
	return sortedPeaks
