#!/usr/bin/python

import sys
try:
        import requests
except ImportError:
        print "CRITICAL - Can't import requests python module, exiting"
        sys.exit(2)



try:
        website = sys.argv[1]
        textToCheck = sys.argv[2]
	for i in sys.argv[3:]:
		textToCheck = textToCheck + ' ' + i
	textToCheck = textToCheck.strip()
except:
        print 'ERROR - Please give a 2 args to check'
        sys.exit(2)

r = requests.get(website, verify=False)


if r.status_code <> 200:
        print "CRITICAL - %s site returned a %s" % (website, r.status_code)
        sys.exit(2)

if textToCheck in r.content:
        print "OK - %s in the website %s" % (textToCheck, website)
        sys.exit(0)
else:
        print "CRITICAL - %s not in website %s" % (textToCheck, website)
        sys.exit(2)


