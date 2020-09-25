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
# everything saved in the write_buffer to the socket and clear the write buffer.
# Similarly, when reading from a socket in select(), the data should be stored in read_buffer and then processed.
# You do not need to add any code to this class, though you may if you want to. You must NOT REMOVE OR RENAME any 
# of the code or properties currently defined in this class.
class ConnectionData(object):
    def __init__(self):
        self.read_buffer = ""
        self.write_buffer = ""



# ServerData extends ConnectionData with properties specific to a connection with a server. As ServerData extends 
# ConnectionData, it also contains read_buffer and write_buffer properties. You will create and save an instance of
# ServerData who you receive a SERVER connection message and refer back to it when you need to communicate
# with that server. 
# You do not need to add any code to this class, though you may if you want to. You must NOT REMOVE OR RENAME any 
# of the code or properties currently defined in this class.
class ServerData(ConnectionData):

    def __init__(self):
        super(ServerData, self).__init__()
        self.servername = None  # The name of the server
        self.hopcount = None    # The number of hops this server is away from the server who created this instance of ServerData
        self.info = None        # A human-readable description of the server

        self.first_link = None  # The name of the server on the first link towards this server. This is a VERY important
                                # field, as you will use it to broadcast messages throughout the network.
                                # Assume a network structured as shown to the right:         ------A---
                                # Each server shown here contains a ServerData for           |        |
                                # each other server in the network.                          C--B     D--E
                                # Consider the different ServerData objects owned by D                |
                                # Its instance of ServerData for C contains A as the first link       F
                                # as, in order to send a message to C, D must first send that
                                # message to A, who will forward it on to C. Thus, when D needs to send
                                # a message to C, to can refer to the first_link property to determine
                                # what neighboring server to send the message to in order to eventually reach C
                                # Similarly, if D receives a message from F addressed to C, it can refer to the
                                # first_link property to determine how to get to C.
                                #
                                # Here are the first link properties for each machine, from D's perspective
                                # Machine - First Link
                                # A - A
                                # B - A
                                # C - A
                                # E - E                              
                                # F - F                                                               


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
        self.first_link = None  # First link has the same properties for UserData as it does for ServerData



