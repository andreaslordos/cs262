from concurrent import futures
import logging
import fnmatch
from colors import *

import grpc
import chat_pb2
import chat_pb2_grpc

host = '0.0.0.0'
port = 7976

logging.basicConfig(format='[%(asctime)-15s]: %(message)s', level=logging.INFO)

class ChatServer(chat_pb2_grpc.ChatService):
    def __init__(self) -> None:
        self.usernames = [] # list of usernames
        self.user_info = {} # key = username, value = {"messages": [], "queue": []}
        self.connections = {} # key = username, value = username, key connected to value
        self.logged_in = set([]) # set of users that are logged in

    """
        The chat service definition.
    """

    def show_state(self) -> None:
        '''
        For debugging purposes
        Shows server's global variables
        '''
        print('='*80)
        print('Users:', self.usernames)
        print('Connections:', self.connections)
        print('User info:', self.user_info)
        print('Logged in:', self.logged_in)


    def add_user(self, username: str) -> None:
        '''
        Adds username to usernames list and initializes object for user in connections list.
        '''
        self.usernames.append(username)
        self.user_info[username] = {}
        self.user_info[username]["messages"] = []
        self.user_info[username]["queue"] = []
        self.connections[username] = ''


    def remove_user(self, username: str) -> None:
        '''
        Removes username from usernames list and removes object for user in connections list.
        '''
        self.usernames.remove(username)

        # TODO: need to disconnect everyone else that is connected to this user

        del self.connections[username]
        
                

    def send_msg_to_client(self, username: str, msg: str) -> None:
        '''
        Sends message to client
        '''
        chat_msg = chat_pb2.ChatMessage()
        chat_msg.sender = 'server'
        chat_msg.to = username
        chat_msg.message = msg
        self.user_info[username]["messages"].append(chat_msg)
    

    def Login(self, request: chat_pb2.User, context) -> chat_pb2.User:
        '''
        Login function
        '''
        username = request.name

        res = chat_pb2.User()
        err = ''

        # check if username valid
        if not username:
            err = 'Username cannot be empty. Please try again.'
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(err)

        elif ' ' in username:
            err = 'Username cannot have whitespaces. Please try again.'
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(err)

        # check if user doesn't exist
        elif username not in self.usernames:
            err = 'Account does not exist. Register or try again.'
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(err)

        # check if user already logged in
        elif username in self.logged_in:
            err = 'Account already logged in!'
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(err)


        if not err:
            self.logged_in.add(username)
            res.name = username
            err = f"User {username} logged in."
        
        logging.info(err)
        #self.show_state()

        return res


    def Logout(self, request: chat_pb2.User, context) -> chat_pb2.User:
        '''
        Logout function
        '''
        username = request.name
        err = ''
        res = chat_pb2.User()
        
        # check if user is logged in
        if username not in self.logged_in:
            err = 'User not logged in.'
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(err)

        if not err:
            err = f"{username} logged out."
            self.logged_in.remove(username)
            if self.connections[username]: self.connections[username] = ''
            res.name = username

        logging.info(err)
        #self.show_state()
        return res


    def Register(self, request: chat_pb2.User, context) -> chat_pb2.User:
        '''
        Register function
        '''
        username = request.name
        res = chat_pb2.User()
        err = ''

        # check if username valid
        if not username:
            err = 'Username cannot be empty. Please try again.'
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(err)

        elif ' ' in username:
            err = 'Username cannot have whitespaces. Please try again.'
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(err)
            
        # check if user already exists
        elif username in self.usernames:
            err = 'Account already exists. Please try a different username.'
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(err)
        
        elif not err:
            self.add_user(username)
            self.logged_in.add(username)
            res.name = username
            err = f"User {username} logged in."

        logging.info(err)
        # self.show_state()

        return res
        

    def GetUsers(self, request: chat_pb2.SearchQuery, context) -> chat_pb2.ListOfUsernames:
        '''
        Lists all users.
        If query is provided, lists all users that match query.
        '''

        query = request.query
        if not query: query = '*' # if no query, list all users

        # Check if query is valid -- must be wildcard at beginning or end
        if '*' in query:
            if not query.startswith('*') and not query.endswith('*'):
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details('Wildcard must be at the beginning or end of query.')
                return chat_pb2.ListOfUsernames()

        # Use fnmatch to filter usernames
        filtered = fnmatch.filter(self.usernames, query)
        return chat_pb2.ListOfUsernames(usernames=filtered)


    def Connect(self, request: chat_pb2.ChatMessage, context) -> chat_pb2.User:
        '''
        Connects one user to another
        If successful, allows user to send messages to other user
        Messages added to queue if connection is not mutual
        '''
        username = request.sender
        other_username = request.to
        err = ''

        # Check if username is valid
        if not other_username:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Cannot connect to empty username!')
            err = f'Cannot connect to empty username!'

        elif ' ' in other_username:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Cannot connect to username with whitespaces!')
            err = f'Cannot connect to username with whitespaces!'

        # Check if requested user exists
        elif other_username not in self.usernames:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f'User {other_username} does not exist!')
            err = f'User {other_username} does not exist!'

        # Check if own username is not the same as other username
        elif username == other_username:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'Cannot connect to self!')
            err = f'Cannot connect to self!'

        
        if err:
            logging.info(err)
            return chat_pb2.User()
        
        self.connections[username] = other_username
        logging.info(f'{username} connected to {other_username}')

        # Check if connection is mutual
        if self.connections[other_username] == username:
            # let user know that other user is connected
            self.send_msg_to_client(username, strCyan(f'{other_username} is connected!'))

            # let other user know that user connected to them
            self.send_msg_to_client(other_username, strCyan(f'{username} just connected to you!'))

        else:
            # let user know that other user is not connected
            self.send_msg_to_client(username, strWarning(f'{other_username} is not connected. Your messages will be queued until they connect.'))

        # Check if user has any queued messages
        if self.user_info[username]["queue"]:
            self.send_msg_to_client(username, strWarning(f'You have the following unread messages from {other_username}:'))
            self.user_info[username]["messages"].extend(self.user_info[username]["queue"])
            self.user_info[username]["queue"] = []

            logging.info(f"Queued messages delivered to {username}")

        # self.show_state()
        return chat_pb2.User(name=other_username)


    def Disconnect(self, request: chat_pb2.User, context) -> chat_pb2.User:
        '''
        Disconnects user from other user
        '''
        username = request.name
        err = ''

        if not self.connections[username]:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f'User {username} is not connected to anyone!')
            err = f'User {username} is not connected to anyone!'
            logging.info(err)
            return chat_pb2.User()

        other_username = self.connections[username]
        self.connections[username] = ''
        logging.info(f'{username} disconnected from {other_username}')
        
        # let other user know that user disconnected
        if self.connections[other_username] == username:
            self.send_msg_to_client(other_username, strWarning(f'{username} just disconnected from you! Your sent messages will be queued.'))
        
        return chat_pb2.User(name=other_username)


    def ChatStream(self, request: chat_pb2.User, context) -> chat_pb2.ChatMessage:
        '''
        Returns stream of messages to user, from user's "messages" object
        Any messages added to "messages" object will be immediately sent to user
        '''
        while request.name in self.logged_in:
            while self.user_info[request.name]["messages"]:
                yield self.user_info[request.name]["messages"].pop(0)


    def SendMessage(self, request: chat_pb2.ChatMessage, context) -> chat_pb2.RequestResponse:
        '''

        '''
        err = ''
        username = request.sender
        # other_username = request.to

        # Check if user is connected to anyone
        if not self.connections[username]:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(f'User {username} is not connected to anyone!')
            err = f'User {username} is not connected to anyone!'
        
        # Check if user is connected to other user
        # elif self.connections[username] != other_username:
        #     context.set_code(grpc.StatusCode.PERMISSION_DENIED)
        #     context.set_details(f'User {username} is not connected to {other_username}!')
        #     err = f'User {username} is not connected to {other_username}!'

        if err:
            logging.info(err)
            return chat_pb2.RequestResponse(success=False)

        other_username = self.connections[username]
        # Check if other user is connected to user
        if self.connections[other_username] == username:
            self.user_info[other_username]["messages"].append(request)
            logging.info(f'Message sent from {username} to {other_username}')
        
        else:
            self.user_info[other_username]["queue"].append(request)
            #self.queued_msgs[other_username].append(request)
            logging.info(f'Message queued from {username} to {other_username}')
        
        return chat_pb2.RequestResponse(success=True)


    def Delete(self, request: chat_pb2.User, context) -> chat_pb2.Empty:
        '''
        Deletes account
        '''
        username = request.name
        err = ''

        # check if user exists
        if username not in self.usernames:
            err = 'Account does not exist. Please try again.'
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(err)
        
        # check if user is logged in
        elif username not in self.logged_in:
            err = 'User not logged in.'
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(err)
        
        if not err:
            # check if any other user is connected to user
            for other in self.connections:
                if self.connections[other] == username:
                    self.Disconnect(chat_pb2.User(name=other), context)
                    self.send_msg_to_client(other, strWarning(f'{username} just deleted their account!'))

            # delete user
            self.logged_in.remove(username)
            self.usernames.remove(username)
            self.user_info.pop(username)
            err = f"User {username} deleted."

        logging.info(err)
        # self.show_state()

        return chat_pb2.Empty()


    def Quit(self, request: chat_pb2.User, context) -> chat_pb2.Empty:
        '''

        '''
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')



def serve():
    # ChatService
    servicer = ChatServer()

    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f'{host}:{port}')
    server.start()

    logging.info(f'GRPC server started, listening on port {port}')
    
    # Run until interrupted
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info('Stopping Server')


if __name__ == '__main__':
    serve()