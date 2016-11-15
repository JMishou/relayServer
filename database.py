from sqlalchemy import *
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.types import TypeDecorator, Unicode
from sqlalchemy.orm import scoped_session
import binascii
import logging
import getpass
import hashlib
import os
import sys
import time
from encryption import *
import simplejson as json


Base = declarative_base()


 
########################################################################
class User(Base):
    """"""
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    password = Column(CHAR(64))
    salt = Column(CHAR(64))
    group = Column(String(10))  # Groups: admin: all access, tech: technician controls, user: user controls
    locked = Column(BOOLEAN)
    resetpwd = Column(BOOLEAN)
    email = Column(String(100))
 
    #----------------------------------------------------------------------
    def __init__(self, username, password, salt, group, email = ""):
        """"""
        self.username = username
        self.password = password
	self.salt = salt
	self.group = group
	self.locked = 0
	self.resetpwd = 0
	self.email = email

class userDatabase():	

	def __init__(self, connection_string=None, connection_file=None, encryption_key_file=None):
		self.connectionString = "";
		if connection_string != None:
			self.connectionString = connection_string
		elif connection_file != None and encryption_key_file == None:
			self.connectionString = open(connection_file).read()
		elif connection_file != None and encryption_key_file != None:
			enc = encryption(None, encryption_key_file)
			self.connectionString = enc.decrypt(connection_file)
		else:
			sys.exit("No database connection supplied") 

		self.engine = create_engine(self.connectionString)
		self.Session = sessionmaker(bind=self.engine)
		self.session = scoped_session(self.Session)
		self.engine.connect()
	
	def queryUser(self, userName):
		query = self.session.query(User).filter(User.username == userName)
	    	return query.first()

	def getUser(self, userName):
		q = self.queryUser(userName)
		if q == None:
			return None
		else:
			return q.__dict__

	def getUsers(self):
		uList = []
		for user in self.session.query(User).all():
			uList.append(user.__dict__)
		return uList

	def addUser(self, userName,password,salt,group):
		q = self.queryUser(userName)
		if q == None:
			user = User(userName,password,salt,group)
			self.session.add(user)
			self.session.commit()
			print '\nUser has been saved\n'
			return True
		else:
			print '\nUsername already in database\n'
			return False



	def unlockUser(self, userName):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.locked = 0
			self.session.commit()
			print userName + ": unlocked."

	def lockUser(self, userName):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.locked = 1
			self.session.commit()
			print userName + ": locked."

	def deleteUser(self, userName):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			self.session.delete(q)
			self.session.commit()
			print userName + ": deleted."

	def resetPassword(self, userName):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.resetpwd = 1
			self.session.commit()
			print userName + ": password to be reset on login."

	def changePassword(self, userName, Password, salt):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.password = Password
			q.salt = salt
			q.resetpwd = 0
			self.session.commit()
			print userName + ": password to be reset on login."

	def editEmail(self, userName, email):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.email = email
			self.session.commit()
			print userName + "email address:" + email

	def editGroup(self, userName, group):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			q.group = group
			self.session.commit()
			print userName + "group changed:" + group

	def authenticateUser(self, userName, password):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			return q.password == password

	def authenticateUserHash(self, userName, password):
		q = self.queryUser(userName)
		if q == None:
			print userName + ": not a valid user name."
		else:
			hashed = hashlib.sha256(password + q.salt).hexdigest()
			return hashed == q.password

	def cliAuthenticate(self,userName=None,group=None):
		
		pass_try = 0 
		pass_attempts = 3
		if userName == None:
			userName = raw_input('Please Enter User Name: ')

		result = self.queryUser(userName)

		if not result:
			print 'Unkown User Name.'
			return False
		if result.locked:
			print userName + ' has been locked.  Please contact an administator.'
			return False

		while pass_try < pass_attempts:
			slt = result.salt
			user_input = hashlib.sha256(getpass.getpass('Please Enter Password: ')+ slt).hexdigest()
			if user_input != result.password:
				pass_try += 1
				print 'Incorrect Password, ' + str(pass_attempts-pass_try) + ' more attemts left\n'
			else:
				pass_try = pass_attempts+1
		
		if pass_try == pass_attempts:

			print 'Too many failed attempts, user has been locked.  Please contact an administator.'
			self.lockUser(userName)
			return False

		if group != None:
			if group != result.group:
				return False

		if result.resetpwd:
			self.cliChangePassword(userName, 1)
			
		return True

	def cliAuthenticateUser(self, userName):

		pass_try = 0 
		pass_attempts = 3


		result = self.queryUser(userName)

		if not result:
			print 'Unkown User Name.'
			return False

		while pass_try < pass_attempts:
			slt = result.salt
			user_input = hashlib.sha256(getpass.getpass('Please Enter Password: ')+ slt).hexdigest()
			if user_input != result.password:
				pass_try += 1
				print 'Incorrect Password, ' + str(pass_attempts-pass_try) + ' more attemts left\n'
			else:
				pass_try = pass_attempts+1
		
		if pass_try == pass_attempts:

			print 'Too many failed attempts, user has been locked.  Please contact an administator.'
			self.lockUser(userName)
			return False

		if group != None:
			if group != result.group:
				return False

		if result.resetpwd:
			cliChangePassword(userName,1)

		return True

	def cliAddUser(self, userName = ""):
		if userName == "":
			userName = raw_input('Please Enter a User Name: ')
		password = 0;
		password2 = 1;
		salt = binascii.hexlify(os.urandom(32))
		while password != password2:
			password = hashlib.sha256(getpass.getpass('Please Enter a Password: ') + salt).hexdigest()
			password2 = hashlib.sha256(getpass.getpass('Please re-enter the Password: ') + salt).hexdigest()
			if password != password2:
				print "Passwords do not match please try again!"
		group = raw_input('Please Enter the User Group: ')
	

		try:
			if self.addUser(userName,password,salt,group):
				print userName + ": successfully added."

		except Exception as e:
			print e


		time.sleep(1)

	def cliChangePassword(self, userName, overrideCurrent = 0):
		q = self.queryUser(userName)
		password = 0;
		password2 = 1;
		if overrideCurrent == 0:
			if not cliAuthenticateUser(userName):
				print "Cannot authenticate " + userName
				time.sleep(1)
				return
		
		salt = binascii.hexlify(os.urandom(32))
		while password != password2:
			password = hashlib.sha256(getpass.getpass('Please Enter a new Password: ') + salt).hexdigest()
			password2 = hashlib.sha256(getpass.getpass('Please re-enter the Password: ') + salt).hexdigest()
			if password != password2:
				print "Passwords do not match please try again!"


		q.salt = salt
		q.password = password
		q.resetpwd = 0
		self.session.commit()
		print "Password successfully changed."
		time.sleep(1)

		
	def userList(self):
		uList = []
		for user in self.session.query(User).with_entities(User.username).all():
			uList.append(str(user[0]))
		return uList

	def emailList(self):
		uList = []
		for user in self.session.query(User).with_entities(User.email).all():
			email = str(user[0])
			if email != "":
				uList.append(email)
		return uList

	def commit(self):
		self.session.commit()


 

