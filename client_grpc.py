import socket, threading
import logging
import time
import random
import grpc
import messaging_pb2
import messaging_pb2_grpc



username = ""

# change color of terminal text
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


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client.connect(('10.250.185.78', 7976))
client.connect(('127.0.0.1', 7976))

# pretty much same as Wednesday, removed the redundant connection at the beginning which asks for login/create account.
def login_message():
    global username
    choice = None
    while choice != "L" and choice != "C":
        choice = input("Log in (L) or create an account (C): ")
    if choice == "L":
        username = input("Enter username: ")
        return VERSION_NUMBER + commands['LOGIN_NAME'] + username
    else:
        username = input("Create new username: ")
        return VERSION_NUMBER + commands['CREATE_NAME'] + username


# parse user's input text. Specifically deal with commands beginning with '/'
def parse_arg(input):
    if not input:
        return VERSION_NUMBER + commands['NOTHING'] + ''

    command = 'TEXT'
    if input[0] == '/':
        if input[1:3] == 'C' or input[1:3] == 'C ':
            command = 'CONNECT'
        if input[1:3] == 'H':
            command = 'HELP'
        if input[1:3] == 'S':
            command = 'SHOW'
        if input[1:3] == 'D':
            command = 'DELETE'

    if command == 'TEXT':
        return send_text(input)
    # if the command is not CONNECT, just send whole payload
    elif command != 'CONNECT':
        return VERSION_NUMBER + commands[command] + ''
    # if the command is CONNECT, send only the part of the payload which specifies which user we are connecting to
    else:
        return VERSION_NUMBER + commands[command] + input[3:]

# send_text command only used when user is engaged in a chatroom. In this case, '/E' triggers chatroom exit.
def send_text(input):
    if input == '/E':
        return VERSION_NUMBER + commands['EXIT_CHAT'] + 'end'
    return VERSION_NUMBER + commands['TEXT'] + input


# new read function for gRPC client. Once successfully logged in, continuously sends requests for any new messages
def read(client_id):
    metadata = [('client-id', client_id)]
    while True:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = messaging_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(messaging_pb2.HelloRequest(details=str(VERSION_NUMBER + commands['REQUEST'] + '')), metadata=metadata)
            # exit if account deleted
            if response.message[2:] == 'Account deleted': return
            # print messaage if one is sent back
            elif response.message[2:]: print(response.message[2:])


logged_in = False
# main function
def run():
    global logged_in
    # create a client id out of the current time and a random string. If a session is started, it will keep the same client id until termination
    client_id = str(time.time()) + str(random.random())
    # send metatdata with HelloRequest
    metadata = [('client-id', client_id)]

    # try logging in
    while not logged_in:
        username = login_message()
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = messaging_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(messaging_pb2.HelloRequest(details=str(username)), metadata=metadata)
            if response.message[1] == commands["DISPLAY"]:
                logged_in = True
            print(response.message[2:])

    inp = input(":")
    m = parse_arg(inp)

    # start the read thread to request new messages
    read_thread = threading.Thread(target=read, args=(client_id,))
    read_thread.start()

    while True:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = messaging_pb2_grpc.GreeterStub(channel)
            response = stub.SayHello(messaging_pb2.HelloRequest(details=str(m)), metadata=metadata)
            if response.message[1] == commands["DISPLAY"]:
                print(response.message[2:])
            elif response.message[1] == commands['SHOW_TEXT']:
                if response.message[2:]: print(response.message[2:])
            elif response.message[1] == commands['DELETE']:
                if response.message[2:]: print(response.message[2:])
                # exit if account deleted
                return
            elif response.message[1] == commands['START_CHAT']:
                if response.message[2:]: print(response.message[2:])

            # poll for new input at the end of each response from server
            inp = input(":")
            m = parse_arg(inp)


logging.basicConfig()
run()
