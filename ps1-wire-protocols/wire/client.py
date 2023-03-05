import socket, threading
from colors import *

IP_ADDR = '0.0.0.0'
PORT = 7976
VERSION_NUMBER = '1'

'''
WIRE PROTOCOL
================
    1. Version Number (1 byte)
    2. Command (1 byte)
    3. Data (variable length)
'''

commands = {'PROMPT': '1', # Prompt for login/create account
            'LOGIN': '2', # Request for logging in
            'REGISTER': '3', # Request for creating new account
            'LOGIN_PROMPT': '4', # Request for entering login credentials
            'CREATE_PROMPT': '5', # Request for entering new account credentials
            'DISPLAY': '6', # Display message to client terminal
            'HELP': '7', # Display help
            'LIST_USERS': '8', #Display list of users
            'CONNECT': '9', # Request to connect to a user
            'TEXT': 'a', # Send text to a user
            'NOTHING': 'b', # When client sends empty message
            'DELETE': 'c', # Request for deleting account
            'EXIT_CHAT': 'd', # Request for exiting chat
            'SHOW_TEXT': 'e', # Display text to client terminal -- prolly not needed, could use display instead
            'START_CHAT': 'f', # Response to client's request to start chat
            'QUIT': 'g', # Request for quitting application
}

class ChatClient:
    def __init__(self, ip, port) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))


    '''
    Parses input from user
    Converts cli input to appropriate request format to send to server
    Format of returned string: <VERSION_NUMBER><COMMAND><DATA>
    '''
    def parse_input(self, cli_input: str) -> str:
        '''
        Parses input from user
        Returns the appropriate request
        '''
        if not cli_input:
            return VERSION_NUMBER + commands['NOTHING'] + ''

        cli_input = ''.join(cli_input.split()) # Remove all whitespace from cli_input
        command = 'TEXT'
        data = ''
        if cli_input[0] == '/':
            if cli_input[1].upper() == 'H':
                command = 'HELP'
            elif cli_input[1].upper() == 'L':
                command = 'LIST_USERS'
            elif cli_input[1].upper() == 'C':
                command = 'CONNECT'
                if len(cli_input) > 2: data = cli_input[2:] # If user enters /C <username> send username to server
            elif cli_input[1].upper() == 'D':
                command = 'DELETE'
            elif cli_input[1].upper() == 'Q':
                command = 'QUIT'

        return VERSION_NUMBER + commands[command] + data


    '''
    Handles login and registration
    Prompts user to login or register
    Returns the appropriate request
    '''
    def login_register(self) -> str:
        # print("Welcome to the chat app! Please choose an option:")
        # print("1. Login (L)")
        # print("2. Register (R)")
        choice = ''

        while choice not in ['L', 'R']:
            choice = input("Enter your choice: ").upper()
        
        if choice == 'L':
            username = input("Welcome back. Enter your username: ")
            return VERSION_NUMBER + commands['LOGIN'] + username
        
        else:
            username = input("Enter your new username: ")
            return VERSION_NUMBER + commands['REGISTER'] + username
        

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message[1] == commands['PROMPT']:
                    if message[2:]: print(message[2:]) # print error message, if any
                    req = self.login_register().encode('utf-8')
                    self.client.send(req)

                elif message[1] == commands['DISPLAY']:
                    if message[2:]: print(message[2:])
                    response = input(f"{strBlue('-->')} ")
                    req = self.parse_input(response).encode('utf-8')
                    client.send(req)
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