import pyodbc
import sys
from datetime import datetime

# MSSQL connection
UID = ''
PWD = ''
DSN = ''
connect_string = 'DSN=' + DSN + ';UID=' + UID + ';PWD=' + PWD + ''


def check_logs():

	try:
		dbconn = pyodbc.connect(connect_string)
		sql = 'SELECT * FROM [Data].[dbo].[LogSourceAge]'
		cursor = dbconn.execute(sql)
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()

		return results

	except Exception, e:
		print e
		sys.exit(2)

if __name__ == '__main__':

	#if len(sys.argv) != 4:
	#   print 'Please execute the script in the following format: '
	#   print 'python check_sp.py <storedProcName> <warning value> <critical value>'
	#   sys.exit(2)

	#table = sys.argv[1]
	#warn = sys.argv[2]
	#crit = sys.argv[3]

	tsr = check_logs()
	# print tsr

	now = datetime.now()
	utc = datetime.utcnow()
	#print now
	#print utc
	#print ""
	
	warns = []
	crits = []
	
	for log in tsr:
		#print log[1]
		if log[5] == 'UTC':
			delta = utc - log[2]
			#print 'Now = ' + str(utc)
		elif log[5] == None:
			delta = now - log[2]
			#print 'Now = ' + str(now)
		else:
			print 'ERROR - Timezone not recognised'
			delta = ''
		delta_str = str(delta)
		
		#print 'Log = ' + str(log[2])
		#print 'Delta = ' + str(delta)
		mins_delta = int(delta.total_seconds() / 60)
		threshold = int(log[4])
		#print 'Minutes Delta = ' + str(mins_delta)
		#print 'Threshold = ' + str(log[4])
		#print ""

		if mins_delta > threshold:
			crits.append(log[1])
			
	if crits:
		crit_string = ', '.join(map(str, crits))
		print "CRITICAL - following log sources exceed time threshold: %s " % (crit_string)
		sys.exit(2)
	else:
		print "OK - No log sources exceed time since import threshold."
		sys.exit(0)

