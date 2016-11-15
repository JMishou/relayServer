#!/usr/bin/env python2                                                       

import curses                                                                
from curses import panel    
import simplejson as json
import signal
import sys
import glob
import traceback

from database import *
from encryption import *
from sendGmail import *

enc = encryption(None, "rsa_key.bin")
connections = json.loads(enc.decrypt("connections.bin"))
userdb = userDatabase(connections['dbconnect'])
currentUser = {}
gmail = sendGmail(connections['gmailUser'],connections['gmailPass'])

class Menu(object): 

    def signal_handler(self, signal, frame):
	raise self.exit_menu
                                                         

    def __init__(self, name, items, stdscreen):
        self.window = stdscreen.subwin(0,0)
        self.window.keypad(1)
	self.name = name
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
	self.panel.set_userptr(self)
        panel.update_panels()

        self.position = 0
	self.name = name
        self.items = items                                                   
        self.items.append(('exit','exit'))      

	signal.signal(signal.SIGINT, self.signal_handler)

    class exit_menu(Exception): pass                             

    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1     

    def exit(self):
	raise self.exit_menu                           

    def display(self):                                                       
        self.panel.top()                                                     
        self.panel.show()                                                    
        self.window.clear()  
	(y, x) = self.window.getmaxyx()                                                
	cursorLoc = (0,0)

	try:
		while True:                                                          
		    self.window.refresh()                                            
		    curses.doupdate()      
		    self.window.addstr(0, 1, self.name, curses.A_UNDERLINE )                                           
		    for index, item in enumerate(self.items):                     
		        if index == self.position:                                   
		            mode = curses.A_REVERSE                                  
		        else:                                                        
		            mode = curses.A_NORMAL                                   

		        msg = '%d. %s' % (index+1, item[0])   


			if len(msg) > x/2:
				msg = msg[:x/2]
			if (index+2) >= y:
				cursorLoc = ((index-y)+4,x/2)
				self.window.addstr((index-y)+4, x/2, msg, mode)
			else:                      
				cursorLoc = (index+2,1)
		        	self.window.addstr(index+2, 1, msg, mode)                    

			self.window.move(cursorLoc[0]+4,cursorLoc[1]+10)
		    key = self.window.getch()                                        

		    if key in [curses.KEY_ENTER, ord('\n')]:                         
		        if self.position == len(self.items)-1:                       
		            break                                                    
		        else:                                                        
		            self.items[self.position][1]()                           

		    elif key == curses.KEY_UP:                                       
		        self.navigate(-1)                                            

		    elif key == curses.KEY_DOWN:                                     
		        self.navigate(1)                                             
	except self.exit_menu:
		pass
	except Exception as e:
		sys.exit(traceback.format_exc())

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()

class MyApp(object):

    def __init__(self, stdscreen):  

        self.screen = stdscreen
        curses.curs_set(0)

	global gmail
	self.gmail = gmail

	users = userdb.userList()
	adminMenu_items = [("Add User", self.addUser)]
	for usr in users:
		adminMenu_items.append((usr, self.userActionMenu))            
	self.adminMenu = Menu("Admin Menu", adminMenu_items, self.screen)   
                                                                   
	self.adminMenu.display()  




    def print_selection(self):
	top = panel.top_panel()
	top.window().clear()
	top.window().addstr(10,30, self.getSelectedItem(), curses.A_NORMAL) 

    def print_msg(self,message,y,x):
	top = panel.top_panel()
	top.window().clear()
	top.window().addstr(y,x, message, curses.A_NORMAL)  
	time.sleep(1)

    def getSelectedItem(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	return menu.items[menu.position][0]

    def gracefulExit(self, excetion):
	if exception != Menu.exitMenu:
		sys.exit(traceback.format_exc())
		

#User actions
    def updateAdminMenu(self):
        users = userdb.userList()
	adminMenu_items = [("Add User", self.addUser)]
	for usr in users:
		adminMenu_items.append((usr, self.userActionMenu))            

	adminMenu_items.append(('exit','exit'))
	self.adminMenu.items = adminMenu_items

    def userActionMenu(self):
	self.curUserName = self.getSelectedItem()
	action_items = [
		('Lock User',self.lockUser),
		('Unlock User',self.unlockUser),
		('Delete User',self.deleteUser),
		('Add Email',self.addEmail),
		('Reset Password - User will reset on next login',self.resetPassword),
		('Change Password - Password will be manually changed by admin',self.changePassword) 
		]
	action_menu = Menu(self.curUserName + " Actions", action_items, self.screen)  
	action_menu.display()  

    def lockUser(self):
	userdb.lockUser(self.curUserName)


    def unlockUser(self):
	userdb.unlockUser(self.curUserName)

    def addEmail(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	email = raw_input("Email address:")
	userdb.editEmail(self.curUserName, email)
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()
	self.print_msg(email + " added",10,10)
	


    def deleteUser(self):
	userdb.deleteUser(self.curUserName)
	self.updateAdminMenu()
	pan = panel.top_panel()
	menu = pan.userptr()
	menu.exit()
	
    def resetPassword(self):
	userdb.resetPassword(self.curUserName)

    def changePassword(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	userdb.cliChangePassword(self.curUserName, 1)
	userdb.resetPassword(self.curUserName)
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()
	self.print_msg(self.curUserName + " Password Changed",10,10)

    def addUser(self):
	top = panel.top_panel()
	menu = top.userptr()
	menu.window.clear()
	menu.window.refresh()
	curses.reset_shell_mode()
	userdb.cliAddUser()
	self.updateAdminMenu()
	curses.reset_prog_mode()
	menu.window.clear()
	menu.window.refresh()



def authenticate():
	userName = raw_input('Please Enter User Name: ')
	authenticated = userdb.cliAuthenticate(userName)
	if authenticated:
		print "Login Success."
		global currentUser 
		currentUser = userdb.getUser(userName)
		sendEmail(userName + " has logged in.", "A user has successfully logged in.")
	else:
		user = userdb.getUser(userName)
		if user == None or user['locked']:
			if user == None:
				sendEmail("Unknown User: " + userName, "An unknown user has attempted to log into the system")
			else:
				sendEmail("User Locked: " + userName, "User is locked out of the system.")
		print "Login Failed"

	return authenticated       

def sendEmail(subject,body):
	recipients = userdb.emailList()
	gmail.subject = subject
	gmail.body = body
	gmail.addRecipients(recipients)
	gmail.send()                                

if __name__ == '__main__':    
        if authenticate():
		curses.wrapper(MyApp)
	else:
		sys.exit("Unauthorized user")                   
  