if __name__ == "__main__":
	# create database tables
	user = raw_input('Please enter DB User Name: ')
	pwd = getpass.getpass('Please enter DB Password: ')
	initial_db_url = 'mysql+pymysql://{}:{}@localhost'
	engine = create_engine(initial_db_url.format(user,pwd))
	engine.execute("CREATE DATABASE IF NOT EXISTS relay;") #create db
	engine.execute("USE relay") # select new db
	Base.metadata.create_all(engine)
	pwd = 0
	pwd1 = 1
	while pwd != pwd1:
		pwd = getpass.getpass('Enter the password for DB User relay: ')
		pwd1 = getpass.getpass('Please confirm the password for DB User relay: ')
		if pwd != pwd1:
			print "Passwords do not match.  Please try again."
	pwd = getpass.getpass('Enter the password for DB User relay: ')
	engine.execute("GRANT USAGE ON *.* TO 'relay'@'localhost';")
	engine.execute("DROP USER 'relay'@'localhost';")
	engine.execute("CREATE USER 'relay'@'localhost' IDENTIFIED BY '{}';".format(pwd))
	engine.execute("GRANT ALL PRIVILEGES ON relay.users TO 'relay'@'localhost';")
	engine.execute("FLUSH PRIVILEGES;")
	dbconnect = 'mysql+pymysql://relay:{}@localhost/relay'.format(pwd)
	user = 0
	user1 = 1
	while user != user1:
		user = raw_input('Please enter gmail address for sending alerts: ')
		user1 = raw_input('Please confirm the gmail address: ')
		if user != user1:
			print "Usernames do not match.  Please try again."
	pwd = 0
	pwd1 = 1
	while pwd != pwd1:
		pwd = getpass.getpass('Enter the password for gmail account: ')
		pwd1 = getpass.getpass('Please confirm the password for gmail account: ')
		if pwd != pwd1:
			print "Passwords do not match.  Please try again."
	d = {'dbconnect': dbconnect,
	     'gmailUser': user,
	     'gmailPass': pwd }
	enc = encryption()
	enc.writeKey("rsa_key.bin")
	enc.encrypt("connections.bin", json.dumps(d))
	udb = userDatabase(dbconnect)
	print "Database successfully initialized."
	print "Private key: rsa_key.bin"
	print "Encrypted connections: connections.bin"
	print ""
	print ""
	print "Adding DB user 'admin'.  Be sure to enter admin for group"
	udb.cliAddUser("admin")

	




