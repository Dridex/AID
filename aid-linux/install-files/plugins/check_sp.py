import pyodbc
import sys

# MSSQL connection
UID = ''
PWD = ''
DSN = ''
connect_string = 'DSN=' + DSN + ';UID=' + UID + ';PWD=' + PWD + ''


def call_sp(table):

	try:
		dbconn = pyodbc.connect(connect_string)
		sql = 'exec [Data].[dbo].[%s]' % table
		cursor = dbconn.execute(sql)
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()

		timeSinceRecord = results[0][0]

		return timeSinceRecord

	except Exception, e:
		print e
		sys.exit(2)

if __name__ == '__main__':

	if len(sys.argv) != 4:
		print 'Please execute the script in the following format: '
		print 'python check_sp.py <storedProcName> <warning value> <critical value>'
		sys.exit(2)

	table = sys.argv[1]
	warn = sys.argv[2]
	crit = sys.argv[3]

	tsr = call_sp(table)

	i_tsr = int(tsr)
	i_warn = int(warn)
	i_crit = int(crit)

	if i_tsr < i_warn:
		print "OK - %s minutes since last record." % tsr
		sys.exit(0)
	elif i_tsr >= i_warn and i_tsr < i_crit:
		print "WARNING - %s minutes since last record." % tsr
		sys.exit(1)
	elif i_tsr >= i_crit:
		print "CRITICAL - %s minutes since last record." % tsr
		sys.exit(2)

