#!/usr/bin/python

import sys
import re


def printHelp():
	print 'This script will check a log file for errors or warnings, and print output and exit code accordingly.'
	print 'Main purpose is as a Nagios / AID plugin.'
	print ''
	print 'USAGE: '
	print '\t $ python check_logs.py <logfile>'


if len(sys.argv) < 2:
	print 'ERROR - not enough arguements given.'
	printHelp()
	sys.exit(2)


logfile = sys.argv[1]
try:
	with open(logfile, 'r') as f:
		lines = f.read()
except:
	print 'ERROR - Could not open log file. Check the path / permissions.'
	sys.exit(2)

# find errors
errors = []
e_pattern = r"error"
for match in re.finditer(e_pattern, lines, flags=re.IGNORECASE):
	errors.append(match.group(0))

# find warnings
warnings = []
w_pattern = r"warning"
for match in re.finditer(w_pattern, lines, flags=re.IGNORECASE):
	warnings.append(match.group(0))


if len(errors) >= 1:
	print "CRITICAL - %s errors in log file: %s" % (len(errors),logfile)
	sys.exit(2)
elif len(warnings) >= 1:
	print "WARNING - %s warnings in log file: %s" % (len(warnings),logfile)
	sys.exit(1)
else:
	print "OK - No errors or warnings in log file \'%s\'" % (logfile)
	sys.exit(0)






