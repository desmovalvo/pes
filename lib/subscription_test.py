#!/usr/bin/python

# system-wide libraries
import csv
import time
import timeit
import traceback
from pygal import *
import ConfigParser
from rdflib import *
from numpy import mean as nmean
from numpy import min as nmin
from numpy import max as nmax
from numpy import var as nvar
from kb_loader import *
from pygal.style import *
from datetime import datetime
from smart_m3.m3_kp_api import *

# local libraries
from output_helpers import *
from JSON_kpi import KP as JKP
from JSON_kpi import Triple as JTriple


# class Handler
class SubscriptionHandler:

    def __init__(self, oh):
        self.oh = oh
        self.oh.p("subscription_handler", "Handler initialiazion")
        self.unlock = False

    def handle(self, added, removed):
        self.oh.p("subscription_handler", "Notification received!")
        self.unlock = True
        self.end_time = time.clock() * 1000
        

# class UpdateTestException
class SubscriptionTestException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# class SubscriptionTest
class SubscriptionTest:

    # constructor
    def __init__(self, sibs, configfile):

        # saving sibs
        self.sibs = sibs

        # date and time of the test
        self.testdatetime = datetime.now().strftime("%Y%m%d-%H%M")
        
        # reading configuration file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(open(configfile))

        # config debug section
        self.debug = config.getboolean("debug", "log")

        # config subscription section
        self.subscriptiontype = config.get("subscription", "type")
        if self.subscriptiontype == "RDF-M3":
            self.subject_template = config.get("subscription", "subject_template")
            self.predicate_template = config.get("subscription", "predicate_template")
            self.object_template = config.get("subscription", "object_template")
            self.subject_type = config.get("subscription", "subject_type")
            self.predicate_type = config.get("subscription", "predicate_type")
            self.object_type = config.get("subscription", "object_type")
        elif self.subscriptiontype == "SPARQL":
            self.subscription_text = config.get("subscription", "text")
        self.sleep = config.getfloat("subscription", "sleep")
        self.iterations = config.getint("subscription", "iterations")
        
        # config kbloader section
        self.kbloader_configfile = config.get("kbloader", "configfile")
        self.kbloader = KBLoader(self.kbloader_configfile)
        self.kb_usen3 = config.getboolean("kbloader", "usen3files")
        self.kb_useowl = config.getboolean("kbloader", "useowlfiles")
        if self.kb_usen3:
            self.kb_n3files = config.get("kbloader", "n3files").split("%")
        else:
            self.kb_n3files = []
        if self.kb_useowl:
            self.kb_owlfiles = config.get("kbloader", "owlfiles").split("%")
        else:
            self.kb_owlfiles = []

        # read update parameters
        self.updatetype = config.get("update", "type")
        if self.updatetype == "RDF-M3":
            self.upd_subject = config.get("update", "subject")
            self.upd_predicate = config.get("update", "predicate")
            self.upd_object = config.get("update", "object")
            self.upd_subject_type = config.get("update", "subject_type")
            self.upd_predicate_type = config.get("update", "predicate_type")
            self.upd_object_type = config.get("update", "object_type")
        elif self.updatetype == "SPARQL":
            self.update_text = config.get("update", "text")
            
        # config csv section
        self.csv = config.getboolean("csv", "csv")

        # config chart section
        self.plot = config.getboolean("chart", "plot")
        if self.plot:
            self.chart_type = config.get("chart", "type")
            self.chart_title = config.get("chart", "title")
            self.chart_x_title = config.get("chart", "x_title")
            self.chart_y_title = config.get("chart", "y_title")
            self.chart_style = config.get("chart", "theme")

        # output helper
        if self.debug:
            self.oh = OutputHelper("SubscriptionTest", "blue")

        # results
        self.results = None


    # run
    def run(self):

        # run the right method depending on the update type
        if self.subscriptiontype == "RDF-M3":
            try:
                self.rdfm3_test()
            except SubscriptionTestException as e:
                return False, str(e)

        elif self.subscriptiontype == "SPARQL":
            try:
                self.sparql_test()
            except SubscriptionTestException as e:
                return False, str(e)

        # plot the graph
        if self.plot:
            try:
                if self.subscriptiontype == "RDF-M3":
                    self.plot_chart()
                elif self.subscriptiontype == "SPARQL":
                    self.plot_chart()

            except SubscriptionTestException as e:
                return False, str(e)

        # write the csv
        if self.csv:
            try:
                if self.subscriptiontype == "RDF-M3":
                    self.csv_output()
                elif self.subscriptiontype == "SPARQL":
                    self.csv_output()

            except SubscriptionTestException as e:
                return False, str(e)
                
        # return
        return True, None


    # # basic rdf-m3 test
    # def rdfm3_test(self):

    #     # initialize the results
    #     self.results = {}
    #     for sib in self.sibs:
    #         self.results[sib["name"]] = []

    #     # connect to the SIBs
    #     for sib in self.sibs:
            
    #         # SSAP or JSSAP?
    #         if sib["protocol"] == "SSAP":

    #             # connect and add the KP to the dictionary
    #             kp = m3_kp_api(False, sib["host"], sib["port"])
    #             sib["kp"] = kp

    #         elif sib["protocol"] == "JSSAP":
                
    #             # connect and add the KP  to the dictionary
    #             kp = JKP(sib["host"], sib["port"], "X", False)
    #             sib["kp"] = kp

    #     # iterate over the SIBs
    #     for sib in self.sibs:

    #         # iterate over the number of iterations
    #         for iteration in range(self.iterations):
    
    #             # debug
    #             if self.debug:
    #                 self.oh.p("rdfm3_test", "--- Iteration: %s" % iteration)
                        
    #             # retrieve data
    #             if sib["protocol"] == "SSAP":
    
    #                 # define the triple pattern for the subscription
    #                 triple_pattern = Triple(URI(self.subject_template), URI(self.predicate_template), URI(self.object_template))
    
    #                 # try to subscription and measure time
    #                 try:
    #                     self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].load_subscription_rdf(triple_pattern), number=1), 3))
    #                 except Exception as e:
    #                     if self.debug:
    #                         self.oh.p("rdfm3_test", "Subscription failed with exception %s" % e, False)
    #                         raise SubscriptionTestException(str(e))
                            
    #             elif sib["protocol"] == "JSSAP":
    
    #                 # define the triple pattern for the subscription
    #                 triple_pattern = JTriple(URIRef(self.subject_template), URIRef(self.predicate_template), URIRef(self.object_template))
                        
    #                 # try to subscription and measure time
    #                 try:

    #                     # subscription
    #                     self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].subscription_rdf([triple_pattern]), number=1), 3))

    #                 except Exception as e:
    #                     if self.debug:
    #                         self.oh.p("rdfm3_test", "Subscription failed with exception %s" % e, False)
    #                         raise SubscriptionTestException(str(e))
                            
    #                 # sleep
    #                 time.sleep(self.sleep)

    
    # sparql test
    def sparql_test(self):

        # initialize the results
        self.results = {}
        for sib in self.sibs:
            self.results[sib["name"]] = []

        # connect to the SIBs
        for sib in self.sibs:
            
            # SSAP or JSSAP?
            if sib["protocol"] == "SSAP":

                # connect and add the KP to the dictionary
                kp = m3_kp_api(False, sib["host"], sib["port"])
                sib["kp"] = kp
                
            elif sib["protocol"] == "JSSAP":
                
                # connect and add the KP  to the dictionary
                kp = JKP(sib["host"], sib["port"], "X", False)
                sib["kp"] = kp

        # iterate over the SIBs
        for sib in self.sibs:

            # iterate over the number of iterations
            for iteration in range(self.iterations):
    
                # debug
                if self.debug:
                    self.oh.p("sparql_test", "--- Iteration: %s" % iteration)
                        
                # retrieve data
                if sib["protocol"] == "SSAP":

                    # load the KB                
                    for n3file in self.kb_n3files:
                        self.kbloader.load_n3_file(sib["host"], sib["port"], sib["name"], sib["protocol"], n3file)
                    for owlfile in self.kb_owlfiles:
                        self.kbloader.load_owl_file(sib["host"], sib["port"], sib["name"], sib["protocol"], owlfile)

                    # subscribe
                    handler = SubscriptionHandler(self.oh)
                    sib["active_sub"] = sib["kp"].load_subscribe_sparql(self.subscription_text, handler)

                    # start the timer
                    start_time = time.clock() * 1000

                    # update
                    if self.updatetype == "RDF-M3":
                        sib["kp"].load_rdf_insert([Triple(URI(self.upd_subject), URI(self.upd_predicate), Literal(self.upd_object))])
                    else:
                        sib["kp"].load_query_sparql(self.update_text)

                    # close the subscription
                    while not handler.unlock:
                        time.sleep(0.1)            
                    sib["kp"].load_unsubscribe(sib["active_sub"])

                    # compute the result
                    elapsed_time = handler.end_time - start_time
                    print elapsed_time
                    self.results[sib["name"]].append(round(elapsed_time, 3))

                    # clean the SIB
                    self.kbloader.clean_sib(sib["host"], sib["port"], sib["name"], sib["protocol"])
                    
                elif sib["protocol"] == "JSSAP":
                    
                    # TODO: load the KB
                    
                    # TODO: subscribe

                    # TODO: update

                    # TODO: close the subscription

                    # TODO: clean the SIB

                    pass

                # sleep
                time.sleep(self.sleep)


    # csv output
    def csv_output(self):
        
        """This method is used to report the results of
        a subscription test to a csv file"""

        # determine the file name
        csv_filename = "subscription-%s-%siter-%s-%s.csv" % (self.subscriptiontype,
                                                      self.iterations,
                                                      self.chart_type.lower(),
                                                      self.testdatetime)

        # initialize the csv file
        csvfile_stream = open(csv_filename, "w")
        csvfile_writer = csv.writer(csvfile_stream, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        # iterate over the SIBs
        for sib in self.results.keys():                    
                                     
            row = [sib]
            
            # add all the times
            for value in self.results[sib]:
                row.append(value)

            # add the mean, min, max and variance value of the times to the row
            row.append(round(nmean(self.results[sib]),3))                
            row.append(round(nmin(self.results[sib]),3))                
            row.append(round(nmax(self.results[sib]),3))                
            row.append(round(nvar(self.results[sib]),3))                

            # write the row
            csvfile_writer.writerow(row)
                
        # close the csv file
        csvfile_stream.close()


    # plot
    def plot_chart(self):
        
        """This method is used to plot the chart"""
            
        # determine the type of the chart
        if self.chart_type == "Box":
            
            # determine the file name
            chart_filename = "subscription-%s-%siter-%s-%s.svg" % (self.subscriptiontype,
                                                            self.iterations,
                                                            self.chart_type.lower(),
                                                            self.testdatetime)

            # initialise the chart
            chart = Box()
            chart.title = self.chart_title
            chart.x_title = self.chart_x_title
            chart.y_title = self.chart_y_title
            chart.style = eval(self.chart_style)

            # iterate over the SIBs
            for sib in self.results.keys():                    
                chart.add(sib, self.results[sib])

            # plot the chart
            chart.render_to_file(chart_filename)

        else:

            # chart type not available
            raise SubscriptionTestException("Chart type %s not available" % self.chart_type)
