from optparse import OptionParser
from socket import *
import os, sys, threading
import selectors
import logging
import types


class CRCClient(object):
    
    def __init__(self, options, run_on_localhost=False):
        self.request_terminate = False

        self.serveraddr = options.serverhost
        self.serverport = options.serverport

        if run_on_localhost:
            self.serveraddr = "127.0.0.1"

        self.nick = options.nick
        self.hostname = options.hostname
        self.servername = options.serverhost
        self.realname = options.realname
        
        # Options to help with debugging and logging
        self.log_file = options.log_file
        self.logger = None

        self.init_logging()

    def run(self):
        self.print_info("Launching client %s@%s..." % (self.nick, self.hostname))
        self.connect_to_server()

        # Send the registration message to the server
        self.send_message_to_server("USER %s %s %s :%s" % (self.nick, self.hostname, self.servername, self.realname))

        # Wait for a response from the server telling us if we registered, or if there was a problem
        rsp = self.sock.recv(2048).decode().replace("\r\n", "\\r\\n")
        self.print_info("Received registration message: " + rsp)
        

    def start_listening_to_server(self):
        x = threading.Thread(target=self.listen_for_server_input)
        x.start()        


    ######################################################################
    # This function should create a socket and connect to the server this client is directly linked to
    def connect_to_server(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((self.serveraddr, int(self.serverport)))


    def listen_for_server_input(self):
        while not self.request_terminate:
            rcvd = self.sock.recv(2048).decode()
            if not rcvd:
                self.print_info("Server has disconnected!")
                self.request_terminate = True


    ######################################################################
    # This block of functions ...
    def send_message_to_server(self, message):
        self.sock.send(message.encode())



    ######################################################################
    # The remaining functions are command handlers. Each command handler is documented
    # with the functionality that must be supported
    
    ######################################################################
    # Quit message
    # Command: QUIT
    # Parameters: 
    #   {[<Quit message>]}: an optional message from the user who has quit. If no message is provided,  
    #                     use the default message: <nick> has quit  
    # Examples: 
    #   QUIT                                        # A message without a quit message
    #   QUIT :shot with an arrow in the chest       # A message with a quit message
    # Expected numeric replies: 
    #   None
    def quit(self, quit_message=None):
        msg = "QUIT"
        if quit_message:
            msg += " :%s" % quit_message
        self.send_message_to_server(msg)

    

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
        print("[%s] \t%s" % (self.nick,msg))
        if self.logger:
            self.logger.info(msg)