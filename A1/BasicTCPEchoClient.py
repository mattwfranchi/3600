from socket import *

# Define variables that hold the desired server name, port, and buffer size
SERVER_NAME = 'newton.computing.clemson.edu'
SERVER_PORT = 3611
BUFFER_SIZE = 32

# We are creating a *TCP* socket here. We know this is a TCP socket because of
# the use of SOCK_STREAM
# It is being created using a with statement, which ensures that the socket will
# be cleaned up correctly when the socket is no longer needed (once the with block has been exited)
with socket(AF_INET, SOCK_STREAM) as s:
    # Connect to a server at the specified port using this socket
    s.connect((SERVER_NAME, SERVER_PORT))
    
    # Loop forever...
    while True:
        # Read in an input statement from the user
        message = input('Input: ')
        # Send the message the user wrote into the socket
        s.send(message.encode())
        # Wait to receive a response from the server, up to 128 bytes in length
        response =  s.recv(BUFFER_SIZE)
        # Print that response to the console
        print(response.decode())