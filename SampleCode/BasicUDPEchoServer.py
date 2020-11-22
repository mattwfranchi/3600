from socket import *
import threading

# Define variables that hold the desired port and buffer size
SERVER_PORT = 3601
BUFFER_SIZE = 32

class BasicUDPEchoServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        with socket(AF_INET, SOCK_DGRAM) as s:
            s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            print('The server is listening...')
            while True:
                message, clientAddr = s.recvfrom(BUFFER_SIZE)
                message = message.decode()
                print('Echoing "', message, '" to ', clientAddr)
                s.sendto(message.encode(), clientAddr)

if __name__ == "__main__":
    BasicUDPEchoServer('', SERVER_PORT).start()