import socket, threading
username = ""

# USER MODIFY THE FOLLOWING LINE WITH IP_ADDRESS OF SERVER
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
        return "createaccount " + username

def receive():
    global username
    while True:

        try:
            m = login_message()
            client.send(m.encode('ascii'))

        except Exception as e:
            print("An error occured!")
            print(e)
            client.close()
            break

receive_thread = threading.Thread(target=receive) #receiving multiple messages
receive_thread.start()