#!/usr/bin/python

# system-wide libraries
# TODO: import the json ssap api
import rdflib
import traceback
import ConfigParser
from smart_m3.m3_kp_api import *

# local libraries
from output_helpers import *
from owl_utils import *
from n3_utils import *

# class KB Loader
class KBLoader:

    # init
    def __init__(self, config_file):

        """Constructor for the KB Loader class"""
        
        # read the configuration file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(open(config_file))
        self.debug = config.getboolean("debug", "log")
        self.step = config.getint("loader", "step")
    
        # create an output helper
        if self.debug:
            color = config.get("debug", "color")
            self.oh = OutputHelper("KBLoader", color)

    
    # load n3 file
    def load_n3_file(self, sib_host, sib_port, sib_name, sib_protocol, filename):

        """This method load the triples contained in the n3 file
        specified by filename into the given SIB"""

        # debug print
        if self.debug:
            self.oh.p("load_n3_file", "Loading %s into %s (%s:%s)" % (filename, sib_name, sib_host, sib_port))

        # parse the n3 file
        self.oh.p("load_n3_file", "Parsing n3 file...")
        try:
            triple_list = get_triples_from_n3file(filename)
        except N3Exception:
            if self.debug:
                self.oh.p("load_n3_file", "Error while parsing N3 file!", True)
            return False

        # connect to the sib        
        kp = None
        if sib_protocol == "SSAP":
            try:
                kp = m3_kp_api(False, sib_host, sib_port)
            except Exception as e:
                if self.debug:
                    self.oh.p("load_n3_file", "Insertion failed!", True)
                    print traceback.print_exc()
                return False
        else:
            return False
            
        # buffered insert
        counter = 0
        ttl = []
        for triple in triple_list:
            counter += 1
            ttl.append(triple)
            if counter == self.step:
                if sib_protocol == "SSAP":
                    try:
                        self.oh.p("load_n3_file", "Inserting %s triples..." % len(ttl))
                        kp.load_rdf_insert(ttl)
                        ttl = []
                        counter = 0
                    except Exception as e:
                        if self.debug:
                            self.oh.p("load_n3_file", "Insertion failed!", True)
                            print traceback.print_exc()                    
                        return False

        if len(ttl) > 0:
            if sib_protocol == "SSAP":
                try:
                    self.oh.p("load_n3_file", "Inserting %s triples..." % len(ttl))
                    kp.load_rdf_insert(ttl)
                except Exception as e:
                    if self.debug:
                        self.oh.p("load_n3_file", "Insertion failed!", True)
                        print traceback.print_exc()                    
                    return False

        # return
        return True
        

    # load owl file
    def load_owl_file(self, sib_host, sib_port, sib_name, sib_protocol, filename):

        """This method load the triples contained in the owl
        file specified by filename into the given SIB"""

        # debug print
        if self.debug:
            self.oh.p("load_owl_file", "Loading %s into %s (%s:%s)" % (filename, sib_name, sib_host, sib_port))

        # parse the owl file
        self.oh.p("load_owl_file", "Parsing owl file...")
        try:
            triple_list = get_triples_from_owlfile(filename)
        except OWLException:
            if self.debug:
                self.oh.p("load_owl_file", "Error while parsing OWL file!", True)
            return False
                
        # connect to the sib        
        kp = None
        if sib_protocol == "SSAP":
            try:
                kp = m3_kp_api(False, sib_host, sib_port)
            except Exception as e:
                if self.debug:
                    self.oh.p("load_owl_file", "Insertion failed!", True)
                    print traceback.print_exc()
                return False
        else:
            return False
            
        # buffered insert
        counter = 0
        ttl = []
        for triple in triple_list:
            counter += 1
            ttl.append(triple)
            if counter == self.step:
                if sib_protocol == "SSAP":
                    try:
                        self.oh.p("load_owl_file", "Inserting %s triples..." % len(ttl))
                        kp.load_rdf_insert(ttl)
                        ttl = []
                        counter = 0
                    except Exception as e:
                        if self.debug:
                            self.oh.p("load_owl_file", "Insertion failed!", True)
                            print traceback.print_exc()                    
                        return False

        if len(ttl) > 0:
            if sib_protocol == "SSAP":
                try:
                    self.oh.p("load_owl_file", "Inserting %s triples..." % len(ttl))
                    kp.load_rdf_insert(ttl)
                except Exception as e:
                    if self.debug:
                        self.oh.p("load_owl_file", "Insertion failed!", True)
                        print traceback.print_exc()                    
                    return False

        # return
        return True




