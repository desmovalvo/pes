#!/usr/bin/python

# requirements
from termcolor import *

# class OH
class OutputHelper:

    # constructor
    def __init__(self, class_name, color):

        """Constructor for the OutputHelper class"""

        # setting class attributes
        self.class_name = class_name
        self.color = color
        self.error_color = "red"

        
    # print
    def p(self, method_name, message, error = False):

        header = "%s:%s> " % (self.class_name, method_name)
        if error:
            print colored(header, self.error_color, attrs=[bold]) + message
        else:
            print colored(header, self.color, attrs=["bold"]) + message
