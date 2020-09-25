import threading, os, re, time, sys, json, copy
from optparse import OptionParser

class MessageParsingTest():
    
    def __init__(self, MessageParser, catch_exceptions):
        self.parser = MessageParser()
        self.catch_exceptions = catch_exceptions

        
    def run_test(self, test):
        try:
            result = ""
            # Loop through all of the commands in this test
            for command in test['commands']:
                msg = command["message"].encode()
                student_output = self.parser.parse_data(msg)
                result += (self.check_test_results(command["output"], student_output))
            
            if result != "":
                return False, result, None
            else:
                return True, "", None
        
        except Exception as e:
            if self.catch_exceptions:
                return False, result, e
            else: 
                raise e


    def check_test_results(self, test, student_output):

        errors = ""
        if len(test) == len(student_output):
            for i in range(len(student_output)):
                errors += self.check_prefix(test[i], student_output[i])
                errors += self.check_command(test[i], student_output[i])
                errors += self.check_params(test[i], student_output[i])
        else:
            errors += "Incorrect number of parsed messages. Expected %i, found %i\n" % (len(test), len(student_output))

        return errors


    def check_prefix(self, test, student_output):
        if test["prefix"] == student_output["prefix"]:
            return ""
        elif test["prefix"] == "" and student_output["prefix"] == None:
            return ""
        else:
            return "Incorrect prefix. Expected \"%s\", found \"%s\"\n" % (test["prefix"], student_output["prefix"])


    def check_command(self, test, student_output):
        if test["command"] != student_output["command"]:
            return "Incorrect command. Expected \"%s\", found \"%s\"\n" % (test["command"], student_output["command"])
        else:
            return ""


    def check_params(self, test, student_output):
        errors = ""
        # If we're expecting no params
        if test["params"] == "":
            # If the student's output has no params, all is good
            if student_output["params"] == None or student_output["params"] == []:
                errors += ""
            else:
                errors += "Incorrect params. Expected either None or an empty list of params, but you returned something else\n"

        else:
            if student_output["params"]:
                missing_from = self.diff(test["params"], student_output["params"])
                if missing_from:
                    errors += "Missing parameters: %s\n" % ", ".join(missing_from)

                extra_in = self.diff(student_output["params"], test["params"])
                if extra_in:
                    errors += "Extra parameters: %s\n" % ", ".join(extra_in)
            else:
                errors += "Missing parameters: %s\n" % ", ".join(test["params"])

        return errors


    # Helper function to find what differences exist in two lists
    def diff(self, list1, list2):
        return (list(set(list1) - set(list2)))

    def union(self, lst1, lst2): 
        final_list = list(set(lst1) | set(lst2)) 
        return final_list

    def intersect(self, lst1, lst2): 
        final_list = list(set(lst1) & set(lst2)) 
        return final_list