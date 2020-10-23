from socket import *
import threading

# Define variables that hold the desired port and buffer size
SERVER_PORT = 3602
BUFFER_SIZE = 32

class BasicTCPEchoServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def start(self):
        self.sock.listen(50)
        print('The server is listening...')
        while True:
            client, address = self.sock.accept()
            self.silly_debugging_function("this is silly")
            print("Accepted connection from ", address)

            message = client.recv(BUFFER_SIZE)
            if message:
                message = message.decode()

                print('Echoing "', message, '" to ', address)
                client.send(message.encode())
            else:
                print("Client disconnected")
                client.close()

    def silly_debugging_function(self, test):
        pass

if __name__ == "__main__":
    BasicTCPEchoServer('', SERVER_PORT).start()