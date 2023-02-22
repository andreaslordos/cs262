import socket, threading
import logging
from concurrent import futures


import grpc
import messaging_pb2
import messaging_pb2_grpc

host = '127.0.0.1'
port = 7976

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


VERSION_NUMBER = '1'
commands = {'LOGIN': '1',
            "CREATE": '2',
            'ENTER': '3',
            'LOGIN_NAME': '4',
            "CREATE_NAME": '5',
            'DISPLAY': '6',
            'HELP': '7',
            'SHOW': '8',
            'CONNECT': '9',
            'TEXT': 'a',
            'NOTHING': 'b',
            'DELETE': 'c',
            'EXIT_CHAT': 'd',
            'SHOW_TEXT': 'e',
            'START_CHAT': 'f',
            'REQUEST': 'g'}

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)              #socket initialization
server.bind((host, port))                                               #binding host and port to socket
server.listen()

queue = {}
USERNAMES = []
connections = {}
clients = {}

# deletes a username from list of usernames, removes the association from the client, and sends the appropriate message
# TODO: eventually will also have to delete undelivered messages to a deleted account
def delete_account_grpc(client, message):
    out = 'Account deleted'
    USERNAMES.remove(clients[client])
    del clients[client]
    return VERSION_NUMBER + commands['DELETE'] + out


# displays the other users on the current server.
def show_grpc(client, message):
    out = ""
    for user in USERNAMES:
        out += user + '\n'

    # I'm just using the "DISPLAY" command to display specific messages and prompt the user for another response at this point.
    return VERSION_NUMBER + commands['DISPLAY'] + out

# displays the list of possible commands.
def help_grpc(client, message):
    out = 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)'
    return VERSION_NUMBER + commands['DISPLAY'] + out

# prompts the user for another input (only used when the user just presses 'enter' without typing anything)
def prompt_grpc(message):
    return VERSION_NUMBER + commands['DISPLAY'] + ''


# called whenever user submits a "non-command". Needs to be updated when actually connecting users,
# Also storing a client object as a dictionary key might be a bit weird, haven't totally figured it out yet.
def text_grpc(client, message):
    sender = client # client code
    receiver = connections[clients[client]] # username

    # if not connected to someone, return blank
    if not receiver:
        return VERSION_NUMBER + commands['DISPLAY'] + ''

    # in gRPC version, we can never send directly to the receiver, so always add to their queue
    if receiver in queue:
        if clients[sender] in queue[receiver]:
            queue[receiver][clients[sender]].append(message[2:])
        else:
            queue[receiver][clients[sender]] = [message[2:]]
    else:
        queue[receiver] = {clients[sender]:[message[2:]]}



    # after adding to queue, if we realize they are not mutually connected, send this message back to the sender
    if not ((receiver in connections) and (connections[receiver] == clients[sender])):
        return VERSION_NUMBER + commands['SHOW_TEXT'] + 'You are not connected. Your chats will be saved. '

    # otherwise return blank
    return VERSION_NUMBER + commands['DISPLAY'] + ''



# conditional logic for connecting to another user. Updates connections accordingly.
def connect_grpc(client, message):
    if message[2:] not in USERNAMES:
        return VERSION_NUMBER + commands['DISPLAY'] + 'user not found. Please try again'
    else:
        # do not allow user to connect to oneself.
        if clients[client] == message[2:]:
            return VERSION_NUMBER + commands['DISPLAY'] + 'You cannot connect to yourself! Please try again '
        else:
            # display queued messages from this connection if applicable
            connections[clients[client]] = message[2:]
            out = ""
            if clients[client] in queue:
                if message[2:] in queue[clients[client]]:
                    for m in queue[clients[client]][message[2:]]:
                        out += bcolors.OKBLUE + message[2:] + ': ' + bcolors.ENDC + m + '\n'
                    queue[clients[client]][message[2:]] = []

            return VERSION_NUMBER + commands['START_CHAT'] + 'You are now connected to ' + message[2:] + '! You may now begin chatting. To exit, type "/E" \n' + out