class CRCServer(object):

    # Initialization method 
    def __init__(self, options, run_on_localhost=False):

        # DO NOT EDIT ANYTHING BELOW THIS LINE IN __init__
        # -----------------------------------------------------------------------------

        # Use this selector object for the assignment.
        self.sel = selectors.DefaultSelector()

        # Use this MessageParser object for assignment 2
        self.parser = MessageParser()


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


        # Store the servers who are directly connected to this server
        # The list should contain the names of the servers
        self.adjacent_servers = []
        
        # Store all information about servers in this variable
        # The key should be the servername, and the variable a ServerData object
        self.servers_lookuptable = {}

        # Store the users who are directly connected to this server
        # The list should contain the nick of the users
        self.adjacent_users = []

        # Store all information about users in this variable
        # The key should be the user's nick, and the variable a UserData object
        self.users_lookuptable = {}


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
        self.listen_for_messages()
        


    # This function is responsible for setting up the server socket and registering it with your selector
    # TODO: Create a TCP server socket and bind to self.port (defined in __init__).
    #       Begin listening for incoming connections and register the socket with your selector
    # HINT: Server sockets are read from, but never written to. This is important when registering the socket
    #       with your selector
    # HINT: Later on, you will need to differentiate between the server socket (which accepts new connections)
    #       and sockets serving connections with other servers and clients. Select won't tell you which is which,
    #       it just tells you that a socket is ready for processing. When registering the server socket, you can
    #       use the data parameter to make this possible
    def setup_server_socket(self):
        tcpServer = socket(AF_INET,SOCK_STREAM)
        tcpServer.bind(('',self.port))

        tcpServer.listen(5)
        tcpServer.setblocking(False)

        events_mask = selectors.EVENT_READ
        data = ServerData()
        data.servername = "SERVER_SOCKET"

        self.sel.register(tcpServer,events_mask,data)


    # This function is responsible for connecting to a remote CRC server upon starting this server
    # The details of the server to connect to are set in self.connect_to_host_addr and self.connect_to_port
    # TODO: Establish a connection with the remote server, register the new socket with your selector,
    #       and send a SERVER registration message to the server you've connected to.
    #       The SERVER registration message should be of the format:
    #       SERVER [servername] [hopcount=1] :[info]\r\n
    # HINT: This socket will need to be both read from and written to
    def connect_to_server(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((self.connect_to_host_addr,self.connect_to_port))
        sock.setblocking(False)


        events_mask = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = ServerData()
        data.servername = self.servername
        data.hopcount = 1
        data.info = self.info

        self.sel.register(sock,events_mask,data)

        reg_msg = "SERVER " + data.servername + " " + str(data.hopcount) + " :" + data.info + "\r\n"
        sock.send(reg_msg.encode())



    # This is the main loop responsible for processing input and output on all sockets this server
    # is connected to. You should manage these connections using the selector self.sel.
    # TODO: Inside of the while not self.request_terminate loop, get a list of all sockets ready for processing
    #       from your selector, and then process these events. If the socket being processed is the server socket,
    #       call self.accept_new_connection. Otherwise, call self.service_socket.
    #       Once the while loop has terminate (i.e. the program is shutting down), call self.cleanup()
    # HINT: Pass a short timeout value into your select() call (e.g. 1 second) to prevent your code from hanging
    #       when it is time to terminate it
    def listen_for_messages(self):
        self.print_info("Listening for new connections on port " + str(self.port))
        
        # All calls to select() MUST be inside of this loop. Select is a blocking call, and we need to terminate the 
        # server in order to test its functionality. We will accomplish this by calling select() inside of a loop that
        # we can terminate by setting self.request_terminate to True.
        while not self.request_terminate:
            # TODO: Implement the above described code within this loop
            events = self.sel.select(timeout = 1)
            for key, mask in events:
                    sock = key.fileobj
                    data = key.data
                    if hasattr(data, 'servername') and data.servername == "SERVER_SOCKET":
                        self.accept_new_connection(key)
                    else:
                        self.service_socket(key,mask)

        self.cleanup()



    # On shutting down the server, we need to release allocated resources associated with the server socket, with all
    # other sockets we've opened, and with our selector. Use this function to accomplish this
    # TODO: Perform any cleanup required upon termination of the program. This includes both sockets and your selector 
    def cleanup(self):
        select_keys = list(self.sel._fd_to_key.values())
        for key in select_keys:
            key.fileobj.close()
            self.sel.unregister(key.fileobj)





    # This function is responsible for handling new connection requests from other servers and from clients.
    # NOTE: At this point we don't yet know if the entity who sent this connection request is a server or a client
    #       We won't find this out until we receive either a SERVER or a USER registration message
    # TODO: Accept the connection request and register it with your selector. You should configure all sockets
    #       for both READ and WRITE events. You will also need to create an instance of ConnectionData() and assign it
    #       to the data field when registering the connection. ConnectionData is a class created for this assignment.
    #       See the comments at the top of this file for more details. ConnectionData holds our read and write buffers
    #       associated with this socket
    def accept_new_connection(self, select_key):
        sock = select_key.fileobj
        conn, addr = sock.accept()

        events_mask  = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = ConnectionData()

        self.sel.register(conn,events_mask,data)





    # This function is responsible for receiving CRC messages received from connected servers and clients. 
    # TODO: Check to see if this is a READ event and/or a WRITE event (it is possible for it to be both).
    #       If it is a read event, read the data from the connection and process it. If you call recv but
    #       don't receive any data, this means that the client/server has closed their connection from
    #       the other side. In this case, you should unregister and close the socket.
    #       On receiving data, call self.handle_messages and pass in that data
    #       If it is a write event, make sure you actually have data to write before writing to the socket.
    #       You don't want to write empty data to your socket
    def service_socket(self, select_key, mask):
        sock = select_key.fileobj

        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(2048)
            if recv_data == "":
                self.sel.unregister(sock)
                sock.close()
            else:
                self.handle_messages(select_key,recv_data)


        if mask & selectors.EVENT_WRITE:
            write_data = select_key.data.write_buffer
            if write_data != "":
                sock.send(write_data.encode())



    # Call this function from server_socket whenever a message is received from a previously connected
    # client or server and pass in the content of that message. This will get passed to your message parser
    # and sent on to the appropriate message handler function.
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
    # in the command handlers, and instead call these functions. This will help with debugging later

    # This function should implement the functionality used to send a message to another server.
    # You CANNOT call send() in this function, or in a function directly called by this function.
    # Remember that send() must be called when handling a selector event with the WRITE mask set to true
    # Otherwise your code may block and cause your program to hang
    # TODO: Write the code required when the server has a message to be sent to another server
    def send_message_to_server(self, name_of_server_to_send_to, message):
        sock = socket(AF_INET,SOCK_STREAM)
        sock.sendto(message,name_of_server_to_send_to)


    # When responding to an error, you may not yet know the name of client/server when sent the message
    # (E.g. when the initial registration command fails.) In this case, you will need to send the message
    # back using the select_key that was passed into your message handler. The functionality of this code
    # will be very similar to your send_message_to_server() function, but it will only be called
    # if you don't know the name of the server/client the message is directed to
    # TODO: Write the code required when the server has a message to be sent through a select_key
    def send_message_to_select_key(self, select_key, message):
        pass


    # This function should implement the functionality used to send a message to a client. This function
    # will be slightly different from send_message_to_server(), as messages addressed to clients are first
    # forwarded to servers, and then sent to the user upon arriving at the server the user is registered to.
    # You CANNOT call send() in this function, or in a function directly called by this function.
    # Remember that send() must be called when handling a selector event with the WRITE mask set to true
    # Otherwise your code may block and cause your program to hang
    # TODO: Write the code required when the server has a message to be sent to a client
    def send_message_to_client(self, name_of_client_to_send_to, message):
        pass


    # Messages will sometimes need to be sent to every server in the IRC network. This is a helper function
    # to make that process easier. You may call send_message_to_server() in this function. Make sure you only
    # send the message to servers that are ADJACENT to this server. 
    # You will sometimes want to exclude a server from receiving this message, such as when forwarding a message 
    # received from another server. In this case, you can't forward this message back to that server or the message 
    # will never die. This is the purpose of the ignore_server parameter. You must NOT broadcast a message
    # to the server included in that parameter, if it is present (it defaults to None).
    # TODO: Write the code required to broadcast to all adjacent servers, except for a server included in the
    #       ignore_server parameter
    def broadcast_message_to_servers(self, message, ignore_server=None):
        pass



    ######################################################################
    # The remaining functions are command handlers. Each command handler is documented with the functionality that 
    # must be supported. Each command handler expects to receive 4 parameters: 
    # * select_key: select_key contains the key value returned by select() for a specific connection. This contains
    #               the socket and the data associated with the socket upon registration with select
    # * prefix:     the prefix of the message to be processed. This should be None if no prefix was present
    # * command:    the command to be processed
    # * params:     a list of the parameters associated with the command. This should be None if no params were present
    
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
        pass




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
        pass



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
        pass

    
    

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