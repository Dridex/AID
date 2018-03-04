#!/usr/bin/python

import logging
import logging.config
import base64
import binascii
import StringIO

from Crypto.Cipher import AES
from Crypto import Random

logging.config.fileConfig('/opt/scripts/aid-controller/etc/logging.conf')
logger = logging.getLogger('helperController.py')

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

