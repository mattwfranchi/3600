class MessageParser(object):
    def __init__(self):
        pass

    
    # This function should return a list of dictionaries. Each element in the list represents a separate 
    # message that has been parsed. Each dictionary represents the different elements of that message:
    # the prefix, the command, and the list of params. An example of the data structure to be returned 
    # is shown below:
    # [message1, message2, message3], where
    # message1 =
    # {
    #   "prefix": "theshire.nz",
    #   "command": "SERVER",
    #   "params": ["rivendale.nz", 1, "Home of the Hobbits"]
    # }
    # message2 =
    # {
    #   "prefix": None,
    #   "command": "SERVER",
    #   "params": ["minastirith.nz", 1, "Tower of Guard"]
    # }
    # message3 =
    # {
    #   "prefix": None,
    #   "command": "QUIT",
    #   "params": None
    # }

    # When processing data received from a socket, it's possible that the data contains multiple commands
    # We need to split the message into a list of commands, which are delimited by \r\n
    def parse_data(self, recv_data):
        p_commands = []

        commands = recv_data.decode().split("\r\n")

        for m in commands:
            message = {
                "prefix": None,
                "command": None,
                "params": None
            }

            print("message:", m)

            #if message has a prefix
            if m.startswith(':'):
                c = m.split(':')
                l = c[1].split(' ')
                message['prefix'] = l[0]
                message['command'] = l[1]

                if len(l) > 2:
                    message['params'] = []
                    x = len(l)
                    l2 = l[2:x]
                    for i in l2:
                        if i == '':
                            message['params'].append(c[-1])
                            break
                        else:
                            message['params'].append(i)
            #if message doesn't have a prefix
            else:
                l = m.split(' ')
                c = m.split(':')
                message['command'] = l[0]

                if len(l) > 1:
                    message['params'] = []
                    x = len(l)
                    l2 = l[1:x]
                    for i in l2:
                        if i.startswith(':'):
                            message['params'].append(c[-1])
                            break
                        else:
                            message['params'].append(i)
                    
                    
            p_commands.append(message)


        return p_commands