# PA1 Solution

from socket import *
import selectors

SERVER_NAME = "newton.computing.clemson.edu"
SERVER_PORT = 3604


sel = selectors.DefaultSelector()
event_mask = selectors.EVENT_READ | selectors.EVENT_WRITE

# socket 1
sock1 = socket(AF_INET, SOCK_STREAM)
sock1.connect((SERVER_NAME,SERVER_PORT))
sock1.setblocking(False)
sel.register(sock1,event_mask,"1")

# socket 2
sock2 = socket(AF_INET, SOCK_STREAM)
sock2.connect((SERVER_NAME,SERVER_PORT))
sock2.setblocking(False)
sel.register(sock2,event_mask,"2")

# socket 3
sock3 = socket(AF_INET, SOCK_STREAM)
sock3.connect((SERVER_NAME,SERVER_PORT))
sock3.setblocking(False)
sel.register(sock3,event_mask,"3")

while True:
    msg = input(">>> ")

    events = sel.select(timeout = 1)
    for key, mask in events:
        sock = key.fileobj
        data = key.data

        if mask & selectors.EVENT_READ:
            rsp = sock.recv(2048)
            print(data + ": " + rsp.decode())

        if mask & selectors.EVENT_WRITE:
            print(data + ": send " + msg + " to server")
            sock.send(msg)

