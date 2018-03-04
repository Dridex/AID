#!/usr/bin/python
# Version 1.0
import os
import re
import sys
import logging
import logging.config
import pyodbc
import base64
import urllib
import binascii
import StringIO
import time

from Crypto.Cipher import AES
from Crypto import Random

os.chdir('/opt/scripts/aid-master/')
logging.config.fileConfig('/opt/scripts/aid-master/etc/logging.conf')
logger = logging.getLogger('helperMaster.py')

# MSSQL connection
DSN = ''
UID = ''
PWD = ''
connect_string = 'DSN=' + DSN + ';UID=' + UID + ';PWD=' + PWD + ''

# Saved print statement for debugging, because it takes forever to figure out all the necessary escapes
# print 'About to execute query: UPDATE [Data].[dbo].[AidService] SET [Status] = \'' + str(exitStat) + '\', [Output] = \'' + output + '\' WHERE Name = \'' + name + '\' and HostID = \'' + hostUID + '\''

# Query the database for info on a host
def queryHost(IP, parentUID):
	try:
		dbconn = pyodbc.connect(connect_string)
		sql = 'SELECT * FROM [Data].[dbo].[AidHost] WHERE [IP] = ? and [ZoneParent] = ?'
		cursor = dbconn.execute(sql, (IP, parentUID))
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()
		return results
	except Exception, e:
		logger.error("Error in queryHost:")
		logger.error(e)
		return None


def insertAidHost(hostname, status, IP, parentUID):

	sql = 'INSERT INTO [Data].[dbo].[AidHost] ([Name],[Status],[IP],[ZoneParent]) VALUES (?, ?, ?, ?)'

	try:
		dbconn = pyodbc.connect(connect_string)
		if not parentUID:
			cursor = dbconn.execute(sql, (hostname, status, IP, 'NULL'))
		else:
			cursor = dbconn.execute(sql, (hostname, status, IP, parentUID))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in insertAidHost:")
		logger.error(e)
		return 0


# Query the database for a particular service
def queryService(name, args, hostUID):

	try:
		dbconn = pyodbc.connect(connect_string)
		sql = 'SELECT * FROM [Data].[dbo].[AidService] WHERE [Script] = ? and [HostID] = ? and [Args] = ?'
		cursor = dbconn.execute(sql, (name, hostUID, args))
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()
		return results
	except Exception, e:
		logger.error("Error in queryService:")
		logger.error(e)
		return None


# Insert a new service into the database
def insertService(serviceName, args, status, hostUID, serviceOutput):

	now = time.strftime('%Y-%m-%d %H:%M:%S')
	sql = 'INSERT INTO [Data].[dbo].[AidService] ([Script],[Args],[Status],[HostID],[Output],[DateTime]) VALUES (?, ?, ?, ?, ?, ?)'
	logger.info('Inserting service: ' + serviceName)

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (serviceName, args, status, hostUID, serviceOutput, now))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in insertAidService:")
		logger.error(e)
		logger.error("Script = " + serviceName)
		logger.error("Args = " + args)
		logger.error("Status = " + str(status))
		logger.error("hostUID = " + hostUID)
		logger.error("serviceOutput = " + serviceOutput)
		return 0


# Update the status of a service
def updateService(name, args, hostUID, exitStat, output):

	now = time.strftime('%Y-%m-%d %H:%M:%S')
	sql = 'UPDATE [Data].[dbo].[AidService] SET [Status] = ?, [Output] = ?, [DateTime] = ? WHERE Script = ? and HostID = ? and Args = ?'
	logger.info('Updating service: ' + name)

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (exitStat, output, now, name, hostUID, args))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in updateService:")
		logger.error(e)
		return 0


# Update the status of a host
def updateHost(hostname, status, IP, controllerUID):

	sql = 'UPDATE [Data].[dbo].[AidHost] SET [Name] = ?, [Status] = ? WHERE IP = ? and ZoneParent = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (hostname, status, IP, controllerUID))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in updateHost:")
		logger.error(e)
		logger.error('hostname = ' + hostname)
		logger.error('status = ' + status)
		logger.error('IP = ' + IP)
		logger.error('controllerUID = ' + controllerUID)
		return 0


