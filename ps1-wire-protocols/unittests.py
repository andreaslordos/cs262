import unittest
import socket
import server
import client

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
            'START_CHAT': 'f'}

class Test(unittest.TestCase):

    def setUp(self):
        host = '0.0.0.0'
        port = 7976

        self.mock_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_server.bind((host, port))
        self.mock_server.listen()

        self.mock_client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_client1.connect(('127.0.0.1', 7976))

        self.mock_client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_client2.connect(('127.0.0.1', 7976))


    def tearDown(self):
        self.mock_client1.close()
        self.mock_client2.close()
        self.mock_server.close()

    """ SERVER SIDE """
    # Attempt login with non-existent username
    def test_login(self):
        username = VERSION_NUMBER + commands['LOGIN_NAME'] + 'name0'
        error = server.login_username(username, self.mock_client1)
        self.assertEqual(error, 'Username not found')

    # Attempt creating account with existing username
    def test_create(self):
        username = VERSION_NUMBER + commands['CREATE_NAME'] + 'name1'
        _ = server.login_username(username, self.mock_client1)
        error = server.login_username(username, self.mock_client2)
        self.assertEqual(error, 'Username taken')

    # Attempt deleting an account
    def test_delete(self):
        server.clients = {self.mock_client1:'name1'}
        message = server.delete_account(self.mock_client1, '')
        self.assertIn('Account deleted', str(message[2:]))

    # Attempt exiting from a connection
    def test_exit(self):
        server.clients = {self.mock_client2:'name2'}
        server.connections = {'name2':'name1'}
        server.exit(self.mock_client2, '')
        self.assertEqual('', server.connections['name2'])

    def test_server_show(self):
        server.USERNAMES = ['n1','n2']
        server.clients = {self.mock_client1:'name1'}
        lst = server.show(self.mock_client1, '')
        for user in server.USERNAMES:
            self.assertIn(user, str(lst))

    """ CLIENT SIDE """
    def test_nothing(self):
        message = ''
        error = client.parse_arg(message)
        self.assertIn(commands['NOTHING'], error)

    # test client side commands: /C
    def test_connect(self):
        message = '/C'
        error = client.parse_arg(message)
        self.assertIn(commands['CONNECT'], error)

    def test_show(self):
        message = '/S'
        error = client.parse_arg(message)
        self.assertIn(commands['SHOW'], error)

    def test_help(self):
        message = '/H'
        error = client.parse_arg(message)
        self.assertIn(commands['HELP'], error)

    def test_delete_client(self):
        message = '/D'
        error = client.parse_arg(message)
        self.assertIn(commands['DELETE'], error)

    def test_delete_client(self):
        message = '/D'
        error = client.parse_arg(message)
        self.assertIn(commands['DELETE'], error)

    def send_exittext_client(self):
        message = '/E'
        error = client.send_text(message)
        self.assertIn(commands['EXIT_CHAT'], error)

    def send_regtext_client(self):
        message = 'hi'
        error = client.send_text(message)
        self.assertIn(commands['TEXT'], error)




if __name__ == '__main__':
    unittest.main()
