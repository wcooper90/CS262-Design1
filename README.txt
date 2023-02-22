
README

Welcome to our messaging system.

Server device:

1) Turn off firewall

(Mac OS: System Preferences --> Security & Privacy --> Firewall --> Turn Firewall Off)

Run python server.py or 'python server_grpc.py'

2) add printed IP address to client code

Client:

Run 'python client.py' or 'python client_grpc.py'


Commands:
/S will show list of users, and number of unread messages from each one, use [key]* to search for all users with usernames beginning with the key
/C [username] will allow you to connect to user
/H will give the list of possible commands
/D allows you to delete your account
/E allows you to exit if you are in an active chat
