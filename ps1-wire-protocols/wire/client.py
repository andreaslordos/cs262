import socket, threading
import sys

IP_ADDR = '0.0.0.0'
PORT = 7976
VERSION_NUMBER = '1'

# to change colors of terminal text
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

commands = {'PROMPT': '1', # Prompt for login/create account
            'LOGIN': '2', # Request for logging in
            'REGISTER': '3', # Request for creating new account
            'LOGIN_PROMPT': '4', # Request for entering login credentials
            'CREATE_PROMPT': '5', # Request for entering new account credentials
            'DISPLAY': '6', # Display message
            'HELP': '7', # Display help
            'LIST_USERS': '8', #Display list of users
            'CONNECT': '9', # Connect to a user
            'TEXT': 'a', # Send text to a user
            'NOTHING': 'b', # 
            'DELETE': 'c',
            'EXIT_CHAT': 'd',
            'SHOW_TEXT': 'e',
            'START_CHAT': 'f',
            'REQUEST': 'g'}

class ChatClient:
    def __init__(self, ip, port) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))


    def login(self):
        self.username = input("Choose a username: ")
        return VERSION_NUMBER + commands['LOGIN'] + self.username


    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message[1] == commands['PROMPT']:
                    self.client.send(self.login().encode('utf-8'))
                else:
                    print(message)
            except:
                print("An error occurred!")
                self.client.close()
                break


    def write(self):
        while True:
            message = f"{self.username}: {input('')}"
            self.client.send(message.encode('utf-8'))


client = ChatClient(IP_ADDR, PORT)
receive_thread = threading.Thread(target=client.receive)
receive_thread.start()