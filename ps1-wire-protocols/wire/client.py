import socket, threading
import sys
from colors import *
from time import sleep

IP_ADDR = '0.0.0.0'
PORT = 7978
VERSION_NUMBER = '8'


'''
WIRE PROTOCOL
================
    1. Version Number (1 byte)
    2. Command (1 byte)
    3. Data (variable length)
'''

commands = {'LOGIN_PROMPT': '1', # Prompt for login/create account
            'LOGIN': '2', # Request for logging in
            'REGISTER': '3', # Request for creating new account
            'DISPLAY': '4', # Display message to client terminal
            'HELP': '5', # Display help
            'LIST_USERS': '6', # Display list of users
            'CONNECT': '7', # Request to connect to a user
            'TEXT': '8', # Send text to a user
            'NOTHING': '9', # When client sends empty message
            'DELETE': 'a', # Request for deleting account
            'EXIT_CHAT': 'b', # Request for exiting chat
            'PROMPT': 'c', # Prompt client for response
            'START_CHAT': 'd', # Response to client's request to start chat
            'QUIT': 'e', # Request for quitting application
            'ERROR': 'f', # Error message
}

class ChatClient:
    def __init__(self, ip, port) -> None:
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))


    def parse_input(self, cli_input: str) -> str:
        '''
        Parses input from user
        Converts cli input to appropriate request format to send to server
        Format of returned string: <VERSION_NUMBER><COMMAND><DATA>
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


    def display_message(self, message: str) -> None:
        '''
        Displays message to client terminal
        '''

        if not message: raise Exception('Error in display_message: invalid message')
        elif len(message) > 2: print(message[2:])
    

    def login_prompt(self) -> str:
        '''
        Prompts user for login/create account
        '''
        choice = input('Login or create account? (L/C): ')

        while choice.upper() not in ['L', 'C']:
            choice = input('Invalid choice. Please try again (L/C): ')

        if choice == 'L':
            username = input("Welcome back. Enter your username: ")
            return VERSION_NUMBER + commands['LOGIN'] + username
        
        else:
            username = input("Enter your new username: ")
            return VERSION_NUMBER + commands['REGISTER'] + username
    

    def prompt(self) -> str:
        '''
        Prompts user for input
        '''
        return input(strBlue("--> "))


    def handle_text(self, text: str) -> str:
        '''
        Handles text input from user
        '''
        if text.upper() == '/E':
            return VERSION_NUMBER + commands['EXIT_CHAT'] + ''
        return VERSION_NUMBER + commands['TEXT'] + text


    def receive(self) -> None:
        '''
        Receives messages from server
        '''
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                #sleep(0.1)
                # Before client is logged in:
                if message[1] == commands['LOGIN_PROMPT']:
                    res = self.login_prompt()
                    self.client.send(res.encode('utf-8'))

                # After client is logged in:
                elif message[1] == commands['DISPLAY']:
                    self.display_message(message)
                
                elif message[1] == commands['PROMPT']:
                    user_input = self.prompt()
                    res = self.parse_input(user_input)
                    self.client.send(res.encode('utf-8'))

                elif message[1] == commands['QUIT']:
                    self.client.close()
                    return
                
                elif message[1] == commands['START_CHAT']:
                    pass
                
                elif message[1] == commands['ERROR']:
                    pass

            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                self.client.close()
                sys.exit()

            except Exception as e:
                print(strFail(repr(e)))
                self.client.close()
                break


    def write(self) -> None:
        while True:
            text = input()
            req = self.handle_text(text)
            client.send(req.encode('utf-8'))
            if req[1] == commands['EXIT_CHAT']:
                return


if __name__ == '__main__':
    client = ChatClient(IP_ADDR, PORT)
    receive_thread = threading.Thread(target=client.receive)
    receive_thread.start()