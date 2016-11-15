from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP


class encryption:

	def __init__(self, key=None, keyFile=None):
		if key != None:
			self.key = RSA.import_key(key)
		elif keyFile != None:
			f = open(keyFile)
			self.key = RSA.import_key(f.read())
			f.close()
		else:
			self.key = RSA.generate(2048)

	def writeKey(self, filename, password=None):
		file_out = open(str(filename), "wb")
		export_key = None
		if password!=None:
			export_key = self.key.exportKey(passphrase=password, pkcs=8, protection="scryptAndAES128-CBC")
		else:
			export_key = self.key.exportKey()

		
		file_out = open(str(filename), "wb")
		file_out.write(export_key)
		file_out.close()


	def readKey(self, filename, password=None):
		f = open(str(filename), "rb")
		import_key = f.read()
		if passphrase != None:
			self.key = RSA.import_key(encoded_key, passphrase=password)
		else:
			self.key = RSA.import_key(import_key)
		f.close()

	def encrypt(self, filename, data):
		file_out = open(str(filename), "wb")

		session_key = get_random_bytes(16)

		# Encrypt the session key with the public RSA key
		
		cipher_rsa = PKCS1_OAEP.new(self.key)
		file_out.write(cipher_rsa.encrypt(session_key))

		# Encrypt the data with the AES session key
		cipher_aes = AES.new(session_key, AES.MODE_EAX)
		ciphertext, tag = cipher_aes.encrypt_and_digest(data)
		[ file_out.write(x) for x in (cipher_aes.nonce, tag, ciphertext) ]
		file_out.close()

	def decrypt(self, filename):
		file_in = open(str(filename), "rb")
		#private = self.key.exportKey()
		enc_session_key, nonce, tag, ciphertext = \
		   [ file_in.read(x) for x in (self.key.size_in_bytes(), 16, 16, -1) ]

		file_in.close()
		# Decrypt the session key with the public RSA key
		cipher_rsa = PKCS1_OAEP.new(self.key)
		session_key = cipher_rsa.decrypt(enc_session_key)

		# Decrypt the data with the AES session key
		cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
		data = cipher_aes.decrypt_and_verify(ciphertext, tag)
		
		return data
		
