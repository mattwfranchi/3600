import threading, os, re, time, sys, json, traceback
from optparse import OptionParser
from CRCServer import CRCServer as CRCServer
from CRCClient import CRCClient as CRCClient
from MessageParser import MessageParser as MessageParser
from Testers.NetworkConnectivityTest import NetworkConnectivityTest
from Testers.MessageParsingTest import MessageParsingTest
from Testers.CRCFunctionalityTest import CRCFunctionalityTest

class CRCLogger(object):
    def __init__(self, logfile):
        self.terminal = sys.stdout
        self.terminal = sys.stdout
        self.log = logfile
        self.lock = threading.Lock()

    def write(self, message):
        self.lock.acquire()
        try:
            self.terminal.write(message)
            self.log.write(message)
        finally:
            self.lock.release()

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        self.terminal.flush()
        self.log.flush()

    def print_to_log(self, message):
        self.log.write(message + "\n")

    def print_to_terminal(self, message):
        self.terminal.write(message)

class CRCTestManager(object):

    ######################################################################
    # Initialization
    def __init__(self, catch_exceptions = False):
        self.catch_exceptions = catch_exceptions


    ######################################################################
    # Test Management
    def run_tests(self, tests):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        if not os.path.exists(os.path.join(__location__, 'Logs')):
            os.makedirs(os.path.join(__location__, 'Logs'))   

        score = 0
        results = []
        for test in sorted(tests.keys()):
            # Open the test file
            with open(os.path.join(__location__, 'TestCases', '%s.cfg' % test), 'r') as fp:
                test_config = json.load(fp)
                # Redirect all output to a log file for this test
                with open(os.path.join(__location__, 'Logs', '%s.log' % test), 'w') as logfile:
                    sys.stdout = CRCLogger(logfile)
                    print("\n##############################################")
                    print("Beginning test " + test + "\n")
                    passed, errors, exception = self.run_test(test_config)
                    results.append({
                        'test':test, 
                        'passed':passed, 
                        'errors':errors,
                        'exception':exception
                    })
                    print("\nTest passed:" + str(passed))
                    time.sleep(0.1)
                    sys.stdout = sys.__stdout__

        print("\n##############################################")
        for result in results:
            if result['passed']:
                score += tests[result['test']]
            print("%s passed: %r" % (result['test'], result['passed']))
            if result['errors']:
                print("%s" % (result['errors']))
            if result['exception']:
                print(traceback.format_exc())
        
        return score

    def run_test(self, test):
        tester = None
        if test["type"] == "network_connectivity":
            tester = NetworkConnectivityTest(CRCServer, CRCClient, self.catch_exceptions)
        elif test["type"] == "message_parsing":
            tester = MessageParsingTest(MessageParser, self.catch_exceptions)
        elif test["type"] == "CRC_functionality":
            tester = CRCFunctionalityTest(CRCServer, CRCClient, self.catch_exceptions)
        else:
            return None
        return tester.run_test(test)
        

if __name__ == "__main__":

    test_manager = CRCTestManager()
    basic_score = 0
    message_parsing_score = 0
    CRC_connection_score = 0

    basic_connection_tests = {
        'NetworkConnectivity_1_TwoServers':5, 
        #'NetworkConnectivity_2_FourServers':5,
        'NetworkConnectivity_3_EightServers':5, 
    }
    message_parsing_tests = {
        'MessageParsing_1_single_param':5, 
        'MessageParsing_2_multiple_params':5, 
        'MessageParsing_3_prefix_and_params':5, 
        'MessageParsing_4_trailing_param':5, 
        'MessageParsing_5_prefix_and_trailing_param':5, 
        'MessageParsing_6_only_command':5, 
        'MessageParsing_7_prefix_no_params':5, 
        'MessageParsing_8_multiple_messages':5, 
    }
    CRC_connection_tests = {
        'ServerConnections_1_TwoServers':3,
        'ServerConnections_2_FourServers':4,
        'ServerConnections_3_EightServers':5,

        'ClientServerConnections_1_OneServer_OneClient':1,
        'ClientServerConnections_2_OneServer_FourClients':3,
        'ClientServerConnections_3_ThreeServers_SevenClients':4,
        'ClientServerConnections_4_ERROR_NickCollision':1,

        'QUIT_1_OneServer_FourClient':1,
        'QUIT_2_ThreeServers_SevenClients':2,
    }


    #test_manager.run_tests(basic_connection_tests)
    test_manager.run_tests(message_parsing_tests)
    #test_manager.run_tests(CRC_connection_tests)


