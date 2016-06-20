#!/usr/bin/python

# system-wide libraries
import csv
import time
import timeit
import traceback
from pygal import *
import ConfigParser
from rdflib import *
from numpy import mean
from pygal.style import *
from datetime import datetime
from smart_m3.m3_kp_api import *

# local libraries
from output_helpers import *
from JSON_kpi import KP as JKP
from JSON_kpi import Triple as JTriple


# class UpdateTestException
class QueryTestException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# class QueryTest
class QueryTest:

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

        # config query section
        self.querytype = config.get("query", "type")
        if self.querytype == "RDF-M3":
            self.subject_template = config.get("query", "subject_template")
            self.predicate_template = config.get("query", "predicate_template")
            self.object_template = config.get("query", "object_template")
            self.subject_type = config.get("query", "subject_type")
            self.predicate_type = config.get("query", "predicate_type")
            self.object_type = config.get("query", "object_type")
        elif self.querytype == "SPARQL":
            self.query_text = config.get("query", "text")
        self.sleep = config.getfloat("query", "sleep")
        self.iterations = config.getint("query", "iterations")
        self.with_update = config.getboolean("query", "with_update")
        
        # read update parameters
        if self.with_update:
            self.updatetype = config.get("update", "type")
            if self.updatetype == "RDF-M3":
                self.upd_subject_template = config.get("update", "subject_template")
                self.upd_predicate_template = config.get("update", "predicate_template")
                self.upd_object_template = config.get("update", "object_template")
                self.upd_subject_type = config.get("update", "subject_type")
                self.upd_predicate_type = config.get("update", "predicate_type")
                self.upd_object_type = config.get("update", "object_type")
            elif self.updatetype == "SPARQL":
                self.update_text = config.get("update", "text")
            self.upd_step = config.getint("update", "step")
            self.upd_limit = config.getint("update", "limit")

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
            self.oh = OutputHelper("QueryTest", "blue")

        # results
        self.results = None


    # run
    def run(self):

        # run the right method depending on the update type
        if self.querytype == "RDF-M3":
            try:
                if self.with_update:
                    self.complex_rdfm3_test()
                else:
                    self.basic_rdfm3_test()
            except QueryTestException as e:
                return False, str(e)

        elif self.querytype == "SPARQL":
            try:
                self.sparql_test()
            except QueryTestException as e:
                return False, str(e)

        # plot the graph
        if self.plot:
            try:
                if self.querytype == "RDF-M3":
                    if self.with_update:
                        self.plot_complex_chart()
                    else:
                        self.plot_basic_chart()
                elif self.querytype == "SPARQL":
                    self.plot_basic_chart()

            except QueryTestException as e:
                return False, str(e)

        # write the csv
        if self.csv:
            try:
                if self.querytype == "RDF-M3":
                    if self.with_update:
                        self.csv_complex_output()
                    else:
                        self.csv_basic_output()
                elif self.querytype == "SPARQL":
                    self.csv_basic_output()

            except QueryTestException as e:
                return False, str(e)
                
        # return
        return True, None


    # basic rdf-m3 test
    def basic_rdfm3_test(self):

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
                    self.oh.p("basic_rdfm3_test", "--- Iteration: %s" % iteration)
                        
                # retrieve data
                if sib["protocol"] == "SSAP":
    
                    # define the triple pattern for the query
                    triple_pattern = Triple(URI(self.subject_template), URI(self.predicate_template), URI(self.object_template))
    
                    # try to query and measure time
                    try:
                        self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].load_query_rdf(triple_pattern), number=1), 3))
                    except Exception as e:
                        if self.debug:
                            self.oh.p("rdfm3_test", "Query failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))
                            
                elif sib["protocol"] == "JSSAP":
    
                    # define the triple pattern for the query
                    triple_pattern = JTriple(URIRef(self.subject_template), URIRef(self.predicate_template), URIRef(self.object_template))
                        
                    # try to query and measure time
                    try:

                        # query
                        self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].query_rdf([triple_pattern]), number=1), 3))

                    except Exception as e:
                        if self.debug:
                            self.oh.p("rdfm3_test", "Query failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))
                            
                    # sleep
                    time.sleep(self.sleep)


    # complex rdfm3-test
    def complex_rdfm3_test(self):

        # initialize the results
        self.results = {}
        for sib in self.sibs:
            self.results[sib["name"]] = {}
            for num_triples in range(self.upd_step, self.upd_limit + self.upd_step, self.upd_step):
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
            for num_triples in range(self.upd_step, self.upd_limit + self.upd_step, self.upd_step):
                
                # debug
                if self.debug:
                    self.oh.p("rdfm3_test", "- Block dimension: %s" % num_triples)

                # build a triple list with num_triples triples 
                triple_list = []
                for triple_number in xrange(num_triples):
                    
                    if sib["protocol"] == "SSAP":
                    
                        # TODO: add a check also for subject and predicate
                        obj = None
                        if self.upd_object_type == "URI":
                            obj = URI(self.upd_object_template % triple_number)
                        else:
                            obj = Literal(self.upd_object_template % triple_number)                    
                            triple_list.append(Triple(URI(self.upd_subject_template % triple_number), 
                                                      URI(self.upd_predicate_template % triple_number), 
                                                      obj))

                    elif sib["protocol"] == "JSSAP":

                        # TODO: add a check also for subject and predicate
                        obj = None
                        if self.upd_object_type == "URI":
                            obj = URIRef(self.upd_object_template % triple_number)
                        else:
                            obj = Literal(self.upd_object_template % triple_number)                    
                            triple_list.append(JTriple(URIRef(self.upd_subject_template % triple_number), 
                                                       URIRef(self.upd_predicate_template % triple_number), 
                                                       obj))

                # insert
                if sib["protocol"] == "SSAP":

                    # clean the SIB                        
                    sib["kp"].load_rdf_remove(Triple(None, None, None))

                    # insert
                    sib["kp"].load_rdf_insert(triple_list)

                elif sib["protocol"] == "JSSAP":

                    # clean the SIB                    
                    sib["kp"].remove([JTriple(None, None, None)])

                    # insert
                    sib["kp"].insert(triple_list)
                                    
                # iterate over the number of iterations
                for iteration in range(self.iterations):

                    # debug
                    if self.debug:
                        self.oh.p("rdfm3_test", "--- Iteration: %s" % iteration)

                    # wait
                    time.sleep(self.sleep)

                    # insert data
                    if sib["protocol"] == "SSAP":

                        # try to retrieve data and measure time
                        try:

                            # define the triple pattern for the query
                            triple_pattern = Triple(URI(self.subject_template), URI(self.predicate_template), URI(self.object_template))

                            # query
                            self.results[sib["name"]][str(len(triple_list))].append(round(timeit.timeit(lambda: sib["kp"].load_query_rdf(triple_pattern), number=1), 3))

                        except Exception as e:
                            if self.debug:
                                self.oh.p("rdfm3_test", "Insertion failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))

                    elif sib["protocol"] == "JSSAP":

                        # try to insert and measure time
                        try:

                            # define the triple pattern for the query
                            triple_pattern = JTriple(URIRef(self.subject_template), URIRef(self.predicate_template), URIRef(self.object_template))
                        
                            # query
                            self.results[sib["name"]][str(len(triple_list))].append(round(timeit.timeit(lambda: sib["kp"].query_rdf(triple_pattern), number=1), 3))

                        except Exception as e:
                            if self.debug:
                                self.oh.p("rdfm3_test", "Insertion failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))

    
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
                
                    # try to query and measure time
                    try:
                        self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].load_query_sparql(self.query_text), number=1), 3))
                    except Exception as e:
                        if self.debug:
                            self.oh.p("sparql_test", "Query failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))
                            
                elif sib["protocol"] == "JSSAP":
    
                    # try to query and measure time
                    try:

                        # query
                        self.results[sib["name"]].append(round(timeit.timeit(lambda: sib["kp"].query_sparql(self.query_text), number=1), 3))

                    except Exception as e:
                        if self.debug:
                            self.oh.p("sparql_test", "Query failed with exception %s" % e, False)
                            raise UpdateTestException(str(e))
                            
                    # sleep
                    time.sleep(self.sleep)


    # csv output
    def csv_basic_output(self):
        
        """This method is used to report the results of
        a query test to a csv file"""

        # determine the file name
        csv_filename = "query-%s-%siter-%s-%s.csv" % (self.querytype,
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

            # add the mean value of the times to the row
            row.append(round(mean(self.results[sib]),3))                

            # write the row
            csvfile_writer.writerow(row)
                
        # close the csv file
        csvfile_stream.close()


    # csv output
    def csv_complex_output(self):
        
        """This method is used to report the results of
        a query test to a csv file"""

        # determine the file name
        csv_filename = "query-%s-%siter-%s-%s.csv" % (self.querytype,
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
                row.append(round(mean(self.results[sib][triple_length]),3))                

                # write the row
                csvfile_writer.writerow(row)
                
        # close the csv file
        csvfile_stream.close()



    # plot
    def plot_complex_chart(self):
        
        """This method is used to plot the chart"""
            
        # determine the type of the chart
        if self.chart_type == "Bar":
            
            # determine the file name
            chart_filename = "query-%s-%siter-%s-%s.svg" % (self.querytype,
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
                    values.append(mean(self.results[sib][triple_length]))      

                # add the values to the chart
                chart.add(sib, values)

            # plot the chart
            chart.render_to_file(chart_filename)

        else:

            # chart type not available
            raise UpdateTestException("Chart type %s not available" % self.chart_type)


    # plot
    def plot_basic_chart(self):
        
        """This method is used to plot the chart"""
            
        # determine the type of the chart
        if self.chart_type == "Bar":
            
            # determine the file name
            chart_filename = "query-%s-%siter-%s-%s.svg" % (self.querytype,
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
                values.append(mean(self.results[sib]))      

                # add the values to the chart
                chart.add(sib, values)

            # plot the chart
            chart.render_to_file(chart_filename)

        else:

            # chart type not available
            raise UpdateTestException("Chart type %s not available" % self.chart_type)
