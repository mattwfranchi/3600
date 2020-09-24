# Matt Franchi
# CPSC 3600
# Programming Activity I
# September 22 2020

# Module Imports
from optparse import OptionParser
from socket import *
import os, sys
import selectors
import logging
import types



class Client:

    clientCount = 1

    def __init__(self, port = 3604, host = 'newton.computing.clemson.edu'):
        self.sel = selectors.DefaultSelector()
        self.sock = socket(AF_INET,SOCK_STREAM)
        self.sock.bind((host,port))
        self.sock.listen()

        conn, addr = self.sock.accept()
        conn.setblocking(False)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE

        self.sel.register(conn,events,Client.clientCount)
        Client.clientCount += 1




if __name__ == "__main__":

    client1 = Client()
    client2 = Client()
    client3 = Client()

    clients = [client1,client2,client3]

    while(True):
        userInput = input("Enter some input: ")
        for client in clients:
            events = client.sel.select(timeout=10)
            for key, mask in events:
                sock = key.fileobj
                data = key.data

                if mask & selectors.EVENT_READ:
                    response = client.sock.recv(2048)


