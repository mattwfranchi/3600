# MATT FRANCHI // CRC PART 3

from optparse import OptionParser
from socket import *
import os, sys
import selectors
import logging
import types
from MessageParser import MessageParser


# This class represents a generic connection. It contains a read_buffer and a write_buffer. When the server wants to
# send a message to the client, it should write the message to the write_buffer, and use \r\n as a message delimiter.
# Then, when select() determines the socket associated with ConnectionData is ready to be written, it should write
# the write_buffer to the socket and clear it.
# Similarly, when reading from a socket in select(), the data should be stored in read_buffer and then processed.
# You do not need to add any code to this class, though you may if you want to. You must NOT REMOVE OR RENAME any 
# of the code or properties currently defined in this class.
class ConnectionData(object):
    def __init__(self):
        self.read_buffer = ""
        self.write_buffer = ""        


# UserData extends ConnectionData with properties specific to a connection with a user. As UserData extends 
# ConnectionData, it also contains read_buffer and write_buffer properties. 
# You do not need to add any code to this class, though you may if you want to. You must NOT REMOVE OR RENAME any 
# of the code or properties currently defined in this class.
class UserData(ConnectionData):    
    def __init__(self):
        super(UserData, self).__init__()
        self.nick = None
        self.hostname = None
        self.servername = None
        self.realname = None
        self.first_link = None


# ServerData extends ConnectionData with properties specific to a connection with a server. As ServerData extends 
# ConnectionData, it also contains read_buffer and write_buffer properties. 
# You do not need to add any code to this class, though you may if you want to. You must NOT REMOVE OR RENAME any 
# of the code or properties currently defined in this class.
class ServerData(ConnectionData):

    def __init__(self):
        super(ServerData, self).__init__()
        self.servername = None  # The name of the server
        self.hopcount = None    # The number of hops this server is away from the server who created this instance
        self.info = None        # A human-readable description of the server

        self.first_link = None  # The name of the server on the first link towards this server. This is a VERY important
                                # field, as you will use it to broadcast messages throughout the network.
                                # Assume a network structured as shown to the right:            ---A---
                                # Each server shown hear contains a ServerData for           |     |
                                # each other server in the network. D's configuration        C--B     D--E
                                # puts the name for A in the first_link property for B                |
                                # and C, as to deliver a message to B or C, D must send               F
                                # the message to A, who then forwards it to B.
                                # D has the name of F in the first_link property for F,
                                # since D must send a message addressed to F along the link
                                # for F. To send a message to C, D must write the message into
                                # the write_buffer associated with A. D can determine this
                                # by checking to see that the first_link property for C is
                                # the name of A, and then look A up in the servers_lookuptree.


