#!/usr/bin/python

## Checks the time since last log in a log file
## Format has to be standard python datetime.now() format

import subprocess
import sys
from datetime import datetime

try:
	warning = sys.argv[1]
	critical = sys.argv[2]
	filepath = sys.argv[3]
	
	
except:
	print 'ERROR - Execute as follows:'
	print 'python check_log_time.py <warning (hours)> <critical (hours)> <path to logfile>'
	sys.exit(2)

line = subprocess.check_output(['tail', '-n1', filepath])
ls = line.strip()

# check that log file isn't empty
if ls == '':
	print "WARNING - log file %s is empty" % (filepath)
	sys.exit(1)

time_dirty = ls.split(' ')
date = time_dirty[0]
time = time_dirty[1]

dt = date + ' ' + time

logtime = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S,%f')
# logtime = datetime.strptime('2016-06-06 14:42:14,515', '%Y-%m-%d %H:%M:%S,%f')
now = datetime.now()

delta = now - logtime
delta_str = str(delta)

if ('days' in delta_str) or ('day' in delta_str):
	days, seconds = delta.days, delta.seconds
	hours = days * 24 + seconds // 3600
	minutes = (seconds % 3600) // 60
	seconds = seconds % 60
	print "CRITICAL - %s days, %s hours, %s mins, %s seconds since log file was last written to!" % (delta.days, hours, minutes, seconds)
	sys.exit(2)
else:
	f = delta_str.split(':')
	hours = int(f[0])
	mins = int(f[1])
	secs = int(f[2].split('.')[0])

	if hours >= critical:
		print "CRITICAL - %s hours, %s mins, %s seconds since log file was last written to." % (hours, mins, secs)
		sys.exit(2)
	elif hours >= warning:
		print "WARNING - %s hours, %s mins, %s seconds since log file was last written to." % (hours, mins, secs)
		sys.exit(1)
	else:
		print "OK - %s hours, %s mins, %s seconds since log file was last written to." % (hours, mins, secs)
		sys.exit(0)

