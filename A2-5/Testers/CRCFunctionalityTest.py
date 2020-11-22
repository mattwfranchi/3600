import threading, os, re, time, sys, json, copy
from optparse import OptionParser
from Testers.CRCTest import CRCTest

class CRCFunctionalityTest(CRCTest):
    
    def __init__(self, CRCServerModule, CRCClientModule, catch_exceptions):
        super().__init__(CRCServerModule, CRCClientModule, catch_exceptions)


    def check_test_results(self, test, servers, clients):        
        problems = ""

        for state in test['final_state']:
            if state in servers:
                r, p = self.check_server(servers[state], test['final_state'][state])
                if not r:
                    problems += p

            elif state in clients:
                pass
                r, p = self.check_client(clients[state], test['final_state'][state])
                if not r:
                    problems += p

        # If there were problems, then this test fails and we return them
        if problems:
            return False, problems
        else:
            return True, None


    def check_server(self, server, configuration):
        problems = ""

        if 'adjacent_users' in configuration:
            problems += self.find_problems_with_server(server.servername, "adjacent_users", server.adjacent_users, configuration['adjacent_users'])
        if 'users_lookuptable' in configuration:
            problems += self.find_problems_with_server(server.servername, "users_lookuptable", server.users_lookuptable, configuration['users_lookuptable'])
        if 'adjacent_servers' in configuration:
            problems += self.find_problems_with_server(server.servername, "adjacent_servers", server.adjacent_servers, configuration['adjacent_servers'])
        if 'servers_lookuptable' in configuration:
            problems += self.find_problems_with_server(server.servername, "servers_lookuptable", server.servers_lookuptable, configuration['servers_lookuptable'])
        
        if problems:
            return False, problems
        else:
            return True, None


    def find_problems_with_server(self, servername, propertyname, server_list, configuration_list):
        problems = ""
        if len(server_list) != len(configuration_list):
            problems += "%s: Wrong number of %s (found %i, expected %i)\n" % (servername, propertyname, len(server_list), len(configuration_list))
        
        missing_from_server = self.diff(configuration_list, server_list)
        if missing_from_server:
            problems += "%s: Missing from %s: %s\n" % (servername, propertyname, ", ".join(missing_from_server))

        extra_in_server = self.diff(server_list, configuration_list)
        if extra_in_server:
            problems += "%s: Extra in %s: %s\n" % (servername, propertyname, ", ".join(extra_in_server))

        return problems

    

    def check_client(self, client, configuration):
        problems = ""

        if problems:
            return False, problems
        else:
            return True, None
