import socket, threading
from colors import *

HOST = '0.0.0.0'
PORT = 7976
VERSION_NUMBER = '1'

'''
WIRE PROTOCOL
================
    1. Version Number (1 byte)
    2. Command (1 byte)
    3. Data (variable length)
'''


'''
Might want to add logout command
Would need to restructure the initial prompting for login/register
so that it's accessible after logging out.
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

# define ChatServer class
class ChatServer:
    def __init__(self, host: str, port: str) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()

        # Global variables
        self.connections = [] # list of objects, key = username, value = username, key connected to value
        self.clients = {} # key = client, value = username
        self.usernames = [] # list of usernames
        self.queue = {} # key = client, value = list of messages
        self.logged_in = set([]) # set of clients that are logged in

        self.host_name = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host_name)

        print(f"Server started on {self.host_name} ({self.ip_addr})")


    '''
    For debugging purposes
    Shows server's global variables
    '''
    def show_state(self) -> None:
        print('*'*80)
        print('clients:', self.clients)
        print('users:', self.usernames)
        print('connections:', self.connections)
        print('queue:', self.queue)
        print('logged_in:', self.logged_in)


    def help(self) -> str:
        message = strBlue("Welcome to the chat server!") + \
        f'''
        Here are the commands you can use:
        {strBlue('/H')} - Display this help message
        {strBlue('/L')} - List all users
        {strBlue('/C')} <username> - Connect to a user
        {strBlue('/Q')} - Quit application
        {strBlue('/D')} - Delete account and exit application
        '''
        return VERSION_NUMBER + commands['DISPLAY'] + message
        

    def add_client(self, client: socket) -> None:
        self.clients[client] = ''

    
    def link_user(self, client: socket, username: str) -> None:
        self.clients[client] = username


    def remove_client(self, client: socket) -> None:
        # Remove client from connections and clients objects
        if client in self.connections:
            self.connections.pop(client)
        self.clients.pop(client)
        self.logged_in.remove(client)
        client.close()


    def broadcast(self, message: str) -> None:
        for client in self.clients:
            msg = VERSION_NUMBER + commands['DISPLAY'] + message
            client.send(msg.encode('utf-8'))


    def handle(self, client: socket) -> None:
       
        self.show_state() # For debugging purposes

        while True:
            try:
                message = client.recv(1024)
                if message[1] == commands['HELP']:
                    client.send(self.help().encode('utf-8'))
                elif message[1] == commands['LIST_USERS']:
                    self.list_users()
                elif message[1] == commands['CONNECT']:
                    self.connect(message[2:])
                elif message[1] == commands['DELETE']:
                    self.delete_account()
                elif message[1] == commands['TEXT']:
                    if message[2:]: self.text(message[2:])
                elif message[1] == commands['EXIT_CHAT']:
                    self.exit_chat()
                elif message[1] == commands['NOTHING']:
                    pass
                # Still need to add text, exit chat, and nothing commands

            except:
                self.remove_client(client)

    '''
    Handles initial login/register prompt. 
    Takes in client and username.
    Returns error message if any.
    '''
    def login_register(self, client: socket, username: str) -> str:
        error_msg = ''
        
        # Check if request is for login
        if username[1] == commands['LOGIN']:
            username = username[2:]
            
            # Check if username exists
            if username not in self.usernames:
                error_msg = 'Username does not exist'

            # Check if user is already logged in
            elif username in self.logged_in:
                error_msg = 'User already logged in'

            else:
                self.link_user(client, username)
                self.logged_in.add(client)
                print(f"User {username} logged in")
                print(f"Current users: {self.usernames}")

        # Check if request is for creating new account
        elif username[1] == commands['REGISTER']:
            username = username[2:]
            
            # Check if username already exists
            if username in self.usernames:
                error_msg = 'Username already exists'

            else:
                self.usernames.append(username)
                self.link_user(client, username)
                self.logged_in.add(client)
                self.connections.append({username: []})
                print(f"New user {username} created")
                print(f"Current users: {self.usernames}")
        
        return error_msg

    def receive(self):
        while True:
            client, addr = self.server.accept()
            print(f"Connected with {str(addr)}")
            client.send("Connected to server".encode('utf-8'))

            self.add_client(client)
            error_msg = '''
Welcome to the chat app! Please choose an option:
1. Login (L)
2. Register (R)
            '''
            # Prompt user to login or create account before creating thread
            while True:
                client.send((VERSION_NUMBER + commands['PROMPT'] + error_msg).encode('utf-8'))
                username = client.recv(1024).decode('utf-8')
                error_msg = self.login_register(client, username)
                
                if error_msg == '':
                    break

            print(f"New account created with username: {username}") # debugging purposes
            # Display list of available commands
            client.send(self.help().encode('utf-8'))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


chatServer = ChatServer(HOST, PORT)
chatServer.receive()