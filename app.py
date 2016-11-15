from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import hashlib
import ssl
from sqlalchemy.orm import sessionmaker
from database import *
import RPi.GPIO as GPIO 	#import the gpio library
import time			#import the time library
import atexit

relay_1_pin = 4	
relay_2_pin = 17	
relay_3_pin = 23	
relay_4_pin = 24

GPIO.setmode(GPIO.BCM)
	
GPIO.setup(relay_1_pin, GPIO.OUT)
GPIO.setup(relay_2_pin, GPIO.OUT)
GPIO.setup(relay_3_pin, GPIO.OUT)
GPIO.setup(relay_4_pin, GPIO.OUT)

GPIO.output(relay_1_pin, GPIO.HIGH)
GPIO.output(relay_2_pin, GPIO.HIGH)
GPIO.output(relay_3_pin, GPIO.HIGH)
GPIO.output(relay_4_pin, GPIO.HIGH)


enc = encryption(None, "rsa_key.bin")
connections = json.loads(enc.decrypt("connections.bin"))
userdb = userDatabase(connections['dbconnect'])
 
app = Flask(__name__)

global pass_attempts
global pass_fails 
global userName_failing
global message

pass_attempts = 3
pass_fails = 0 
userName_failing = ""
message = ""

ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
ctx.load_cert_chain('ssl.cert', 'ssl.key')
 
@app.route('/')
def home():
    global message

    if not session.get('logged_in'):
        return render_template('login.html', msg=message)
    else:
	checked = [GPIO.input(relay_1_pin), GPIO.input(relay_2_pin), GPIO.input(relay_3_pin), GPIO.input(relay_4_pin)]
	for index in range(len(checked)):
		if checked[index]:
			checked[index] = ""
		else:
			checked[index] = " checked"
        return render_template('relay.html', checked=checked)

def locked():
        return "Account Locked.  Please contact your adminstrator"
 
@app.route('/login', methods=['POST'])
def do_admin_login():

    global pass_attempts
    global pass_fails
    global userName_failing
    global message
    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
 
    result = userdb.queryUser(POST_USERNAME)
    if not result:
	message = 'User name not found!'
	return home()
    else:
	if not result.locked:
		salt = result.salt
		pwd = result.password
		if hashlib.sha256(POST_PASSWORD + salt).hexdigest() == pwd:	
			pass_fails = 0
			message = ""
			session['logged_in'] = True
		else:
			if userName_failing != POST_USERNAME:
				pass_fails = 0
				userName_failing = POST_USERNAME
			pass_fails += 1
			remaining = pass_attempts - pass_fails
			message = "Login failed... {} attempts remaining".format(remaining)
	        if pass_fails == pass_attempts:
			pass_fails = 0
	        	userdb.lockUser(POST_USERNAME) 
			return locked()
	else:
		return locked()
    return home()
 
@app.route('/relay', methods=['POST'])
def do_relay():
	return home()

# When the submit button is pushed on the webpage
@app.route("/submit", methods=['POST'])
def handle_data(): #get the data
   relay1 = request.values.getlist('relay1')
   relay2 = request.values.getlist('relay2')
   relay3 = request.values.getlist('relay3')
   relay4 = request.values.getlist('relay4')

   print str(relay1) + " " + str(relay2) + " " + str(relay3) + " " + str(relay4)

   GPIO.output(relay_1_pin, not relay1)
   GPIO.output(relay_2_pin, not relay2)
   GPIO.output(relay_3_pin, not relay3)
   GPIO.output(relay_4_pin, not relay4)

   #reload the main page
   return home()

def cleanup():
	GPIO.cleanup()


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return home()

 
if __name__ == "__main__":
    atexit.register(cleanup)
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000, ssl_context=ctx)


