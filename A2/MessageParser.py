import re


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
        processed_commands = []

        commands = re.split("\r\n",recv_data.decode())

        for msg in commands:
            message = {
                "prefix": None,
                "command": None,
                "params": None
            }

            if re.findall("(?<=^):(\S*)", msg):
                prefix = re.findall("(?<=^):(\S*)", msg)[0]
            else:
                prefix = None

            command = re.findall("[A-Z]{2,}", msg)[0]

            params_string = re.findall("[A-Z]{2,}([^:]*)", msg)[0]
            params = re.findall("\S+", params_string)
            params.append(re.findall("(?<!^):(.*)", msg))

            message["prefix"] = prefix
            message["command"] = command
            message["params"] = params


            processed_commands.append(message)



        return processed_commands
