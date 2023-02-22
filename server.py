import socket, threading

host = '0.0.0.0'
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
            'START_CHAT': 'f'}

hostname=socket.gethostname()
IPAddr=socket.gethostbyname(hostname)
print("Your Computer Name is:"+hostname)
print("Your Computer IP Address is:"+IPAddr)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)              #socket initialization
server.bind((host, port))                                               #binding host and port to socket
server.listen()

queue = {}
USERNAMES = []
connections = {}
clients = {}
LOGGED_IN = set([])

# deletes a username from list of usernames, removes the association from the client, and sends the appropriate message
# TODO: eventually will also have to delete undelivered messages to a deleted account
def delete_account(client, message):
    out = 'Account deleted'
    LOGGED_IN.remove(clients[client])
    USERNAMES.remove(clients[client])
    queue.pop(clients[client])
    clients[client] = ''
    return (VERSION_NUMBER + commands['DELETE'] + out).encode('ascii')

    # client.send((VERSION_NUMBER + commands['DELETE'] + out).encode('ascii'))


# displays the other users on the current server.
def show(client, message):

    all_users = []

    if message[4:]:
        if '*' in message[4:]:
            key = message[4:message.index('*')]
            for user in USERNAMES:
                if key in user:
                    all_users.append(user)

        elif message[4:] in USERNAMES:
            all_users.append(message[4:])
        else:
            return (VERSION_NUMBER + commands['DISPLAY'] + "No users match").encode('ascii')
    else:
        all_users = USERNAMES


    out = ""
    for user in all_users:

        # Display number of unread messages from other users
        number_unread = 0
        if clients[client] in queue:
            if user in queue[clients[client]]:
                number_unread = len(queue[clients[client]][user])

        if number_unread > 0: out += user + ' ('+str(number_unread)+' unread messages)' + '\n'
        else: out += user + '\n'

    # I'm just using the "DISPLAY" command to display specific messages and prompt the user for another response at this point.
    return (VERSION_NUMBER + commands['DISPLAY'] + out).encode('ascii')

# displays the list of possible commands.
def help(client, message):
    out = 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)'
    client.send((VERSION_NUMBER + commands['DISPLAY'] + out).encode('ascii'))

# prompts the user for another input (only used when the user just presses 'enter' without typing anything)
def prompt(client, message):
    client.send((VERSION_NUMBER + commands['DISPLAY'] + '').encode('ascii'))


# conditional logic for logging in / creating an account. Updates USERNAMES and clients global data as necessary.
def login_username(username, client):
    error_message = ''
    if username[1] == commands['LOGIN_NAME']:
        if username[2:] not in USERNAMES:
            error_message = 'Username not found'
        elif username[2:] in LOGGED_IN:
            error_message = 'User currently logged in!'
        else:
            clients[client] = username[2:]
            connections[username[2:]] = ''
            LOGGED_IN.add(username[2:])

    if username[1] == commands['CREATE_NAME']:
        if username[2:] in USERNAMES:
            error_message = 'Username taken'
        elif ' ' in username[2:]:
            error_message = "Your username can not have spaces"
        elif '*' in username[2:]:
            error_message = "You username can not have '*'"
        else:
            USERNAMES.append(username[2:])
            clients[client] = username[2:]
            connections[username[2:]] = ''
            queue[username[2:]] = {}
            LOGGED_IN.add(username[2:])
    return error_message


