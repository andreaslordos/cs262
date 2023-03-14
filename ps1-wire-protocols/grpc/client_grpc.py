from colors import *
import threading
import traceback
import sys

import grpc
import chat_pb2
import chat_pb2_grpc

host = '0.0.0.0'
port = 7976


commands = {'LOGIN': '1', # Request for logging in
            'REGISTER': '2', # Request for creating new account
            'LOGOUT': '3', # Request for logging out
            'HELP': '4', # Request for help
            'LIST_USERS': '5', # Request for list of users
            'CONNECT': '6', # Request to connect to a user
            'TEXT': '7', # Request to send text to a user
            'NOTHING': '8', # When client sends empty message
            'DELETE': '9', # Request for deleting account
            'EXIT_CHAT': 'a', # Request for exiting chat
            'QUIT': 'b', # Request for quitting application
}


class ChatClient:
    def __init__(self):
        self.__channel = grpc.insecure_channel(f'{host}:{port}')
        self.__stub = chat_pb2_grpc.ChatServiceStub(self.__channel)
        self.__listening_stream = None

        # Client state
        self.__user = None # : chat_pb2_grpc.User
        self.__is_logged_in = None # : bool used to determine which help message to display, and for handler function validation
        self.__is_connected = None # : bool used to determine prompt for user input, and for handler function validation
        self.__connected_to = None # : chat_pb2_grpc.User 


    def parse_input(self, cli_input: str) -> tuple:
        '''
        Parses input from user
        Converts cli input to appropriate request format to send to server
        Format of returned string: <COMMAND><DATA>
        '''
        if not cli_input:
            return commands['NOTHING'] + ''

        command = 'TEXT'
        data = ''

        cli_input = cli_input.split() # split input up by spaces
        
        if not self.is_logged_in:
            if len(cli_input[0]) == 1 and cli_input[0].upper() in ['L', 'R']:
                if cli_input[0].upper() == 'L':
                    command = 'LOGIN'
                    if len(cli_input) > 1: data = ' '.join(cli_input[1:])

                elif cli_input[0].upper() == 'R':
                    command = 'REGISTER'
                    if len(cli_input) > 1: data = ' '.join(cli_input[1:])

            elif len(cli_input[0]) == 2 and cli_input[0].upper() == '/Q':
                command = 'QUIT'

        elif cli_input[0][0] == '/':
            if len(cli_input[0]) == 2:
                cli_input = ''.join(cli_input) # Remove all whitespace from cli_input
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
                elif cli_input[1].upper() == 'E':
                    command = 'EXIT_CHAT'
                elif cli_input[1].upper() == 'X':
                    command = 'LOGOUT'
                elif cli_input[1].upper() == 'Q':
                    command = 'QUIT'
        
        else: data = ' '.join(cli_input)
        
        return commands[command], data.strip()

    # Getter methods for is_logged_in, user and is_connected
    @property
    def is_logged_in(self):
        return self.__is_logged_in

    @is_logged_in.setter
    def is_logged_in(self, value: bool):
        self.__is_logged_in = value

    @property
    def username(self): 
        if self.is_logged_in:
            return self.__user.name
        return None


    @property
    def is_connected(self):
        if self.is_logged_in:
            return self.__is_connected
        return None
    
    
    @is_connected.setter
    def is_connected(self, value: bool):
        self.__is_connected = value


    def handler(self, opcode, arg=''):
        '''
        Handles input from terminal,
        making appropriate requests to server
        '''
        try:
            if opcode == commands['LOGIN']:
                self.login(arg)
                self.help()

            elif opcode == commands['REGISTER']:
                self.register(arg)
                self.help()

            elif opcode == commands['HELP']:
                self.help()

            elif opcode == commands['QUIT']:
                self.quit()
            
            elif self.is_logged_in:
                if opcode == commands['LIST_USERS']:
                    self.get_users(arg)

                elif opcode == commands['DELETE']:
                    self.delete_account()
                    self.help()

                elif opcode == commands['CONNECT']:
                    self.connect(arg)

                elif opcode == commands['LOGOUT']:
                    self.logout(self.username)
                    self.help()

                elif self.is_connected:
                    if opcode == commands['TEXT']:
                        self.send_text(arg)

                    elif opcode == commands['EXIT_CHAT']:
                        self.disconnect()
                
                else:
                    self.display('Cannot perform that operation, user not connected to another user.', 'client')

            else:
                self.display('Cannot perform that operation, user not logged in.', 'client')
        
        except grpc.RpcError as RPC_ERR:
            self.display(strFail(f'Error {RPC_ERR.code()}: {RPC_ERR.details()}'), 'server')
            
            # Handle situation where user is connected to another user who deletes their account
            if RPC_ERR.details() == f'User {self.username} is not connected to anyone!' and self.is_connected:
                self.is_connected = False
                self.__connected_to = None


    def display(self, message: str, sender: str) -> str:
        '''
        Helper function to display text to terminal in a consistent format
        <sender> message
        '''
        if sender=='server': print(f'<{strBlue(sender)}> {message}')
        else: print(f"{strBlue(sender + ':')} {message}")


    def help(self) -> None:
        '''
        Displays help menu to user
        '''
        if self.is_logged_in:
            print('''
Choose from the following commands:
/H - Help
/L <query>- List users. If wildcard is specified, list matching users.
/C <username> - Connect to user
/D - Delete account
/X - Log out
/Q - Quit application
            ''')
        
        else:
            print('''
Welcome to the GRPC chat app! Please login or create an account to continue.
L <username> - Login
R <username> - Register
/Q - Quit application
            ''')

        
    def login(self, username: str) -> None:
        '''
        Logs user in
        Makes call to Login RPC
        Updates client state variables and starts listening thread
        '''
        user = chat_pb2.User(name=username)
        res = self.__stub.Login(user)

        self.is_logged_in = True
        self.__user = res
        self.display(strGreen('Welcome back!'), 'server')

        # Initialize listening stream and start receiving thread
        self.__listening_stream = self.__stub.ChatStream(self.__user)
        listening_thread = threading.Thread(target=self.receive_messsages, daemon=True)
        listening_thread.start()


    def logout(self, username: str) -> None:
        '''
        Logs user out
        Makes call to Logout RPC
        Updates client state variables and starts listening thread
        '''
        user = chat_pb2.User(name=username)
        self.__stub.Logout(user)

        self.is_logged_in = False
        self.__user = None

        self.display(strWarning('Logging out...'), 'server')


    def register(self, username: str) -> None:
        '''
        Registers user 
        Makes call to Register RPC
        Updates client state variables and starts listening thread
        '''
        user = chat_pb2.User(name=username)
        res = self.__stub.Register(user)
        
        self.is_logged_in = True
        self.__user = res
        self.display(strGreen('Account successfully created!'), 'server')

        # Initialize listening stream and start receiving thread
        self.__listening_stream = self.__stub.ChatStream(self.__user)
        listening_thread = threading.Thread(target=self.receive_messsages, daemon=True)
        listening_thread.start()
    

    def get_users(self, wildcard: str) -> None:
        '''
        Gets users
        Takes in wildcard string
        Makes call to GetUsers RPC, passing in SearchQuery object
        Prints out all users that match wildcard
        '''
        res = self.__stub.GetUsers(chat_pb2.SearchQuery(query=wildcard))
        message = ''
        for username in res.usernames:
            message += username + '\n'

        if message: self.display('These are all the users that have signed up:', 'server')
        else: self.display('No users registered.', 'server')

        print(message)


    def connect(self, other: str) -> None:
        '''
        Connects user to another user
        Makes call to Connect RPC
        Updates client state variables
        '''
        req_obj = chat_pb2.ChatMessage(message='', sender=self.username, to=other)
        connected_to = self.__stub.Connect(req_obj)
        self.is_connected = True
        self.__connected_to = connected_to

        self.display(strGreen(f'Connected to {other}! Text and enter to send messages. Send /E to exit chat.'), 'server')

    
    def disconnect(self) -> None:
        '''
        Disconnects user from another user
        Makes call to Disconnect RPC
        Updates client state variables
        '''
        req_obj = chat_pb2.User(name=self.username)
        other_user = self.__stub.Disconnect(req_obj)
        self.is_connected = False
        self.__connected_to = None

        self.display(strWarning(f'Disconnected from {other_user.name}!'), 'server')


    def send_text(self, message: str) -> None:
        '''
        Sends text to another user
        Makes call to SendMessage RPC
        Only successful if user is connected to another user (checked on server side)
        '''
        chat_msg = chat_pb2.ChatMessage(message=message, sender=self.username, to=self.__connected_to.name)
        self.__stub.SendMessage(chat_msg)


    def delete_account(self) -> None:
        '''
        Deletes user account
        Makes call to Delete RPC
        Updates client state variables
        '''
        user = chat_pb2.User(name=self.username)
        self.__stub.Delete(user)

        self.is_logged_in = False
        self.is_connected = False
        self.__user = None
        self.display(strWarning('Account deleted.'), 'server')


    def receive_messsages(self) -> None:
        '''
        Helper function to receive messages from server
        Runs in a separate thread started in login and register
        '''
        for chat_msg in self.__listening_stream:
            self.display(message=chat_msg.message, sender=chat_msg.sender)

    
    def quit(self) -> None:
        '''
        Quits client
        '''
        self.logout(self.username)
        self.__channel.close()
        sys.exit()


if __name__ == '__main__':
    client = ChatClient()
    client.help() # Display help menu
    try:
        while True:
            prompt = '> '
            if client.is_connected: prompt = '' # No prompt if connected to another user
            inp = input(prompt)
            try: op, data = client.parse_input(inp)
            except ValueError: continue # No input provided
            client.handler(op, data)

    except KeyboardInterrupt:
        print(strWarning('Keyboard interrupt detected. Client closing.'))
        if client.username: client.logout(client.username)
    
    except Exception as e:
        print(strWarning(f'Error occurred: {repr(e)}. Client closing.'))
        print(traceback.format_exc())
        if client.username: client.logout(client.username)