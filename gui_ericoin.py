import os
import requests

from tkinter import *


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()
	
	# Balances function
    def check_balances(self):
        response = requests.get('http://132.196.148.36:' + '5010' + '/balances')
        accounts = list(response.json().keys())
        account_balances = list(response.json().values())
        print("Account Balances:")
        for i in range(len(accounts)):
            if len(str(accounts[i])) >= 13:
                to_be_printed = "\t"+str(accounts[i][:5])+"..."+str(accounts[i][-5:])+": "+str(account_balances[i])
            else:
                to_be_printed = "\t"+str(accounts[i])+": "+str(account_balances[i])
            print(to_be_printed)
        print("\n")
	
	# Mining function
    def start_mining(self):
        os.system("python setup_2_miners_1_bookkeeper.py")
        os.system("python register_nodes.py")
	
	# Transaction function
    def make_transaction(self):
        os.system("python sign_and_send_transaction.py")
		
	# Widget manipulation
    def createWidgets(self):
		# Account Balances
        self.balances = Button(self)
        self.balances["text"] = "Account Balances"
        self.balances["fg"]   = "navy"
        self.balances["command"] = self.check_balances
        self.balances.pack({"side": "left"})
		# Start Mining
        self.mining = Button(self)
        self.mining["text"] = "Start Mining"
        self.mining["fg"]   = "navy"
        self.mining["command"] = self.start_mining
        self.mining.pack({"side": "left"})
        # Make Transaction
        self.transact = Button(self)
        self.transact["text"] = "Make Transaction"
        self.transact["fg"]   = "navy"
        self.transact["command"] = self.make_transaction
        self.transact.pack({"side": "left"})
		# Quit GUI
        self.quit_button = Button(self)
        self.quit_button["text"] = "Exit"
        self.quit_button["fg"]   = "firebrick"
        self.quit_button["command"] =  self.quit
        self.quit_button.pack({"side": "right"})


root = Tk()
app = Application(master=root)
app.mainloop()
root.destroy()	
