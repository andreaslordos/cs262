# Wire Protocol Chat App

This is a simple TCP Chat, with two different implementations:

- wire protocol
- grpc

## Set up

After cloning the repository using `git clone https://github.com/h33m4/cs262`, navigate to the `ps-1-wire-protocols` directory using `cd ps-1-wire-protocols`. After going into the appropriate folder for the implementation you want to check out:

### Mac

First run the server using:

```
python3 server.py
```

Then run the client using:

```
python3 client.py
```

### Windows

First run the server using:

```
python server.py
```

Then run the client using:

```
python client.py
```

## Wire Implementation

Upon connecting, the client will prompt you to either login or register. Once you do, the server creates a handler thread for the client that receives and sends requests. After logging in, you can perform any of the commands in the table below. To chat to another client, you have to connect to them. Connections can be mutual, but don't have to be -- if User 1 connects to User 2 who is offline, messages sent will be queued and shown once User 2 connects to User 1.

The table below shows our commands:

| Opcode | Command Name | CLI Input + Args (! if required)  | Client Reaction | Server Reaction |
| --- | --- | --- | --- | --- |
| 1  | LOGIN_PROMPT  |  -  |  Handle login/registration. Send LOGIN/REGISTER request to server with username.  |  -  |
| 2  |  LOGIN  |  L  |  -  |  Validate username, and log user in. If unsuccessful, send error message.  |
| 3  |  REGISTER  |  R  |  -  |  Validate username, and register user. If unsuccessful, send error message.  |
| 4  |  DISPLAY  |  -  |  Display message from server to terminal.  |  -  |
| 5  |  HELP  |  /H  |  -  |  Send DISPLAY request with list of available commands.  |
| 6  |  LIST_USERS  |  /L <query> |  -  |  Send DISPLAY request with list of users. Handles wildcard query.  |
| 7  |  CONNECT  |  /C <!username>  |  -  |  Connect client to <username>. Updates global variables. Sends START_CHAT request to client. |
| 8  |  TEXT  |  -  |  -  |  Default command. If client is connected to a user, it handles sending message to that user.  |
| 9  |  NOTHING  |  -  |  -  |  -  |
| a  |  DELETE  |  /D  |  -  |  Cleans up global variables, deleting user and sending QUIT request to client.  |
| b  |  EXIT_CHAT  |  /E  |  Close write thread.  |  Disconnect client.  |
| c  |  PROMPT  |  -  |  Prompt user for input. Parse and format input and send to server.  |  -  |
| d  |  START_CHAT  |  -  |  Start write thread for chat  |    |
| e  |  QUIT  |  /Q  |  Close client, and end program  |    |


## GRPC Implementation

This implementation works more like a client making API calls -- the gRPC stub acts as the interface for the client, allowing it to make requests that return a response. Another key difference is that the messages 'sent' to the client are actually just added to some list object that is emptied into the stream the client is listening to.

With the wire, some issues that I ran into was synchronization of data being sent/received. After completing the wire implementation and then doing gRPC, I realize that one thing that could've been improved on the wire is ensuring that the data that was sent is the same as the data that was received -- i.e. including the size of the data in the wire protocol. 