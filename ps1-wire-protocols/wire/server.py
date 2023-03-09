import socket, threading
from colors import *
from time import sleep

HOST = '0.0.0.0'
PORT = 7978
VERSION_NUMBER = '8'

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

commands = {'LOGIN_PROMPT': '1', # Prompt for login/create account
            'LOGIN': '2', # Request for logging in
            'REGISTER': '3', # Request for creating new account
            'DISPLAY': '4', # Display message to client terminal and await response
            'HELP': '5', # Display help
            'LIST_USERS': '6', # Display list of users
            'CONNECT': '7', # Request to connect to a user
            'TEXT': '8', # Send text to a user
            'NOTHING': '9', # When client sends empty message
            'DELETE': 'a', # Request for deleting account
            'EXIT_CHAT': 'b', # Request for exiting chat
            'PROMPT': 'c', # Prompt client for response
            'START_CHAT': 'd', # Response to client's request to connect to user
            'QUIT': 'e', # Request for quitting application
            'ERROR': 'f', # Error message
}


def text_message_from(username: str, message: str) -> str:
    return f"{strCyan(username)}: {message}"


# define ChatServer class
class ChatServer:
    def __init__(self, host: str, port: str) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()

        # Global variables
        self.clients = {} # key = client, value = username
        self.usernames = [] # list of usernames
        self.connections = {} # key = username, value = username, key connected to value
        self.queued_msgs = {} # key = username, value = dict of "user": [messages]
        self.logged_in = set([]) # set of users that are logged in

        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname(hostname)
        print(f"Server started on {hostname} ({ip_addr})")


    def show_state(self) -> None:
        '''
        For debugging purposes
        Shows server's global variables
        '''
        print('*'*80)
        print('clients:', self.clients)
        print('users:', self.usernames)
        print('connections:', self.connections)
        print('queue:', self.queued_msgs)
        print('logged_in:', self.logged_in)

    
    def handle(self, client: socket.socket) -> None:
        
        self.show_state()

        while True:
            try:
                self.prompt(client)
                message = client.recv(1024).decode('utf-8')
                
                if not message:
                    username = self.clients[client] 
                    self.logout(client, username)
                    self.remove_client(client)
                    print(strWarning("Client disconnected after logging in."))
                    return

                print(f"Received from client: {message}")

                if message[1] == commands['HELP']:
                    self.help(client)
                elif message[1] == commands['LIST_USERS']:
                    self.list_users(client)
                elif message[1] == commands['CONNECT']:
                    if len(message) < 3:
                        self.show_client(client, strWarning("Username is missing!"))
                        continue
                    username = message[2:]
                    self.connect(client, username)
                elif message[1] == commands['TEXT']:
                    pass
                elif message[1] == commands['DELETE']:
                    self.delete_account(client)
                    return
                elif message[1] == commands['EXIT_CHAT']:
                    pass
                elif message[1] == commands['QUIT']:
                    self.close_client(client)
                    return
                elif message[1] == commands['ERROR']:
                    pass

            except Exception as e:
                print(f"Error from handle function: {strFail(repr(e))}")
                break


    def receive(self) -> None:
        while True:
            try:
                client, address = self.server.accept()
                print(f"Connected with {str(address)}")
                self.show_client(client, strCyan("Connected to server"))
                self.add_client(client)

                response = ''
                error_msg = ''
                # Prompt user to login or create account before creating thread
                while True:
                    if error_msg: 
                        self.show_client(client, error_msg)
                    client.send((VERSION_NUMBER + commands['LOGIN_PROMPT'] + '').encode('utf-8'))
                    response = client.recv(1024).decode('utf-8')
                    error_msg = self.handle_login_register(client, response)
                    
                    if error_msg == '' or error_msg == 'ERR':
                        break
                
                # No response received from client
                if error_msg == 'ERR': 
                    self.remove_client(client)
                    print(strWarning("Client disconnected before logging in."))
                
                # Client logged in successfully
                else:
                    self.show_client(client, strBlue('You are now logged in!\n'))
                    self.help(client)

                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()
            
            except Exception as e:
                print(f"Error from receive function: {strFail(repr(e))}")
                self.show_state()

    ### Helper functions ### 

    def add_client(self, client: socket.socket) -> None:
        '''
        Adds client to clients dictionary, initialized with empty username.
        '''
        self.clients[client] = ''


    def remove_client(self, client: socket.socket) -> None:
        '''
        Removes client from clients dictionary.
        '''
        del self.clients[client]


    def add_user(self, username: str) -> None:
        '''
        Adds username to usernames list and initializes object for user in connections list.
        '''
        self.usernames.append(username)
        self.connections[username] = ''
        self.queued_msgs[username] = {}


    # STILL NEED TO TEST THAT QUEUED MESSAGES ARE DELETED
    def remove_user(self, username: str) -> None:
        '''
        Removes username from usernames list and removes object for user in connections list.
        '''
        self.usernames.remove(username)

        # TODO: need to disconnect everyone else that is connected to this user

        del self.connections[username]
        self.queued_msgs.pop(username)

        # delete queued messages from this user to others
        for other in self.queued_msgs:
            if username in self.queued_msgs[other]:
                del self.queued_msgs[other][username]


    def link_user(self, client: socket.socket, username: str) -> None:
        '''
        Links client to username in clients dictionary.
        '''
        self.clients[client] = username


    def login(self, client: socket.socket, username: str) -> None:
        '''
        Adds username to logged_in set and links client to username.
        '''
        self.link_user(client, username)
        self.logged_in.add(username)


    def logout(self, client: socket.socket, username: str) -> None:
        '''
        Removes username from logged_in set and unlinks client from username.
        '''
        self.logged_in.remove(username)

    
    def show_client(self, client: socket.socket, message: str,) -> None:
        '''
        Displays message to client
        '''
        client.send((VERSION_NUMBER + commands['DISPLAY'] + message).encode('utf-8'))
        sleep(0.1)


    def handle_login_register(self, client: socket, username: str) -> str:
        '''
        Handles initial login/register prompt.
        Takes in client and username.
        Returns error message if any.
        '''
        error_msg = ''

        # Check if username is empty -- only happens if client unexpectedly shuts down
        if not username or len(username) < 2:
            error_msg = 'ERR'
        
        # Check if request is for login
        elif username[1] == commands['LOGIN']:
            username = username[2:]
            
            # Check if username exists
            if username not in self.usernames:
                error_msg = 'Username does not exist'

            # Check if user is already logged in
            elif username in self.logged_in:
                error_msg = 'User already logged in'

            else:
                self.login(client, username)
                print(f"User {username} logged in")

        # Check if request is for creating new account
        elif username[1] == commands['REGISTER']:
            username = username[2:]
            
            # Check if username already exists
            if username in self.usernames:
                error_msg = 'Username already exists'

            else:
                self.add_user(username)
                self.login(client, username)
                print(f"New user {username} created")
        
        return error_msg


    def prompt(self, client: socket.socket) -> None:
        client.send((VERSION_NUMBER + commands['PROMPT'] + '').encode('utf-8'))
    
    ### Wrapper functions for commands ### 

    def help(self, client: socket.socket) -> None:
        '''
        Displays help message
        '''

        message = f'''
Here are the commands you can use:
{strBlue('/H')} - Display this help message
{strBlue('/L')} - List all users
{strBlue('/C')} <username> - Connect to a user
{strBlue('/Q')} - Quit application
{strBlue('/D')} - Delete account and exit application
'''
        self.show_client(client, message)


    def list_users(self, client: socket.socket) -> None:
        '''
        Lists all users
        '''

        message = 'Users:\n'

        for username in self.usernames:
            message += username + '\n'

        self.show_client(client, message)


    def close_client(self, client: socket.socket) -> None:
        '''
        Closes client connection
        '''
        username = self.clients[client] 
        self.logout(client, username)
        self.remove_client(client)
        
        self.show_client(client, strCyan("Quitting..."))
        client.send((VERSION_NUMBER + commands['QUIT'] + '').encode('utf-8'))


    def delete_account(self, client: socket.socket) -> None:
        '''
        Deletes account and closes client connection
        '''
        username = self.clients[client] 
        self.logout(client, username)
        self.remove_client(client)
        self.remove_user(username)
        
        self.show_client(client, strCyan("Account deleted. Quitting application..."))
        client.send((VERSION_NUMBER + commands['QUIT'] + '').encode('utf-8'))


    def connect(self, client: socket.socket, other_user: str) -> None:
        # Check if requested user exists
        if other_user not in self.usernames:
            self.show_client(client, strWarning("User does not exist"))
            return
        
        username = self.clients[client]
        # Check if own username
        if other_user == username:
            self.show_client(client, strWarning("You cannot connect to yourself"))
            return

        self.connections[username] = other_user
        client.send((VERSION_NUMBER + commands['START_CHAT'] + other_user).encode('utf-8'))

        # Check if user has any queued messages from other user
        if other_user in self.queued_msgs[username]:
            msgs = f"{strCyan('You have queued messages from')} {other_user}{strCyan(':')}\n"
            for msg in self.queued_msgs[username][other_user]:
                msg += text_message_from(other_user, msg) + '\n'

            self.queued_msgs[username][other_user] = [] # clear queued messages
            self.show_client(client, msgs) # display queued messages


if __name__ == '__main__':
    chat_server = ChatServer(HOST, PORT)
    chat_server.receive()