# Set all services belonging to a host to DOWN
def setServicesDown(hostUID):

	now = time.strftime('%Y-%m-%d %H:%M:%S')
	sql = 'UPDATE [Data].[dbo].[AidService] SET [Status] = ?, [Output] = ?, [DateTime] = ? WHERE HostID = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, ('2', 'No response from host', now, hostUID))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in setServicesDown:")
		logger.error(e)
		return 0


# Get ID of a controller, used for when one dies
def getContID(IP):
	
	sql = 'SELECT * FROM [Data].[dbo].[AidHost] WHERE IP = ? and ZoneParent = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (IP, 'NULL'))
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()
		return results
	except Exception, e:
		logger.error("Error in getContID:")
		logger.error(e)
		return None

# Get a list of host IDs belonging to a controller
def getHostIDs(contUID):
	
	sql = 'SELECT * FROM [Data].[dbo].[AidHost] WHERE ZoneParent = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (contUID))
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()
		return results
	except Exception, e:
		logger.error("Error in getHostIDs:")
		logger.error(e)
		return None


# Set all hosts belonging to a controller to DOWN
def setHostsDown(hostUID):

	sql = 'UPDATE [Data].[dbo].[AidHost] SET [Status] = ? WHERE ID = ? or ZoneParent = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, ('DOWN', hostUID, hostUID))
		rowcount = cursor.rowcount
		cursor.close()
		dbconn.commit()
		dbconn.close()
		return rowcount
	except Exception, e:
		logger.error("Error in setHostsDown:")
		logger.error(e)
		return 0


# Get host status in DB to compare new status from request
def getHostStatus(IP):
	
	sql = 'SELECT * FROM [Data].[dbo].[AidHost] WHERE IP = ?'

	try:
		dbconn = pyodbc.connect(connect_string)
		cursor = dbconn.execute(sql, (IP))
		results = cursor.fetchall()
		cursor.close()
		dbconn.close()
		return results
	except Exception, e:
		logger.error("Error in getHostStatus:")
		logger.error(e)
		return None


def pkcs7_decode(text, k):
	'''
	Remove the PKCS#7 padding from a text string
	'''
	nl = len(text)
	val = int(binascii.hexlify(text[-1]), 16)

	if val > k:
		raise ValueError('Input is not padded or padding is corrupt')

	l = nl - val
	return text[:l]


def pkcs7_encode(text, k):
	'''
	Pad an input string according to PKCS#7
	'''
	l = len(text)
	output = StringIO.StringIO()
	val = k - (l % k)

	for _ in xrange(val):
		output.write('%02x' % val)

	return text + binascii.unhexlify(output.getvalue())


def encrypt(text):
	key = 'iosje6rioj*#$(WOF"F"G:AD}{``efEF'

	# 16 byte initialization vector
	#iv = '1234567812345678'
	iv =  Random.get_random_bytes(16)
	aes = AES.new(key, AES.MODE_CBC, iv)

	# pad the plain text according to PKCS7
	pad_text = pkcs7_encode(text, 16)
	# encrypt the padding text
	cipher = aes.encrypt(pad_text)
	# base64 encode the cipher text for transport
	enc_cipher = base64.b64encode(iv + cipher)

	return enc_cipher


def decrypt(cipherString):
	key = 'iosje6rioj*#$(WOF"F"G:AD}{``efEF'

	# 16 byte initialization vector
	# iv = '1234567812345678'

	dec_cipher = base64.b64decode(cipherString)

	iv = dec_cipher[:16]
	cipher = dec_cipher[16:]

	aes = AES.new(key, AES.MODE_CBC, iv)

	text = aes.decrypt(cipher)
	upad_text = pkcs7_decode(text, 16)

	return upad_text

