import socket
import threading
import fnmatch
from account import Account
from commands import opcodes

HOST = '0.0.0.0'
PORT = 51234
HOSTNAME = socket.gethostname()
IP = socket.gethostbyname(HOSTNAME)

def login(username, client):
    return_message = ''
    if username not in accounts:
        return_message = 'User not registered'
    elif username in loggedIn:
        return_message = 'User is already logged in!'
    else:
        clients[client] = username
        connectedTo[username] = ''
        loggedIn.append(username)
    return return_message

def createAccount(username, client):
    if username in accounts:
        return_message = 'User already registered!'
    else:
        accounts[username] = Account(username)
        return_message = login(username, client)
    return return_message

def delAccount(client):
    return_message = "Account deleted"
    loggedIn.remove(clients[client])
    accounts.remove(clients[client])
    clients[client] = ''
    return ((opcodes['exit'] + return_message).encode('ascii'))

def list(client, wildcard):
    return_accounts = fnmatch.filter(list(accounts), wildcard)
    return ((opcodes['SHOW'] + '\n'.join(return_accounts)).encode('ascii'))    

def check_unread_messages(client):
    user = clients[client]
    out = ""
    for key, val in queue[user].items():
        out += 'You have unread messages from: ' + str(key) + '\n'
    return out


# called whenever user submits a "non-command". Needs to be updated when actually connecting users,
# Also storing a client object as a dictionary key might be a bit weird, haven't totally figured it out yet.
def text(client, message):

    sender = client # client code

    receiver = connectedTo[clients[client]] # username

    if not receiver:
        client.send((opcodes['SHOW'] + 'You currently are not connected to anyone.').encode('ascii'))
        return

    receiver_address = ''
    for key, val in clients.items():
        if val == receiver:
            receiver_address = key
            break

    if (receiver in connectedTo) and (connectedTo[receiver] == clients[sender]): # comparing usernames
            receiver_address.send((opcodes['SHOW'] + clients[client] + ': ' + message).encode('ascii'))

    else:
        # Tell client that reciever is not in chat anymore, but sent messages will be saved for htem
        # store the messages
        if receiver in queue:
            if clients[sender] in queue[receiver]:
                queue[receiver][clients[sender]].append(message)
            else: queue[receiver][clients[sender]] = [message]
        else:
            queue[receiver] = {clients[sender]:[message]}

        client.send((opcodes['SHOW'] + 'The recipient has disconnected. Your chats will be saved. ').encode('ascii'))


# conditional logic for connecting to another user. Updates connections accordingly.
def connect(client, message):
    if message not in accounts:
        print(message)
        client.send((opcodes['SHOW'] + 'user not found. Retry').encode('ascii'))
    else:
        # do not allow user to connect to oneself.
        if clients[client] == message:
            client.send((opcodes['SHOW'] + 'Cant connect to self! Retry').encode('ascii'))
        else:
            connectedTo[clients[client]] = message

            client.send((opcodes['startchat'] + 'You are now connected to ' + message + '! You may now begin chatting. To exit, type "/E"').encode('ascii'))

            out = ''
            if clients[client] in queue:
                if message[2:] in queue[clients[client]]:
                    for m in queue[clients[client]][message[2:]]:
                        out += message + ': ' + m + '\n'

                    queue[clients[client]][message[2:]] = []

            client.send((opcodes['SHOW_TEXT'] + out).encode('ascii'))

def parseArgs(client):
    while True:

        # for debugging purposes
        print('*'*80)
        print('clients:', clients)
        print('users:', accounts)
        print('connections:', connectedTo)
        print('queue:', queue)

        try:
            received = client.recv(1024).decode()
            if len(received) > 0:
                command = received[0]
                args = received[1:]
                
            if command == opcodes['CONNECT']:
                connect(client, args)
            elif command == opcodes['TEXT']:
                text(client, args)
            elif command == opcodes['SHOW']:
                client.send(list(client, args))
            elif command == opcodes['DELETE']:
                client.send(delAccount(client))
            elif command == opcodes['EXIT_CHAT']:
                client.send(exit(client, args))
            else:
                client.send((opcodes['SHOW'] + '').encode('ascii'))
        except:
            loggedIn.remove(clients[client])
            if client in connectedTo:
                connectedTo.pop(client)
            clients.pop(client)
            client.close()
            break

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create an INET, STREAMing socket
server.bind((IP, PORT)) # bind socket to port
server.listen()

print("Became server socket")

accounts = {} # accounts[username] stores the Account instance of a user
clients = {} 
connectedTo = {} # maps connections for chat threads
queue = {}
loggedIn = set([]) # list of who is currently logged in

def receive():
    while True:
        client, address = server.accept()

        print(f"client: {str(client)}")
        print(f"address: {str(address)}")

        clients[client] = '' # initialize client in clients dictionary
        return_message = ''
        username = ''
        print("Connected with {}".format(str(address)))
        while True:
            client.send((opcodes['INPUT'] + return_message).encode('ascii'))
            command = client.recv(1024).decode('ascii') # reads at most 1024 bytes
            if len(command) > 1: # check if command length is more than one
                opcode = command[0]
                username = command[1:]
                if opcode == opcodes["createaccount"]:
                    return_message = createAccount(username, client)
                elif opcode == opcodes["login"]:
                    return_message = login(username, client)
                if return_message == '':
                    break
                else:
                    print(return_message)


        print(f"{username} logged in")
        client.send((opcodes['SHOW'] + \
            'Logged in! Commands: connect [username] (connect with a user), list <wildcard> (show list of users), delaccount (delete account, quit)\n' + check_unread_messages(client)).encode('ascii'))
        thread = threading.Thread(target=parseArgs, args=(client,))
        thread.start()

receive()
