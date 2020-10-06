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
        # Sorry about using regex! I wanted to teach myself something new because I wasn't very familiar with it

        # list processed_commands to store parsed commands
        processed_commands = []

        # split raw data into list of commands, delimited by "\r\n"
        commands = re.split("\r\n",recv_data.decode())

        # For each loop for each message in commands
        for msg in commands:
            # message dictionary spec
            message = {
                "prefix": None,
                "command": None,
                "params": None
            }

            # prefix detection
            # match must start with colon, and continues to match until whitespace is reached
            if re.findall("(?<=^):(\S*)", msg):
                prefix = re.findall("(?<=^):(\S*)", msg)[0]
            else:
                prefix = None

            # command detection
            # match must be ALL CAPS (at least 2 consecutive)
            command = re.findall("[A-Z]{2,}", msg)[0]

            # non-trailing parameters detection
            # parameters must occur AFTER command, and continue until a colon is reached
            params_string = re.findall("[A-Z]{2,}([^:]*)", msg)[0]
            # split params_string into actual parameters, matching non-whitespace
            params = re.findall("\S+", params_string)

            # trailing parameter detection
            # match everything after a colon that does NOT occur at the beginning of the string msg
            if re.findall("(?<!^):(.*)", msg):
                params.append(re.findall("(?<!^):(.*)", msg)[0])

            # put data into dictionary
            message["prefix"] = prefix
            message["command"] = command
            message["params"] = params

            # append dictionary to processed commands list
            processed_commands.append(message)

        return processed_commands
