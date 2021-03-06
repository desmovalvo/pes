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
from pygal.style import *
from datetime import datetime
from smart_m3.m3_kp_api import *

# local libraries
from output_helpers import *
from JSON_kpi import KP as JKP
from JSON_kpi import Triple as JTriple


# class UpdateTestException
class UpdateTestException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# class UpdateTest
class UpdateTest:

    """This class is used to perform the update test
    using either SPARQL or RDF-M3"""

    # constructor
    def __init__(self, sibs, configfile):

        """This is the constructor for the UpdateTest class"""
        
        # saving sibs
        self.sibs = sibs

        # date and time of the test
        self.testdatetime = datetime.now().strftime("%Y%m%d-%H%M")
        
        # reading configuration file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(open(configfile))

        # config debug section
        self.debug = config.getboolean("debug", "log")

        # config update section
        self.updatetype = config.get("update", "type")
        if self.updatetype == "RDF-M3":
            self.subject_template = config.get("update", "subject_template")
            self.predicate_template = config.get("update", "predicate_template")
            self.object_template = config.get("update", "object_template")
            self.subject_type = config.get("update", "subject_type")
            self.predicate_type = config.get("update", "predicate_type")
            self.object_type = config.get("update", "object_type")
        elif self.updatetype == "SPARQL":
            self.update_text = config.get("update", "text")
        self.step = config.getint("update", "step")
        self.limit = config.getint("update", "limit")
        self.sleep = config.getfloat("update", "sleep")
        self.iterations = config.getint("update", "iterations")

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
            self.oh = OutputHelper("UpdateTest", "blue")

        # results
        self.results = None


    # run
    def run(self):
        
        # run the right method depending on the update type
        if self.updatetype == "RDF-M3":
            try:
                self.rdfm3_test()
            except UpdateTestException as e:
                return False, str(e)

        elif self.updatetype == "SPARQL":
            try:
                self.sparql_test()
            except UpdateTestException as e:
                return False, str(e)

        # plot the graph
        if self.plot:
            try:
                self.plot_chart()
            except UpdateTestException as e:
                return False, str(e)

        # write the csv
        if self.csv:
            try:
                self.csv_output()
            except UpdateTestException as e:
                return False, str(e)
                
        # return
        return True, None


    # rdfm3-test
    def rdfm3_test(self):

        # initialize the results
        self.results = {}
        for sib in self.sibs:
            self.results[sib["name"]] = {}
            for num_triples in range(self.step, self.limit + self.step, self.step):
                self.results[sib["name"]][str(num_triples)] = []

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

            # debug
            if self.debug:
                self.oh.p("rdfm3_test", "Testing sib %s" % sib["name"])

            # iterate over the range
            for num_triples in range(self.step, self.limit + self.step, self.step):
                
                # debug
                if self.debug:
                    self.oh.p("rdfm3_test", "- Block dimension: %s" % num_triples)

                # build a triple list with num_triples triples
                triple_list = []
                for triple_number in xrange(num_triples):
                    
                    if sib["protocol"] == "SSAP":

                        # TODO: add a check also for subject and predicate
                        obj = None
                        if self.object_type == "URI":
                            obj = URI(self.object_template % triple_number)
                        else:
                            obj = Literal(self.object_template % triple_number)                    
                            triple_list.append(Triple(URI(self.subject_template % triple_number), 
                                                      URI(self.predicate_template % triple_number), 
                                                      obj))

                    elif sib["protocol"] == "JSSAP":

                        # TODO: add a check also for subject and predicate
                        obj = None
                        if self.object_type == "URI":
                            obj = URIRef(self.object_template % triple_number)
                        else:
                            obj = Literal(self.object_template % triple_number)                    
                            triple_list.append(JTriple(URIRef(self.subject_template % triple_number), 
                                                       URIRef(self.predicate_template % triple_number), 
                                                       obj))
                                    
                # iterate over the number of iterations
                for iteration in range(self.iterations):

                    # debug
                    if self.debug:
                        self.oh.p("rdfm3_test", "--- Iteration: %s" % iteration)

                    # wait
                    time.sleep(self.sleep)
                    
                    # clean the SIB
                    if sib["protocol"] == "SSAP":
                        sib["kp"].load_rdf_remove(Triple(None, None, None))
                    elif sib["protocol"] == "JSSAP":
                        sib["kp"].remove([JTriple(None, None, None)])

                    # insert data
                    if sib["protocol"] == "SSAP":

                        # try to insert and measure time
                        try:
                            self.results[sib["name"]][str(len(triple_list))].append(round(timeit.timeit(lambda: sib["kp"].load_rdf_insert(triple_list), number=1) * 1000, 3))
                        except Exception as e:
                            if self.debug:
                                self.oh.p("rdfm3_test", "Insertion failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))

                    elif sib["protocol"] == "JSSAP":

                        # try to insert and measure time
                        try:
                            self.results[sib["name"]][str(len(triple_list))].append(round(timeit.timeit(lambda: sib["kp"].insert(triple_list), number=1) * 1000, 3))
                        except Exception as e:
                            if self.debug:
                                self.oh.p("rdfm3_test", "Insertion failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))


    # sparql-test
    def sparql_test(self):
        pass

        
    # csv output
    def csv_output(self):
        
        """This method is used to report the results of
        an update test to a csv file"""

        # determine the file name
        csv_filename = "update-%s-%sstep-%smax-%siter-%s-%s.csv" % (self.updatetype,
                                                                    self.step,
                                                                    self.limit,
                                                                    self.iterations,
                                                                    self.chart_type.lower(),
                                                                    self.testdatetime)

        # initialize the csv file
        csvfile_stream = open(csv_filename, "w")
        csvfile_writer = csv.writer(csvfile_stream, delimiter=',', quoting=csv.QUOTE_MINIMAL)

        # iterate over the SIBs
        for sib in self.results.keys():                    
                         
            # iterate over the possible block lengths
            for triple_length in sorted(self.results[sib].keys(), key=int):
            
                row = [sib]
    
                # add the length of the block to the row
                row.append(triple_length)

                # add all the times
                for value in self.results[sib][triple_length]:
                    row.append(value)

                # add the mean value of the times to the row
                row.append(round(nmean(self.results[sib][triple_length]),3))                
                row.append(round(nmin(self.results[sib][triple_length]),3))                
                row.append(round(nmax(self.results[sib][triple_length]),3))                
                row.append(round(nvar(self.results[sib][triple_length]),3))                

                # write the row
                csvfile_writer.writerow(row)

        # close the csv file
        csvfile_stream.close()
                

    # plot
    def plot_chart(self):
        
        """This method is used to plot the chart"""
            
        # determine the type of the chart
        if self.chart_type == "Bar":
            
            # determine the file name
            chart_filename = "update-%s-%sstep-%smax-%siter-%s-%s.svg" % (self.updatetype,
                                                                          self.step,
                                                                          self.limit,
                                                                          self.iterations,
                                                                          self.chart_type.lower(),
                                                                          self.testdatetime)

            # initialise the chart
            chart = Bar()
            chart.title = self.chart_title
            chart.x_title = self.chart_x_title
            chart.y_title = self.chart_y_title
            chart.style = eval(self.chart_style)

            # iterate over the SIBs
            for sib in self.results.keys():                    
                
                # iterate over the possible block lengths
                values = []
                for triple_length in sorted(self.results[sib].keys(), key=int):
                    values.append(nmean(self.results[sib][triple_length]))                

                # add the values to the chart
                chart.add(sib, values)
            
            # add the labels for the x axis
            x_labels = []
            for triple_length in sorted(self.results[self.results.keys()[0]].keys(), key=int):
                x_labels.append(triple_length)
            chart.x_labels = x_labels

            # plot the chart
            chart.render_to_file(chart_filename)

        else:

            # chart type not available
            raise UpdateTestException("Chart type %s not available" % self.chart_type)

    