# conditional logic for disconnecting from another user. Updates connections accordingly. Prompts user for new connection.
def exit_grpc(client, message):
    # disconnect
    connections[clients[client]] = ""
    return VERSION_NUMBER + commands['DISPLAY'] + 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)'


# new function for handling read thread from gRPC client
def request_grpc(client, message):

    # the client thread which continuously requests may not know the account has been deleted, so do this check just in case
    # that thread keeps running for a bit after the account is deleted
    if client not in clients:
        return VERSION_NUMBER + commands["DISPLAY"] + 'Account deleted'

    connection = connections[clients[client]]
    out = ""
    # if the client is currently connected, check queue to see if any new messages
    if connection:
        if connections[connection] == clients[client]:
            if connection in queue[clients[client]]:
                for m in queue[clients[client]][connection]:
                    out += bcolors.OKBLUE + connection + ': ' + bcolors.ENDC + m + '\n'

                queue[clients[client]][connection] = []

    return VERSION_NUMBER + commands['DISPLAY'] + out


# gRPC class
class Greeter(messaging_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        # client id is sent through metadata
        metadict = dict(context.invocation_metadata())
        client = metadict['client-id']
        message = request.details
        error_message = ''

        # debugging messages
        # logging.debug(connections)
        # logging.debug(clients)
        # logging.debug(queue)
        # logging.debug("*"*80)

        # conditionals for different types of commands

        if message[1] == commands['LOGIN_NAME']:
            if message[2:] not in USERNAMES:
                error_message = 'Username not found'
                return messaging_pb2.HelloReply(message = VERSION_NUMBER + commands["ENTER"] + error_message)

            # if client leaves without warning, their old client id will still be in connections. Delete this if the username is signed into again
            for key, val in clients.items():
                if val == message[2:]:
                    del clients[key]
                    break

            clients[client] = message[2:]
            connections[clients[client]] = ""
            return messaging_pb2.HelloReply(message = VERSION_NUMBER + commands['DISPLAY'] + \
                'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)')

        elif message[1] == commands['CREATE_NAME']:
            if message[2:] in USERNAMES:
                error_message = 'Username taken'
                return messaging_pb2.HelloReply(message = VERSION_NUMBER + commands["ENTER"] + error_message)
            else:
                USERNAMES.append(message[2:])

                # if client leaves without warning, their old client id will still be in connections. Delete this if the username is signed into again
                for key, val in clients.items():
                    if val == message[2:]:
                        del clients[key]
                        break

                clients[client] = message[2:]
                connections[clients[client]] = ""
                queue[clients[client]] = {}
                return messaging_pb2.HelloReply(message = VERSION_NUMBER + commands['DISPLAY'] + \
                    'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)')

        elif message[1] == commands['REQUEST']:
            return messaging_pb2.HelloReply(message = request_grpc(client, message))
        elif message[1] == commands['CONNECT']:
            return messaging_pb2.HelloReply(message = connect_grpc(client, message))
        elif message[1] == commands['TEXT']:
            return messaging_pb2.HelloReply(message = text_grpc(client, message))
        elif message[1] == commands['SHOW']:
            return messaging_pb2.HelloReply(message = show_grpc(client, message))
        elif message[1] == commands['HELP']:
            return messaging_pb2.HelloReply(message = help_grpc(client, message))
        elif message[1] == commands['DELETE']:
            return messaging_pb2.HelloReply(message = delete_account_grpc(client, message))
        elif message[1] == commands['EXIT_CHAT']:
            return messaging_pb2.HelloReply(message = exit_grpc(client, message))
        else:
            return messaging_pb2.HelloReply(message = prompt_grpc(message))


    # probably won't need this
    def SayHelloAgain(self, request, context):
        return messaging_pb2.HelloReply(message=f'Hello again, {request.details}!')



def serve():
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messaging_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
    serve()
