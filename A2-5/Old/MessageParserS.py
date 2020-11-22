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
        # Split message by CR LF character, this will extract all of the commands present in the data
        messages = recv_data.decode().split("\r\n")
        if messages[-1] == '':
            messages.pop(-1)

        output = []
        for mesage in messages:
            if mesage:
                output.append(self.parse_mesage(mesage))

        return output


    # process_message extracts the prefix (if present), the command, and the params (if present), and
    # then forwards the information to the relevant command handler
    def parse_mesage(self, message):        
        # Extract the prefix
        prefix, body = self.get_prefix(message)

        # Extract the command
        command, param = self.parse_command(body)

        # Extract the params, if present
        if param:
            param = self.parse_params(param)

        return {
            "prefix": prefix,
            "command": command,
            "params": param
        }


    # Separates the prefix from the message
    # Should return two values: the prefix, and the remainder of the message
    # If there is no prefix, return None for the prefix
    def get_prefix(self, message):
        # Check to see if there is a prefix. This is indicated by a leading : character
        if message.startswith(':'):
            # Split the message into two parts on the first <SPACE> character found
            parts = message[1:].split(' ', 1)
            return parts[0], parts[1]
        else:
            return None, message       


    # Separates the command from the params
    # Should return two values: the command, and the params
    # If there are no params, return None for the params
    def parse_command(self, message):
        # Extract the command by spliting the string on the first <SPACE> encountered
        # parts[0] = command
        # parts[1] = params
        parts = message.split(' ', 1)
        if (len(parts) == 2):
            return parts[0], parts[1]
        else:
            return parts[0], None


    # Extract the parameters from the message
    # We need to handle the following circumstances:
    # 1. The message only contains <MIDDLE> params
    # 2. The message contains <MIDDLE> params and a <TRAILING> param
    # 3. The message only contains a <TRAILING> params
    def parse_params(self, message):
        # Check to see if : is the first character. In this case, we ONLY have a trailing parameter
        if message.startswith(":"):
            # Return a list that contains the trailing parameter, with the : removed
            return [message[1:]]
        else:
            # Extract the trailing parameter, if present
            last_param = "empty"
            parts = message.split(':')
            if len(parts) == 2:
                last_param = parts[1]
            else:
                last_param = None
            
            # Extract the other parameters
            params = parts[0].strip().split(' ')
            if last_param:
                params.append(last_param)
            # Return the list of parameters 
            return params