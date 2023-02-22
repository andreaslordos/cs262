import socket, threading
from commands import opcodes

username = ""

IP_ADDRESS = '127.0.0.1'
PORT = 51234

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP_ADDRESS, PORT))





def login_message():
    global username
    choice = None
    while choice != "L" and choice != "C":
        choice = input("Enter L to login, or C to create an account: ")
    if choice == "L":
        username = input("Enter username: ")
        return "login " + username
    else:
        username = input("Create new username: ")
        return opcodes["createaccount"] + username


# parse user's input text. Specifically deal with commands beginning with '/'
def parse_arg(input):
    if not input:
        return opcodes['NOTHING'] + ''

    input_strip = "".join(input.split())

    command = 'TEXT'
    if input_strip[0] == '/':
        if input_strip[1] == 'C':
            command = 'CONNECT'
        if input_strip[1] == 'S':
            command = 'list'
        if input_strip[1] == 'D':
            command = 'DELETE'

    if command == 'TEXT':
        return opcodes[command] + input_strip
    elif command == 'list':
        return opcodes[command] + input_strip
    # if the command is not CONNECT, just send whole payload
    elif command != 'CONNECT':
        return opcodes[command] + ''
    # if the command is CONNECT, send only the part of the payload which specifies which user we are connecting to
    else:
        return opcodes[command] + input_strip[2:]

# send_text command only used when user is engaged in a chatroom. In this case, '/E' triggers chatroom exit.
def send_text(input):
    if input == '/E':
        return opcodes['EXIT_CHAT'] + 'end'
    return opcodes['TEXT'] + input


def receive():
    global username
    while True:

        try:
            message = client.recv(1024).decode('ascii')
            if message[0] == opcodes['INPUT']:
                if message[1:]:
                    print(message[1:])
                m = login_message()
                client.send(m.encode('ascii'))

            elif message[0] == opcodes['DELETE']:
                if message[1:]:
                    print(message[1:])
                return

            elif message[0] == opcodes['SHOW']:
                if message[1:]: print(message[1:])
                inp = input(":")
                m = parse_arg(inp)
                client.send(m.encode('ascii'))


            elif message[1] == opcodes['SHOW']:
                if message[1:]: print(message[1:])


            # we know we are connected to another user/in a chat room when we receive the "TEXT" command
            elif message[0] == opcodes['startchat']:
                    if message[1:]: print(message[1:])
                    write_thread = threading.Thread(target=write) #sending messages
                    write_thread.start()


            # I assume when receiving chats from other users, message should be directly printed here. Not sure if it will be this easy in practice.
            # a new color can be toggled for received chats by serverside.
            else:
                if message[1:]:
                    print(message[1:])
        except Exception as e:
            print("An error occured!")
            print(e)
            client.close()
            break



def write():
    while True:
        inp = input()
        m = send_text(inp)
        client.send(m.encode('ascii'))
        if m[0] == opcodes['EXIT_CHAT']:
            return

receive_thread = threading.Thread(target=receive) #receiving multiple messages
receive_thread.start()