class CRCServer(object):

    # Initialization method
    def __init__(self, options, run_on_localhost=False):

        # Setup the selector we'll be using to handle multiple simultaneous connections
        self.sel = selectors.DefaultSelector()
        self.parser = MessageParser()

        # DO NOT EDIT ANYTHING BELOW THIS LINE IN __init__
        # -----------------------------------------------------------------------------

        # CRCServer accepts an "options" variable on construction, which is used to pass in
        # several important values from the test configuration file. This includes the 
        # server's name, the port the server socket should listen on, and a human-readable
        # description of the server (info)

        self.servername = options.servername
        self.port = options.port
        self.info = options.info

        # The next three variables store information about what machine this server should
        # attempt to connect to on initialization. Except for the very first CRCServer in a
        # network, all CRCServers connect to a pre-existing server on initialization. This
        # pre-existing server will be the new server's point of access into the wider network
    
        # The hostname of the server to connect to on startup (e.g. theshire.nz)
        self.connect_to_host = options.connect_to_host

        # The IP address of the server to connect to on startup.
        # IMPORTANT: You MUST use self.connect_to_host_addr when creating a TCP socket to
        #            connect to this machine. This value is set dynamically based on whether
        #            we are testing on localhost, or running in the wild on real servers
        self.connect_to_host_addr = options.connect_to_host
    
        # The port to connect to on the host server
        self.connect_to_port = options.connect_to_port

        # If this server is configured to run on localhost, then self.connect_to_host_addr
        # will be overwritten with the loopback address
        self.run_on_localhost=run_on_localhost
        if self.run_on_localhost:
            self.connect_to_host_addr = '127.0.0.1'


        # Store the users who are directly connected to this server
        # The list should contain the nick of the users
        self.adjacent_users = []

        # Store all information about users in this variable
        # The key should be the user's nick, and the variable a UserData object
        self.users_lookuptable = {}

        # Store the servers who are directly connected to this server
        # The list should contain the names of the servers
        self.adjacent_servers = []
        
        # Store all information about servers in this variable
        # The key should be the servername, and the variable a ServerData object
        self.servers_lookuptable = {}


        # Options to help with debugging and logging
        self.log_file = options.log_file
        self.logger = None
        self.init_logging()


        # THIS WILL BE SET TO TRUE BY CRCTestManager.py WHEN IT IS TIME TO TERMINATE THIS PROCESS
        # DO NOT CHANGE THIS VALUE IN YOUR CODE
        self.request_terminate = False


        # This dictionary contains mappings from commands to command handlers.
        # Upon receiving a command X, the appropriate command handler can be called with: self.message_handlers[X](...args)
        self.message_handlers = {
            # Connection Registration message handlers
            "USER":self.handle_user_message,
            "SERVER":self.handle_server_message,
            "QUIT":self.handle_quit_message,
        }

        # This dictionary maps human-readable reply/error messages to their numerical representations.
        # The numerical representation must be sent to clients, not the human-readable version. 
        # The full format for each reply/error message is included next to each command as a comment
        self.reply_codes = {
            "RPL_WELCOME": 1,           # :server_name ### :Welcome to the Internet Relay Network <nick>!<user>@<host>
            "ERR_NOSUCHNICK":401,       # :server_name ### <nick> :No such nick
            "ERR_NICKCOLLISION":436,    # :server_name ### <nick> :Nickname collision KILL from <user>@<host>
            "ERR_NEEDMOREPARAMS":461,   # :server_name ### <command> :Not enough parameters
        }



    # DO NOT EDIT THIS METHOD
    # Setup the server and start listening for incoming messages
    def run(self):
        self.print_info("Launching server %s..." % self.servername)
        # Set up the server socket that will listen for new connections
        self.setup_server_socket()

        # If we are supposed to connect to another server on startup, then do so now
        if self.connect_to_host and self.connect_to_port:
            self.connect_to_server()
        
        # Start listening for connections on the server socket
        self.listen_for_messages(self.servr_socket)
        


    # This function is responsible for setting up the server socket and registering it with your selector
    # TODO: Create a TCP server socket and bind to self.port (defined in __init__).
    #       Begin listening for incoming connections and register the socket with your selector
    # HINT: Server sockets are read from, but never written to. This is important when registering the socket
    #       with your selector
    # HINT: Later on, you will need to differentiate between the server socket (which accepts new connections)
    #       and sockets serving connections with other servers and clients. Select won't tell you which is which,
    #       it just tells you that a socket is ready for processing. When registering the server socket, you can
    #       use the data parameter to make this possible
    # Grading scheme: 5 points for this function
    # 1 pt = define TCP socket
    # 1 pt = bind to (('', self.port))
    # 1 pt = call listen()
    # 1 pt = set blocking to false
    # 1 pt = register the socket to the selector 
    def setup_server_socket(self):
        self.print_info("Configuring the server socket...")

        # Configure a server socket for each of the ports we're listening on
        self.servr_socket = socket(AF_INET, SOCK_STREAM)

        try:
            self.servr_socket.bind(('', self.port))
        except error as e:
            # Could not bind on port
            self.print_info("Could not bind on port " + str(self.port))
            return

        self.servr_socket.listen(10)
        
        # Configure this socket to not be blocking. We need this for it to work with your selector
        self.servr_socket.setblocking(False)

        # Register the socket with the selector. We're listening for read events, and not providing any initial data
        self.sel.register(self.servr_socket, selectors.EVENT_READ, data=None)
        


    # This function is responsible for connecting to a remote IRC server upon starting this server
    # The details of the server to connect to are set in self.connect_to_host_addr and self.connect_to_port
    # TODO: Establish a connection with the remote server, register the new socket with your selector,
    #       and send a SERVER registration message to the server you've connected to.
    #       The SERVER registration message should be of the format:
    #       SERVER [servername] [hopcount=1] :[info]
    #       e.g. "SERVER lothlorien.nz 1 :Home of the elves"
    # HINT: This socket will need to be both read from and written to
    # Grading scheme: 6 points for this function
    # 1 pt = define TCP socket
    # 1 pt = connect to ((self.connect_to_host_addr, self.connect_to_port))
    # 1 pt = set blocking to false
    # 1 pt = register the socket to the selector
    #        0.5 pt = registered with READ and WRITE events
    #        0.5 pt = registered with a ConnectionData (or ServerData) object 
    # 1 pt = create valid server registration message
    # 1 pt = add server registration message to write buffer
    def connect_to_server(self):
        self.print_info("Connecting to remote server %s:%i..." % (self.connect_to_host, self.connect_to_port))

        # Attempt to connect to another IRC server
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        try:
            # Connect to the host_addr, not the host. This lets us preserve the server name when running on localhost
            self.client_socket.connect((self.connect_to_host_addr, self.connect_to_port))
        except error as er:
            self.print_info("Could not connect to %s:%i " % (self.connect_to_host, self.connect_to_port))
            return

        # Configure this socket to not be blocking. We need this for it to work with selector
        self.client_socket.setblocking(False)

        # Register this as a standard Connection Data, even though we know this is a server. The server will 
        # respond with it's info, and this will get processed when we get a response message
        select_data = ConnectionData()
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(self.client_socket, events, select_data)

        # Send the registration message to the server
        reg_msg = "SERVER %s 1 :%s" % (self.servername, self.info)
        select_data.write_buffer += reg_msg + "\r\n"
          


    # This is the main loop responsible for processing input and output on all sockets this server
    # is connected to. You should manage these connections using a selector you have instantiated.
    # TODO: Inside of the while not self.request_terminate loop, get a list of all sockets ready for processing
    #       from your selector, and then process these events. If the socket being processed is the server socket,
    #       call self.accept_new_connection. Otherwise, call self.service_socket.
    #       Once the while loop has terminate (i.e. the program is shutting down), call self.cleanup()
    # HINT: Pass a short timeout value into your select() call (e.g. 1 second) to prevent your code from hanging
    #       when it is time to terminate it
    # Grading scheme: 4 points for this function
    # 1 pt = call select() on self.sel
    # 1 pt = loop over returned list from select()
    # 1 pt = correctly call self.accept_new_connection for server sockets
    # 1 pt = correctly call self.service_socket for client sockets
    def listen_for_messages(self, server_sockets):
        self.print_info("Listening for new connections on port " + str(self.port))
        # All calls to select() MUST be inside of this loop. Select is a blocking call, and we need to terminate the 
        # server in order to test its functionality. We will accomplish this by calling select() inside of a loop that
        # we can terminate by setting self.request_terminate to True.
        while not self.request_terminate:
            # TODO: Why do we need this check? This seems like it's being caused by a bug somewhere
            if len(self.sel._fd_to_key) > 0:
                events = self.sel.select(timeout=1)
                for keys, mask in events:
                    # If key.data is None, that means this connection came from a listening socket, which means we need
                    # to accept a new connection
                    if keys.data == None:
                        self.accept_new_connection(keys)
                    # Otherwise, this is a message containing data
                    else:
                        self.service_socket(keys, mask)

        self.cleanup()



    # On shutting down the server, we need to release allocated resources associated with the server socket, with all
    # other sockets we've opened, and with our selector. Use this function to accomplish this
    # TODO: Perform any cleanup required upon termination of the program. This includes both sockets and your selector 
    def cleanup(self):
        self.sel.close()
        self.servr_socket.close()



    # This function is responsible for handling new connection requests from other servers and from clients.
    # NOTE: At this point we don't yet know if the entity who sent this connection request is a server or a client
    #       We won't find this out until we receive either a SERVER or a USER registration message
    # TODO: Accept the connection request and register it with your selector. You should configure all sockets
    #       for both READ and WRITE events. You will also need to create an instance of ConnectionData() and assign it
    #       to the data field when registering the connection. ConnectionData is a class created for this assignment.
    #       See the comments at the bottom of this file for more details. ConnectionData holds our read and write buffers
    #       associated with this socket
    # Grading scheme: 4 points for this function
    # 1 pt = call accept() on the socket passed in to this function
    # 1 pt = set the newly created socket to non blocking
    # 1 pt = create a ConnectionData() object
    # 1 pt = register the new socket with the selector
    def accept_new_connection(self, select_key):
        connection, addr = select_key.fileobj.accept()
        connection.setblocking(False)
        # Assign a new instance of client data to this connection. Any data specific to this
        # connection will be stored here
        select_data = ConnectionData()
        select_data.sock = connection
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(connection, events, select_data)



    # This function is responsible for handling CRC messages received from connected servers and clients. 
    # TODO: Check to see if this is a READ event and/or a WRITE event (it is possible for it to be both).
    #       If it is a read event, read the data from the connection and process it. If you call recv but
    #       don't receive any data, this means that the client/server has closed their connection from
    #       the other side. In this case, you should unregister and close the socket.
    #       On receiving data, call self.handle_messages and pass in that data
    #       If it is a write event, make sure you actually have data to write before writing to the socket.
    #       You don't want to write empty data to your socket
    # Grading scheme: 6 points for this function
    # 1 pt = recv() data if a READ event has happened
    # 1 pt = pass data on to self.handle_messages()
    # 1 pt = close the socket if receiving a blank byte string in a READ event
    # 1 pt = send the write_buffer if a WRITE event has happened
    # 1 pt = check to make sure there is content in the write buffer before sending
    # 1 pt = clear the write buffer after sending
    def service_socket(self, select_key, mask):
        socket_to_service = select_key.fileobj

        # If the socket is ready for reading
        if mask & selectors.EVENT_READ:
            # Attempt to read data from the socket
            recv_info = socket_to_service.recv(2048) 
            # If we received data, process it
            if recv_info:
                self.handle_messages(select_key, recv_info)
            # If we did not receive data, that means the client closed their connection and we should clean up ours
            else:
                self.sel.unregister(socket_to_service)
                socket_to_service.close()

        # We need to use select to write data because it's possible for
        # the send() command to block, if the TCP receiver's recv buffer is full
        # This isn't necessarily a common occurance, but it can happen
        # If we can write, and we have data to write...
        if (mask & selectors.EVENT_WRITE):
            if select_key.data.write_buffer:
                socket_to_service.send(select_key.data.write_buffer.encode())
                select_key.data.write_buffer = ""


    # This is a function stub that will be completed in a future assignment
    def handle_messages(self, select_key, recv_data):
        messages = self.parser.parse_data(recv_data)

        for message in messages:
             # If we recognize the command, then process it using the assigned message handler
            if message["command"] in self.message_handlers:
                self.print_info("Received message \"%s\"" % (message))
                self.message_handlers[message["command"]](select_key, message["prefix"], message["command"], message["params"])
            else:
                raise Exception("Unrecognized command: " + message["command"])


    ######################################################################
    # This block of functions should handle all functionality realted to how
    # the server sends messages. Avoid directly sending messages or responses
    # in the command handlers, and instead call these functions

    # This function should implement the functionality used to send a message to another server.
    # You CANNOT call send() in this function, or in a function directly called by this function.
    # Remember that send() must be called when handling a selector event with the WRITE mask set to true
    # TODO: Write the code required when the server has a message to be sent to another server
    def send_message_to_server(self, name_of_server_to_send_to, message):
        # KEY: APPEND to write_buffer, dont' set
        self.servers_lookuptable[name_of_server_to_send_to].write_buffer += message



    # This function should implement the functionality used to send a message to a client. This function
    # will be slightly different from send_message_to_server(), as messages addressed to clients are first
    # forwarded to servers, and then sent to the user upon arriving at the server the user is registered to.
    # You CANNOT call send() in this function, or in a function directly called by this function.
    # Remember that send() must be called when handling a selector event with the WRITE mask set to true
    # TODO: Write the code required when the server has a message to be sent to a client
    def send_message_to_client(self, name_of_client_to_send_to, message):
        user = self.users_lookuptable[name_of_client_to_send_to]
        # adjacency test
        if str(message)[0] == ":":
            user.write_buffer += message
        else:
            adj_server = self.servers_lookuptable[user.first_link]
            adj_server.write_buffer += message

    # When responding to an error, you may not yet know the name of client/server when sent the message
    # (E.g. when the initial registration command fails.) In this case, you will need to send the message
    # back using the select_key that was passed into your message handler. The functionality of this code
    # will be very similar to your send_message_to_server() function, but it will only be called
    # if you don't know the name of the server/client the message is directed to
    # TODO: Write the code required when the server has a message to be sent through a select_key
    def send_message_to_select_key(self, select_key, message):
        select_key.data.write_buffer += message


    # Messages will sometimes need to be sent to every server in the IRC network. This is a helper function
    # to make that process easier. You may call send_message_to_server() in this function. Make sure you only
    # send the message to servers that are ADJACENT to this server. 
    # You will sometimes want to exclude a  server from receiving this message, such as when forwarding a message 
    # received from another server. In this case, you can't forward this message back to that server or the message 
    # will never die. This is the purpose of the ignore_server parameter. You must NOT broadcast a message
    # to the server included in that parameter, if it is present (it defaults to None).
    # TODO: Write the code required to broadcast to all adjacent servers, except for a server included in the
    #       ignore_server parameter
    def broadcast_message_to_servers(self, message, ignore_server=None):
        # skip if current server equals ignore_server
        for s in self.adjacent_servers:
            if s == ignore_server:
                continue
            self.send_message_to_server(s,message)




    # This is a helper function that should ingest the name of the numeric reply you want to send, and the message
    # associated with that numeric reply, and will return a fully formatted numeric reply. The format for all 
    # numeric replies is--> :<server_name> <numeric code> <message>
    def create_numeric_reply(self, reply_key, message):
        return ":" + self.servername + " " + str(reply_key) + " " + message




    ######################################################################
    # The remaining functions are command handlers. Each command handler is documented with the functionality that 
    # must be supported. Each command handler expects to receive 4 parameters: 
    # * select_key: select_key contains the key value returned by select() for a specific connection. This contains
    #               the socket and the data associated with the socket upon registration with select
    # * prefix:     the prefix of the message to be processed. This should be None if no prefix was present
    # * command:    the command to be processed
    # * params:     a list of the parameters associated with the command. This should be None if no params were present
    

    ######################################################################
    # User message
    # Command: USER
    # Parameters: 
    #   <nick>: the requested nickname for the new user (nicks may NOT start with '#')
    #   <hostname>: the name of the computer this user is connecting from
    #   <servername>: the name of the server this user is connecting to
    #   [<realname>]: the real name of the user
    # Examples: 
    #   USER samwise bagend theshire.irc.com :Samwise Gamgee                        # This is an initial registration command coming from a new client
    #   :rivendale.irc.com USER samwise bagend theshire.irc.com :Samwise Gamgee     # This is a notification from a server about a new client
    # Numeric replies:  
    #   ERR_NEEDMOREPARAMS: The message is missing parameters
    #   ERR_NICKCOLLISION: A user with this nick is already registered somewhere on the network
    #   RPL_WELCOME: The registration was successful
    # Notes: 
    # This function handles the initial registrion process for new users. The user must provide a unique
    # nick on registration. If this nick is not unique, the function must return a ERR_NICKCOLLISION message.
    # Upon receipt of a valid registration method, this function should create a new UserData object containing 
    # this user's details. This should be stored in the users_lookuptable, using the user's nick as the key associated
    # with this new value. Finally, the server should then notify the client that they have registered, using the RPL_WELCOME message,
    # and should broadcast their message to all other servers to inform them of the user's registration.
    #
    # Additionally, the server the user registers directly with also needs to replace the ConnectionData associated with this socket
    # that was created in accept_new_connection(). It should replace ConnectionData with the new UserData object.
    # The ConnectionData object can be replaced using the selector.modify command (see python docs for more detail). This allows us
    # to determine that the connection received over that socket is from a client, and to determine which client, for all future
    # messages received from that socket
    def handle_user_message(self, select_key, prefix, command, params):
        # ERROR: NEED MORE PARAMETERS CHECK
        if len(params) < 4:
            self.send_message_to_select_key(select_key,
                                            self.create_numeric_reply(self.reply_codes["ERR_NEEDMOREPARAMS"],"\r\n"))
            return

        # ERROR: NICKNAME COLLISION CHECK
        for u in self.users_lookuptable:
            U = self.users_lookuptable[u]
            if U.nick == params[0]:
                self.send_message_to_select_key(select_key,
                                                self.create_numeric_reply(self.reply_codes["ERR_NICKCOLLISION"],"\r\n"))
                return

        # Create new user data instance
        U = UserData()
        U.nick = params[0]
        U.hostname = params[1]
        U.servername = params[2]
        U.realname = params[3]

        # CASE: ADJACENT
        if prefix is None:
            U.first_link = U.servername

            self.sel.modify(select_key.fileobj,selectors.EVENT_READ | selectors.EVENT_WRITE, U)

            self.users_lookuptable[U.nick] = U
            self.adjacent_users.append(U.nick)

            welcome = self.create_numeric_reply(self.reply_codes["RPL_WELCOME"],"\r\n")
            self.send_message_to_client(U.nick,welcome)

            alert_message = ":" + self.servername + " USER " + U.nick + " " + U.hostname + " " + U.servername + " :" + \
                            U.realname + "\r\n"
            self.broadcast_message_to_servers(alert_message,U.servername)

        # CASE: NOT ADJACENT
        else:
            U.first_link = prefix

            self.users_lookuptable[U.nick] = U

            alert_message = ":" + self.servername + " USER " + U.nick + " " + U.hostname + " " + U.servername + " :" + \
                            U.realname + "\r\n"
            self.broadcast_message_to_servers(alert_message, prefix)





    ######################################################################
    # Server message
    # Command: SERVER
    # Parameters: 
    #   <servername>: the name of the new server
    #   <hopcount>: the number of hops required to reach this server
    #   [<info>]: human-readable name for the server
    # Examples: 
    #   SERVER rivendale.irc.edu 1 :The House of Elrond                     # This is an initial registration command coming from a new server
    #                                                                       # that should be connected to this server in the spanning tree
    #   :gondolin.irc.com SERVER rivendale.irc.edu 4 :The House of Elrond   # This is a notification from a known server about a new server
    #                                                                       # that has connected elsewhere into the spanning tree
    # Numeric replies:  
    #   ERR_NEEDMOREPARAMS: The message is missing parameters
    # Notes: 
    # This function handles the initial registrion process for new servers. The user must provide a unique servername
    # on registration. Upon receipt of a valid registration method, this function should create a new ServerData object containing 
    # this server's details. This should be stored in the servers_lookuptable, using the server's name as the key associated
    # with this new value. The server should then notify all other servers about this new server. 
    # 
    # Finally, the server should send the new server all known servers and users. This can be accomplished by sending 
    # SERVER and USER messages, and RPL_TOPIC/RPL_NOTOPIC and RPL_NAMEPLY messages, that inform the new server about every other
    # known server, user, and channel. Sending SERVER and USER messages will inform the new server about all servers and users 
    # using the normal registration code, and thus requires no additional development. You will need to complete the appropriate
    # RPL handlers for RPL_TOPIC, RPL_NOTOPIC, and RPL_NAMEPLY to enable the new server to register existing channel information.
    # These RPL handlers will only be used for this functionality.
    #
    # Additionally, the server the new server registers directly with also needs to replace the ConnectionData associated with this socket
    # that was created in accept_new_connection(). It should replace ConnectionData with the new ServerData object.
    # The ConnectionData object can be replaced using the selector.modify command (see python docs for more detail). This allows us
    # to determine that the connection received over that socket is from a server, and to determine which server, for all future
    # messages received from that socket
    def handle_server_message(self, select_key, prefix, command, params):
        if len(params) < 3:
            self.send_message_to_select_key(select_key,
                                            self.create_numeric_reply(self.reply_codes["ERR_NEEDMOREPARAMS"],None))
            return

        # CASE: NEW ADJACENT SERVER
        if prefix is None:
            A = ServerData()
            A.servername = params[0]
            A.hopcount = int(params[1])
            A.info = params[2]
            A.first_link = params[0]

            self.sel.modify(select_key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, A)

            self.adjacent_servers.append(A.servername)


            reg_msg = ":" + self.servername + " SERVER " + self.servername + " 1 :" + self.info + "\r\n"
            self.send_message_to_select_key(select_key, reg_msg)

            for s in self.servers_lookuptable:
                S = self.servers_lookuptable[s]
                reg_msg = ":" + self.servername + " SERVER " + S.servername + " " + str(S.hopcount) + " :" + S.info + "\r\n"
                self.send_message_to_select_key(select_key,reg_msg)

            for u in self.users_lookuptable:
                U = self.users_lookuptable[u]
                reg_msg = ":" + self.servername + " USER " + U.nick + " " + U.hostname + " " + U.servername \
                            + " :" + U.realname + "\r\n"
                self.send_message_to_select_key(select_key,reg_msg)

            self.servers_lookuptable[A.servername] = A

            # broadcast registration to other adjacent servers
            alert_message = ":" + self.servername + " SERVER " + A.servername + " " + str(A.hopcount + 1) + " :" \
                            + A.info + "\r\n"
            self.broadcast_message_to_servers(alert_message, A.servername)

        # CASE: NONADJACENT / RETURN FROM ADJACENT
        else:
            # RETURN FROM ADJACENT
            if prefix == params[0]:
                A = ServerData()
                A.servername = params[0]
                A.hopcount = params[1]
                A.info = params[2]
                A.first_link = params[0]

                self.sel.modify(select_key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, A)

                self.adjacent_servers.append(A.servername)
                self.servers_lookuptable[A.servername] = A

            # NONADJACENT
            else:
                select_key.data.first_link = prefix

                N = ServerData()
                N.servername = params[0]
                N.hopcount = int(params[1]) + 1
                N.info = params[2]
                N.first_link = prefix

                self.servers_lookuptable[N.servername] = N

                alert_message = ":" + self.servername + " SERVER " + params[0] + " " + str(int(params[1]) + 1) + " :" + params[
                    2] + "\r\n"
                self.broadcast_message_to_servers(alert_message, prefix)




    ######################################################################
    # Quit message
    # Command: QUIT
    # Parameters: 
    #   {[<Goodbye message>]}: an optional message from the user who has quit. If no message is provided,  
    #                     use the default message: <nick> has quit  
    # Examples: 
    #   QUIT :shot with an arrow in the chest               # A message from a user who is quitting the server
    #   :boromir QUIT :shot with an arrow in the chest      # A message from another server about a user who has quit. The user's 
    #                                                       # nick is included in the prefix of the message
    # Numeric replies: 
    #   None
    # Notes: 
    # This function should be called when a user quits the IRC network. All information of this user should be removed from
    # users_lookuptable and adjacent_users, as well as any channels the user had joined. The Quit message must then be broadcast
    # to all servers. If the user appended an optional Goodbye message then it should be sent to all users in the channels
    # the user had joined.
    def handle_quit_message(self, select_key, prefix, command, params):
        if prefix:
            username = prefix
        else:
            username = select_key.data.nick


        message = ":"+username+ " QUIT :"

        # CASE: OPTIONAL MESSAGE INCLUDED
        if params:
            message += params[0] + "\r\n"
        # CASE: USE DEFAULT MESSAGE
        else:
            message += username + " has quit \r\n"

        self.users_lookuptable.pop(username)
        # ONLY REMOVE FROM ADJ USERS IF PRESENT
        if username in self.adjacent_users:
            self.adjacent_users.remove(username)

        self.broadcast_message_to_servers(message,select_key.data.servername)



    
    

    # DO NOT EDIT ANY OF THE FUNCTIONS INCLUDED IN IRCServer BELOW THIS LINE
    # These are helper functions to assist with logging, and list management
    # ----------------------------------------------------------------------


    ######################################################################
    # This block of functions enables logging of info, debug, and error messages
    # Do not edit these functions. init_logging() is already called by the template code
    # You are encouraged to use print_info, print_debug, and print_error to log
    # messages useful to you in development

    def init_logging(self):
        # If we don't include a log file name, then don't log
        if not self.log_file:
            return

        # Get a reference to the logger for this program
        self.logger = logging.getLogger("IRCServer")
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

        # Create a file handler to store the log files
        fh = logging.FileHandler(os.path.join(__location__, 'Logs', '%s' % self.log_file), mode='w')

        # Set up the logging level. It defaults to INFO
        log_level = logging.INFO
        
        # Define a formatter that will be used to format each line in the log
        formatter = logging.Formatter(
            ("%(asctime)s - %(name)s[%(process)d] - "
             "%(levelname)s - %(message)s"))

        # Assign all of the necessary parameters
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        self.logger.setLevel(log_level)
        self.logger.addHandler(fh)

    def print_info(self, msg):
        print("[%s] \t%s" % (self.servername,msg))
        if self.logger:
            self.logger.info(msg)



    # This function takes two lists and returns the union of the lists. If an object appears in both lists,
    # it will only be in the returned union once.
    def union(self, lst1, lst2): 
        final_list = list(set(lst1) | set(lst2)) 
        return final_list

    # This function takes two lists and returns the intersection of the lists.
    def intersect(self, lst1, lst2): 
        final_list = list(set(lst1) & set(lst2)) 
        return final_list

    # This function takes two lists and returns the objects that are present in list1 but are NOT
    # present in list2. This function is NOT commutative
    def diff(self, list1, list2):
        return (list(set(list1) - set(list2)))