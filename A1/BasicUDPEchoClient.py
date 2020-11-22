from socket import *

# Define variables that hold the desired server name, port, and buffer size
SERVER_NAME = 'localhost'
SERVER_PORT = 3601
BUFFER_SIZE = 32

# We are creating a *UDP* socket here. We know this is a UDP socket because of
# the use of SOCK_DGRAM
# It is being created using a with statement, which ensures that the socket will
# be cleaned up correctly when the socket is no longer needed (once the with block has been exited)
with socket(AF_INET, SOCK_DGRAM) as s:

    # Loop forever
    while True:
        # Read in an input statement from the user
        message = input('Input: ')
        # Send the message the user wrote into the socket
        s.sendto(message.encode(), (SERVER_NAME, SERVER_PORT))
        # Wait to receive a response from the server
        response, serverAddr =  s.recvfrom(BUFFER_SIZE)
        # Print that response to the console
        print(response.decode())