import socket
import threading
import fnmatch

HOST = '0.0.0.0'
PORT = 51234
HOSTNAME = socket.gethostname()
IP = socket.gethostbyname(HOSTNAME)

print(f"Computer Name: {HOSTNAME}")
print(f"Computer IP: {IP}")

accounts = {}
clients = {}
connectedTo = {}
loggedIn = []

class Account:
    def __init__(self, username):
        self.username = username
        self.messageQueue = []



def login(username, client):
    error_message = ''
    if username not in accounts:
        error_message = 'User not registered'
    elif username in loggedIn:
        error_message = 'User is already logged in!'
    else:
        clients[client] = username
        connectedTo[username] = ''
        loggedIn.append(username)
    return error_message

def createAccount(username, client):
    if username in accounts:
        error_message = 'User already registered!'
    else:
        accounts[username] = Account(username)
        error_message = login(username, client)
    return error_message


# TODO: Replace prints with send to client socket
def parseArgs(command):
    opcode = command.split(" ")[0] # first argument of command should be an opcode
    args = command.split(" ")[1:] # everything else is arguments
    match opcode:
        
        case 'createaccount':
            if len(args) == 1:
                username = args[0]
                if len(username) > 0:
                    if (username not in accounts):
                        accounts[username] = Account(username)
                    else:
                        print("Error")
                else:
                    print("Error")
            else:
                print("Error")
        
        case 'login':
            if len(args) == 1:
                username = args[0]
                if len(username) > 0:
                    if (username in accounts):
                        pass
                        # do stuff with message queue
                    else:
                        print("Error")
                else:
                    print("Error")
            else:
                print("Error")
                
        case 'list':
            if len(args) == 1:
                return_accounts = fnmatch.filter(list(accounts), args[1])
                print("\n".join(return_accounts))  
            else:
                print("Error")  
        case 'delaccount':
            pass
            # do something
        
        case 'sendmessage':
            pass
            # do something
        
        case other:
            print("Error")
        

def clientthread(conn):
	while True:
		try:
			data = conn.recv(4096)
			if not data: 
				for username in accounts:
					if accounts[username].socket == conn:
						accounts[username].socket = None
				break
			interpret(data, conn)
		except:
			#conn.send('[FAILURE]'.encode('utf-8'))
			continue


# create an INET, STREAMing socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket
server.bind((IP, PORT))
# become a server socket, accept max 5 connecetions
server.listen(5)

print("Became server socket")


while True:
    try:
        client, address = server.accept()

        print(f"client: {str(client)}")
        print(f"address: {str(address)}")

        clients[client] = '' # initialize client in clients dictionary
        error_message = ''
        username = ''
        print("Connected with {}".format(str(address)))
        while True:
            command = client.recv(1024).decode('utf-8') # reads at most 1024 bytes
            print(f"Printing command: {command}")
            opcode = command.split(" ")[0]
            username = command.split(" ")[1]
            if len(opcode) > 0 and len(username) > 0:
                if opcode == "createaccount":
                    error_message = createAccount(username, client)
                    print(f"Created account for {username}")
                elif opcode == "login":
                    error_message = login(username, client)
            if error_message == '':
                break
            else:
                print(error_message)

        print("Username is {}".format(username))
        # need to start thread
    except KeyboardInterrupt:
        client.close()
        break

client.close()
server.close()



