import socket, threading
import sys

HOST = '0.0.0.0'
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


# define ChatServer class
class ChatServer:
    def __init__(self, host, port) -> None:
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


    def add_client(self, client):
        self.clients[client] = ''

    
    def link_user(self, client, username):
        self.clients[client] = username


    def remove_client(self, client):
        # Remove client from connections and clients objects
        if client in self.connections:
            self.connections.pop(client)
        self.clients.pop(client)
        self.logged_in.remove(client)
        client.close()


    def broadcast(self, message):
        for client in self.clients:
            client.send(message)


    def handle(self, client):
        while True:
            try:
                message = client.recv(1024)
                self.broadcast(message)
            except:
                self.remove_client(client)



    def receive(self):
        while True:
            client, addr = self.server.accept()
            print(f"Connected with {str(addr)}")
            client.send("Connected to server".encode('utf-8'))

            self.add_client(client)
            error_msg = ''

            client.send((VERSION_NUMBER + commands['PROMPT'] + error_msg).encode('utf-8')) 
            username = client.recv(1024).decode('utf-8')
            self.usernames.append(username)
            self.link_user(client, username)

            print(f"Username of client is {username}")
            self.broadcast(f"{username} has joined the chat!".encode('utf-8'))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()


chatServer = ChatServer(HOST, PORT)
chatServer.receive()