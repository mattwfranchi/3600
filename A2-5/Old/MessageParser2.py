# Marianna Moawad - CPSC 3600

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
        final_list = []
        commands = recv_data.decode().split('\r\n')

        if commands[-1] == '':
            commands.pop(-1)

        # Can have multiple commands
        for command in commands:


            # Each command will have this dictionary
            temp_dict = {
                'prefix': None,
                'command': None,
                'params':None
            }

            if command.startswith(':'):
                colon_splits = command.split(':')
                # looking at the text after the colon
                txt = colon_splits[1].split(' ')

                temp_dict['prefix'] = txt[0]
                temp_dict['command'] = txt[1]

                # checking for parameters
                if len(txt) > 2:
                    temp_dict['params'] = []
                    # checking for trailing params
                    if len(colon_splits) >= 3:
                        # looping through sublist of remainng items
                        for i in txt[2:len(txt)]:
                            # checking if reached the trailing params
                            if i == '':
                                temp_dict['params'].append(colon_splits[-1])
                                break
                            else:
                                temp_dict['params'].append(i)
                    else:
                        temp_dict['params'] = txt[2:len(txt)]
                    
            # no prefix
            else:
                colon_splits = command.split(':')
                txt = command.split(' ')

                temp_dict['command'] = txt[0]

                # checking for parameters
                if len(txt) > 1:
                    temp_dict['params'] = []
                    # checking for trailing params
                    if len(colon_splits) >= 2:
                        # looping through sublist of remainng items
                        for i in txt[1:len(txt)]:
                            # checking if reached the trailing params
                            if i.startswith(':'):
                                temp_dict['params'].append(colon_splits[-1])
                                break
                            else:
                                temp_dict['params'].append(i)
                    else:
                        temp_dict['params'] = txt[1:len(txt)]
                    

            # adding this message's dictionary to the final list 
            final_list.append(temp_dict)
        return final_list