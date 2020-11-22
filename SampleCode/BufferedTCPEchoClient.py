from socket import *
from struct import pack, unpack

# Define variables that hold the desired server name, port, and buffer size
SERVER_NAME = 'localhost'
SERVER_PORT = 3604
BUFFER_SIZE = 32

class BufferedTCPEchoClient(object):
    def __init__(self, server_name, server_port):
        # We are creating a *TCP* socket here. We know this is a TCP socket because of
        # the use of SOCK_STREAM
        self.sock = socket(AF_INET, SOCK_STREAM)
        # Connect to a server at the specified port using this socket
        self.sock.connect((server_name, server_port))


    def start(self):
        while True:
            # Read in an input statement from the user
            message = input('Input: ')
            
            # Send the message to the server
            self.send_message(message)

            # Wait for a response from the server
            response = self.receive_message()
            if response:
                print(response)
            else:
                print("Server disconnected...")
                break

        print("Closing socket...")
        self.sock.close()


    def send_message(self, message):
        message_length = len(message)
        data = pack("!B" + str(message_length) + "s", message_length, message.encode()) 
        self.sock.send(data)

            
    def receive_message(self):
        # Get the first part of the message, this includes the header and the start of the string
        first_part = self.sock.recv(BUFFER_SIZE)

        if first_part:
            # First, strip out the header
            message_length = unpack("!B", first_part[:1])[0]
            print("..New message size: " + str(message_length))
            print("..Received '" + first_part[1:].decode() + "'")

            message = first_part[1:]
            # Next, continue recv until the full message has been received
            while (len(message) < message_length):
                # Receive the next part of the message
                next_part = self.sock.recv(BUFFER_SIZE)
                # If there is a next part, append it to the current message
                if next_part:
                    print("..Received '" + next_part.decode() + "'")
                    message += next_part
                # Else, the client has disconnected, so return false
                else:
                    print("Client disconnected!")
                    return False
            return message.decode()
        else:
            return False


if __name__ == "__main__":
    BufferedTCPEchoClient(SERVER_NAME, SERVER_PORT).start()