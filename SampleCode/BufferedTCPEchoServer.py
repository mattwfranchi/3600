from socket import *
from struct import pack, unpack

# Define variables that hold the desired port and buffer size
SERVER_PORT = 3604
BUFFER_SIZE = 32

### Protocol Definition
### first byte defines message length (maximum message length of 255 characters)
### remaining bytes contain a string message

class BufferedTCPEchoServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def start(self):
        # Begin listening for new connection requests
        self.sock.listen(1)
        print('The server is listening...')

        # Loop forever listening for new connection requests
        while True:
            print("Waiting for a new connection...")
            # Attempt to accept a new connection. This call will block until a connection request is received
            client, address = self.sock.accept()
            print("Accepted connection from ", address)
            
            # Continue receiving input from the client until they disconnect
            while True:
                # Receive the next message
                message = self.receive_message(client)
                # If a message was received, echo it back to the client
                if message:
                    print('Echoing "', message, '" to ', address)
                    self.send_message(client, message)
                # Otherwise, the client has disconnected
                else:
                    print("Client disconnected")
                    client.close()
                    break

    def receive_message(self, client):
        # Get the first part of the message, this includes the header and the start of the string
        first_part = client.recv(BUFFER_SIZE)

        if first_part:
            # First, strip out the header
            message_length = unpack("!B", first_part[:1])[0]
            print("..New message size: " + str(message_length))
            print("..Received '" + first_part[1:].decode() + "'")

            message = first_part[1:].decode()
            # Next, continue recv until the full message has been received
            while (len(message) < message_length):
                # Receive the next part of the message
                next_part = client.recv(BUFFER_SIZE)
                # If there is a next part, append it to the current message
                if next_part:
                    print("..Received '" + next_part.decode() + "'")
                    message += next_part.decode()
                # Else, the client has disconnected, so return false
                else:
                    print("Client disconnected!")
                    return False
            return message
        else:
            return False

    def send_message(self, client, message):
        message_length = len(message)
        data = pack("!B" + str(message_length) + "s", message_length, message.encode()) 
        client.send(data)


if __name__ == "__main__":
    BufferedTCPEchoServer('', SERVER_PORT).start()