import socket, threading
import sys
from colors import * # this is a custom module that I wrote to make printing colored text easier


IP_ADDR = '0.0.0.0'
PORT = 7980
VERSION_NUMBER = '1'


'''
WIRE PROTOCOL
================
    1. Version Number (1 byte)
    2. Command (1 byte)
    3. Data (variable length)

REQUEST FORMAT: "<VERSION NUMBER><COMMAND CODE><DATA>"
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
                if len(cli_input) > 2: data = cli_input[2:] # If user enters /L <query> send search query to server
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

        if choice.upper() == 'L':
            username = input("Welcome back. Enter your username: ")
            return VERSION_NUMBER + commands['LOGIN'] + username
        
        elif choice.upper() == 'C':
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
        Returns formatted string to send to server
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
                
                ### Before client is logged in:

                if message[1] == commands['LOGIN_PROMPT']:
                    res = self.login_prompt()
                    self.client.send(res.encode('utf-8'))

                ### After client is logged in:

                # Displays from server
                elif message[1] == commands['DISPLAY']:
                    self.display_message(message)
                
                # Accepts user input and sends to server
                elif message[1] == commands['PROMPT']:
                    user_input = self.prompt()
                    res = self.parse_input(user_input)
                    self.client.send(res.encode('utf-8'))

                # Quits application
                elif message[1] == commands['QUIT']:
                    if message[2:]: print(message[2:])
                    self.client.close()
                    return
                
                # Starts chat thread
                elif message[1] == commands['START_CHAT']:
                    write_thread = threading.Thread(target=self.write)
                    write_thread.start()
                
                # Not used as of now
                elif message[1] == commands['ERROR']:
                    pass
            
            # Except statements to handle exceptions
            except KeyboardInterrupt:
                print('KeyboardInterrupt')
                self.client.close()
                sys.exit()

            except Exception as e:
                print(strFail(repr(e)))
                self.client.close()
                break


    def write(self) -> None:
        '''
        Write thread when client is connected to another user
        Ends when user enters '/E'
        '''
        while True:
            text = input()
            req = self.handle_text(text)
            self.client.send(req.encode('utf-8'))
            if req[1] == commands['EXIT_CHAT']:
                return


if __name__ == '__main__':
    client = ChatClient(IP_ADDR, PORT)
    try:
        receive_thread = threading.Thread(target=client.receive)
        receive_thread.start()

    except KeyboardInterrupt:
        print(strWarning('KeyboardInterrupt'))
        client.client.close()
        sys.exit()

    except Exception as e:
        print(strFail(repr(e)))
        client.client.close()
