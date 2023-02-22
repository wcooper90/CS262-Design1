import socket, threading
import sys

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
            'START_CHAT': 'f'}



class Server():
    def __init__(self, host, port, commands, colors, version_number):
        self.VERSION_NUMBER = version_number
        self.colors = colors
        self.commands = commands
        self.host = host
        self.port = port
        self.hostname=socket.gethostname()
        self.IPAddr=socket.gethostbyname(self.hostname)
        print("Your Computer Name is:"+self.hostname)
        print("Your Computer IP Address is:"+self.IPAddr)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = []

        self.queue = {}
        self.USERNAMES = []
        self.connections = {}
        self.clients = {}
        self.LOGGED_IN = set([])


    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.receive()


    # deletes a username from list of usernames, removes the association from the client, and sends the appropriate message
    # TODO: eventually will also have to delete undelivered messages to a deleted account
    def delete_account(self, client, message):
        out = 'Account deleted'
        self.LOGGED_IN.remove(clients[client])
        self.USERNAMES.remove(clients[client])
        self.queue.pop(clients[client])
        self.clients[client] = ''
        return (self.VERSION_NUMBER + self.commands['DELETE'] + out).encode('ascii')



    # displays the other users on the current server.
    def show(self, client, message):

        all_users = []

        if message[4:]:
            if '*' in message[4:]:
                key = message[4:message.index('*')]
                for user in self.USERNAMES:
                    if key in user:
                        all_users.append(user)

            elif message[4:] in self.USERNAMES:
                all_users.append(message[4:])
            else:
                return (self.VERSION_NUMBER + self.commands['DISPLAY'] + "No users match").encode('ascii')
        else:
            all_users = self.USERNAMES


        out = ""
        for user in all_users:

            # Display number of unread messages from other users
            number_unread = 0
            if self.clients[client] in self.queue:
                if user in self.queue[self.clients[client]]:
                    number_unread = len(self.queue[self.clients[client]][user])

            if number_unread > 0: out += user + ' ('+str(number_unread)+' unread messages)' + '\n'
            else: out += user + '\n'

        # I'm just using the "DISPLAY" command to display specific messages and prompt the user for another response at this point.
        return (self.VERSION_NUMBER + self.commands['DISPLAY'] + out).encode('ascii')

    # displays the list of possible commands.
    def help(self, client, message):
        out = 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)'
        client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + out).encode('ascii'))

    # prompts the user for another input (only used when the user just presses 'enter' without typing anything)
    def prompt(self, client, message):
        client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + '').encode('ascii'))


    # conditional logic for logging in / creating an account. Updates USERNAMES and clients global data as necessary.
    def login_username(self, username, client):
        error_message = ''
        if username[1] == self.commands['LOGIN_NAME']:
            if username[2:] not in self.USERNAMES:
                error_message = 'Username not found'
            elif username[2:] in self.LOGGED_IN:
                error_message = 'User currently logged in!'
            else:
                self.clients[client] = username[2:]
                self.connections[username[2:]] = ''
                self.LOGGED_IN.add(username[2:])

        if username[1] == self.commands['CREATE_NAME']:
            if username[2:] in self.USERNAMES:
                error_message = 'Username taken'
            elif ' ' in username[2:]:
                error_message = "Your username can not have spaces"
            elif '*' in username[2:]:
                error_message = "You username can not have '*'"
            else:
                self.USERNAMES.append(username[2:])
                self.clients[client] = username[2:]
                self.connections[username[2:]] = ''
                self.queue[username[2:]] = {}
                self.LOGGED_IN.add(username[2:])
        return error_message


    # called whenever user submits a "non-command". Needs to be updated when actually connecting users,
    # Also storing a client object as a dictionary key might be a bit weird, haven't totally figured it out yet.
    def text(self, client, message):

        sender = client # client code

        receiver = self.connections[self.clients[client]] # username

        if not receiver:
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'You currently are not connected to anyone. Type /H for help.  ').encode('ascii'))
            return

        receiver_address = ''
        for key, val in self.clients.items():
            if val == receiver:
                receiver_address = key
                break

        if (receiver in self.connections) and (self.connections[receiver] == self.clients[sender]): # comparing usernames
                receiver_address.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + self.colors.OKBLUE + self.clients[client] + ': ' + self.colors.ENDC+ message[2:]).encode('ascii'))

        else:
            # Tell client that reciever is not in chat anymore, but sent messages will be saved for htem
            # store the messages
            if receiver in self.queue:
                if self.clients[sender] in self.queue[receiver]:
                    self.queue[receiver][self.clients[sender]].append(message[2:])
                else: self.queue[receiver][self.clients[sender]] = [message[2:]]
            else:
                self.queue[receiver] = {self.clients[sender]:[message[2:]]}

            client.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + 'The recipient has disconnected. Your chats will be saved. ').encode('ascii'))

    # conditional logic for connecting to another user. Updates connections accordingly.
    def connect(self, client, message):
        if message[2:] not in self.USERNAMES:
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'user not found. Please try again').encode('ascii'))
        else:
            # do not allow user to connect to oneself.
            if self.clients[client] == message[2:]:
                client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + 'You cannot connect to yourself! Please try again ').encode('ascii'))
            else:
                self.connections[self.clients[client]] = message[2:]

                client.send((self.VERSION_NUMBER + self.commands['START_CHAT'] + 'You are now connected to ' + message[2:] + '! You may now begin chatting. To exit, type "/E"').encode('ascii'))

                out = ''
                if self.clients[client] in self.queue:
                    if message[2:] in self.queue[self.clients[client]]:
                        for m in self.queue[self.clients[client]][message[2:]]:
                            out += self.colors.OKBLUE + message[2:] + ': ' + self.colors.ENDC + m + '\n'

                        self.queue[self.clients[client]][message[2:]] = []

                client.send((self.VERSION_NUMBER + self.commands['SHOW_TEXT'] + out).encode('ascii'))


    def check_unread_messages(self, client):
        user = self.clients[client]
        out = ""
        for key, val in self.queue[user].items():
            out += 'You have unread messages from: ' + str(key) + '\n'
        return out


    # conditional logic for disconnecting from another user. Updates connections accordingly. Prompts user for new connection.
    def exit(self, client, message):
        # connections.pop(clients[client])
        self.connections[self.clients[client]] = ''
        return (self.VERSION_NUMBER + self.commands['DISPLAY'] + 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)').encode('ascii')


    def handle(self, client):
        while True:

            # for debugging purposes
            print('*'*80)
            print('clients:', self.clients)
            print('users:', self.USERNAMES)
            print('connections:', self.connections)
            print('queue:', self.queue)

            try:
                message = client.recv(1024).decode()
                self.messages.append(message)
                # print("size of transfer buffer: " + str(sys.getsizeof(message)))
                if message[1] == self.commands['CONNECT']:
                    self.connect(client, message)
                elif message[1] == self.commands['TEXT']:
                    self.text(client, message)
                elif message[1] == self.commands['SHOW']:
                    client.send(self.show(client, message))
                elif message[1] == self.commands['HELP']:
                    self.help(client, message)
                elif message[1] == self.commands['DELETE']:
                    client.send(self.delete_account(client, message))
                elif message[1] == self.commands['EXIT_CHAT']:
                    client.send(self.exit(client, message))
                else:
                    self.prompt(client, message)


            except:
                self.LOGGED_IN.remove(self.clients[client])
                if client in self.connections:
                    self.connections.pop(client)
                self.clients.pop(client)
                self.client.close()
                break


    def receive(self):
        while True:
            client, address = self.server.accept()
            self.clients[client] = ''
            error_message = ''
            username = ''
            print("Connected with {}".format(str(address)))
            while True:
                client.send((self.VERSION_NUMBER + self.commands['ENTER'] + error_message).encode('ascii'))
                username = client.recv(1024).decode('ascii')
                error_message = self.login_username(username, client)
                if error_message == '':
                    break

            print("Username is {}".format(username[2:]))
            client.send((self.VERSION_NUMBER + self.commands['DISPLAY'] + \
                'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)\n' + self.check_unread_messages(client)).encode('ascii'))

            thread = threading.Thread(target=self.handle, args=(client,))
            thread.start()