# called whenever user submits a "non-command". Needs to be updated when actually connecting users,
# Also storing a client object as a dictionary key might be a bit weird, haven't totally figured it out yet.
def text(client, message):

    sender = client # client code

    receiver = connections[clients[client]] # username

    if not receiver:
        client.send((VERSION_NUMBER + commands['DISPLAY'] + 'You currently are not connected to anyone. Type /H for help.  ').encode('ascii'))
        return

    receiver_address = ''
    for key, val in clients.items():
        if val == receiver:
            receiver_address = key
            break

    if (receiver in connections) and (connections[receiver] == clients[sender]): # comparing usernames
            receiver_address.send((VERSION_NUMBER + commands['SHOW_TEXT'] + bcolors.OKBLUE + clients[client] + ': ' + bcolors.ENDC+ message[2:]).encode('ascii'))

    else:
        # Tell client that reciever is not in chat anymore, but sent messages will be saved for htem
        # store the messages
        if receiver in queue:
            if clients[sender] in queue[receiver]:
                queue[receiver][clients[sender]].append(message[2:])
            else: queue[receiver][clients[sender]] = [message[2:]]
        else:
            queue[receiver] = {clients[sender]:[message[2:]]}

        client.send((VERSION_NUMBER + commands['SHOW_TEXT'] + 'The recipient has disconnected. Your chats will be saved. ').encode('ascii'))



    # if client in connections and connections[client]:
    #     client.send((VERSION_NUMBER + commands['TEXT'] + '').encode('ascii'))

# conditional logic for connecting to another user. Updates connections accordingly.
def connect(client, message):
    if message[2:] not in USERNAMES:
        print(message[2:])
        client.send((VERSION_NUMBER + commands['DISPLAY'] + 'user not found. Please try again').encode('ascii'))
    else:
        # do not allow user to connect to oneself.
        if clients[client] == message[2:]:
            client.send((VERSION_NUMBER + commands['DISPLAY'] + 'You cannot connect to yourself! Please try again ').encode('ascii'))
        else:
            connections[clients[client]] = message[2:]

            client.send((VERSION_NUMBER + commands['START_CHAT'] + 'You are now connected to ' + message[2:] + '! You may now begin chatting. To exit, type "/E"').encode('ascii'))

            out = ''
            if clients[client] in queue:
                if message[2:] in queue[clients[client]]:
                    for m in queue[clients[client]][message[2:]]:
                        out += bcolors.OKBLUE + message[2:] + ': ' + bcolors.ENDC + m + '\n'

                    queue[clients[client]][message[2:]] = []

            client.send((VERSION_NUMBER + commands['SHOW_TEXT'] + out).encode('ascii'))


def check_unread_messages(client):
    user = clients[client]
    out = ""
    for key, val in queue[user].items():
        out += 'You have unread messages from: ' + str(key) + '\n'
    return out


# conditional logic for disconnecting from another user. Updates connections accordingly. Prompts user for new connection.
def exit(client, message):
    # connections.pop(clients[client])
    connections[clients[client]] = ''
    return (VERSION_NUMBER + commands['DISPLAY'] + 'Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)').encode('ascii')


def handle(client):
    while True:

        # for debugging purposes
        print('*'*80)
        print('clients:', clients)
        print('users:', USERNAMES)
        print('connections:', connections)
        print('queue:', queue)

        try:
            message = client.recv(1024).decode()
            if message[1] == commands['CONNECT']:
                connect(client, message)
            elif message[1] == commands['TEXT']:
                text(client, message)
            elif message[1] == commands['SHOW']:
                client.send(show(client, message))
            elif message[1] == commands['HELP']:
                help(client, message)
            elif message[1] == commands['DELETE']:
                client.send(delete_account(client, message))
            elif message[1] == commands['EXIT_CHAT']:
                client.send(exit(client, message))
            else:
                prompt(client, message)


        except:
            LOGGED_IN.remove(clients[client])
            if client in connections:
                connections.pop(client)
            clients.pop(client)
            client.close()
            break


def receive():
    while True:
        client, address = server.accept()
        clients[client] = ''
        error_message = ''
        username = ''
        print("Connected with {}".format(str(address)))
        while True:
            client.send((VERSION_NUMBER + commands['ENTER'] + error_message).encode('ascii'))
            username = client.recv(1024).decode('ascii')
            error_message = login_username(username, client)
            if error_message == '':
                break

        print("Username is {}".format(username[2:]))
        client.send((VERSION_NUMBER + commands['DISPLAY'] + \
            'Logged in! Commands: /C [username] (connect with a user), /S (show list of other users), /H (help), /D (delete account and exit)\n' + check_unread_messages(client)).encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

receive()
