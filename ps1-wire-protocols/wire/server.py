import socket, threading
from colors import *
from time import sleep
import traceback
import fnmatch

HOST = '0.0.0.0'
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
}


def text_message_from(username: str, message: str) -> str:
    '''
    Returns formatted text message, with username in cyan
    '''
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
        print('='*80)
        print('Clients:', self.clients)
        print('Users:', self.usernames)
        print('Connections:', self.connections)
        print('Queued Messages:', self.queued_msgs)
        print('Logged in:', self.logged_in)

    
    def handle(self, client: socket.socket) -> None:
        '''
        Handles client requests
        New thread for each client
        '''
        
        self.show_state() # For debugging purposes

        while True:
            try:
                
                # Prompt client to make a request if they are not
                # in connected state. If in connected state, handled
                # by write thread in client file.
                if self.connections[self.clients[client]] == '':
                    self.prompt(client) # Prompt client to make a request
                
                message = client.recv(1024).decode('utf-8')
                
                # Handle client dropping connection
                if not message:
                    username = self.clients[client]
                    if self.connections[username] != '':
                        self.disconnect(client) 
                    self.logout(client, username)
                    self.remove_client(client)
                    print(strWarning("Client disconnected after logging in."))
                    return

                # Handle different client requests
                if message[1] == commands['HELP']:
                    self.help(client)

                elif message[1] == commands['LIST_USERS']:
                    query = ''
                    if len(message) >= 3: query = message[2:]
                    self.list_users(client, query)

                elif message[1] == commands['CONNECT']:
                    if len(message) < 3:
                        self.show_client(client, strWarning("Username is missing!"))
                        continue
                    username = message[2:]
                    self.connect(client, username)

                elif message[1] == commands['TEXT']:
                    self.send_message(client, message)

                elif message[1] == commands['EXIT_CHAT']:
                    self.disconnect(client)

                elif message[1] == commands['DELETE']:
                    self.delete_account(client)
                    return # Close client connection

                elif message[1] == commands['QUIT']:
                    self.close_client(client)
                    return # Close client connection

            except Exception as e:
                print(f"Error from handle function: {strFail(repr(e))}")
                print(traceback.format_exc())
                break


    def receive(self) -> None:
        '''
        Accepts incoming connections.
        Handles login/register before creating thread.
        '''
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
            
            except KeyboardInterrupt:
                print(strWarning("Server stopped by user."))
                quit_clients = VERSION_NUMBER + commands['QUIT'] + ''
                self.broadcast(quit_clients)
                self.server.close()
                break

            except Exception as e:
                print(f"Error from receive function: {strFail(repr(e))}")
                self.show_state()

    ### Helper functions ###
    def broadcast(self, message: str) -> None:
        '''
        Sends message to all clients
        '''
        for client in self.clients:
            client.send(message.encode('utf-8'))


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


    def handle_login_register(self, client: socket.socket, username: str) -> str:
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
        '''
        Prompts client for input
        '''
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


    def list_users(self, client: socket.socket, query: str) -> None:
        '''
        Lists all users.
        If query is provided, lists all users that match query.
        '''

        message = 'Users:\n'

        if not query: query = '*' # if no query, list all users

        # Check if query is valid -- must be wildcard at beginning or end
        if '*' in query:
            if not query.startswith('*') and not query.endswith('*'):
                self.show_client(client, strWarning("Wildcard must be at the beginning or end of query."))
                return

        # Use fnmatch to filter usernames
        filtered = fnmatch.filter(self.usernames, query)
        for username in filtered:
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

        # Disconnect other user if connected
        for other in self.connections:
            # find other user that is connected to this user
            if self.connections[other] == username:
                # find client of other user
                for conn, user in self.clients.items():
                    if user == other:
                        other_client = conn
                        break
                # disconnect other user
                self.disconnect(other_client)
        
        self.show_client(client, strCyan("Account deleted. Quitting application..."))
        client.send((VERSION_NUMBER + commands['QUIT'] + '').encode('utf-8'))


    def connect(self, client: socket.socket, other_user: str) -> None:
        '''
        Connects client to other user
        If successful, allows client to send messages to other user
        Messages added to queue if connection is not mutual
        '''
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
        sleep(0.1)
        # Check if user has any queued messages from other user
        if other_user in self.queued_msgs[username]:
            if len(self.queued_msgs[username][other_user]) > 0:
                unread_msgs = f"{strWarning('You have queued messages from')} {other_user}{strWarning(':')}\n"
                for msg in self.queued_msgs[username][other_user]:
                    unread_msgs += text_message_from(other_user, msg) + '\n'

                self.queued_msgs[username][other_user] = [] # clear queued messages
                self.show_client(client, unread_msgs) # display queued messages

        # Check if connection is mutual
        if self.connections[other_user] == username:
            # Alert user that other user is connected to them
            self.show_client(client, strGreen(f"{other_user} is connected to you!"))
            for client, user in self.clients.items():
                if user == other_user:
                    other_client = client
                    break
            # Alert other user that user just connected to them
            self.show_client(other_client, strGreen(f"{username} has connected!"))
            return
        
        else:
            self.show_client(client, strWarning(f"{other_user} is not connected to you. Sent messages will be queued!"))
            

    def disconnect(self, client: socket.socket) -> None:
        '''
        Disconnects client from other user
        '''
        # Disconnect from other user
        username = self.clients[client]
        other = self.connections[username]
        self.connections[username] = ''
        self.show_client(client, strCyan(f"Disconnected from {other}."))

        # Alert other that user has disconnected
        if other in self.usernames:
            if self.connections[other] == username:
                for client, user in self.clients.items():
                    if user == other:
                        other_client = client
                        break
                self.show_client(other_client, strWarning(f"{username} has disconnected. Sent messages will be queued until they reconnect!"))


    def send_message(self, client: socket.socket, message: str) -> None:
        '''
        Sends message to other user.
        Only sends message if client is connected to other user.
        '''
        username = self.clients[client]
        other = self.connections[username]

        # Check if user is connected to another user
        if not other:
            self.show_client(client, strWarning("You are not connected to another user. Type /H for list of commands."))
            return

        # Check if message is empty
        if len(message) < 3:
            self.show_client(client, strWarning("Message is missing!"))
            return
        
        message = message[2:]

        # Queue message if other user is not mutually connected
        if self.connections[other] != username:
            if username not in self.queued_msgs[other]:
                self.queued_msgs[other][username] = [] # create new list for queued messages
            self.queued_msgs[other][username].append(message)
            return

        # Send message to other user
        for client, user in self.clients.items():
            if user == other:
                other_client = client
                break

        self.show_client(other_client, text_message_from(username, message))


if __name__ == '__main__':
    chat_server = ChatServer(HOST, PORT)
    chat_server.receive()


