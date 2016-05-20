#!/usr/bin/python

# system-wide libraries
# TODO: import the json ssap api
import rdflib
import traceback
import ConfigParser
from smart_m3.m3_kp_api import *

# local libraries
from output_helpers import *

# class KB Loader
class KBLoader:

    # init
    def __init__(self, config_file):

        """Constructor for the KB Loader class"""
        
        # read the configuration file
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(open(config_file))

        # create an output helpre
        self.debug = config.getboolean("debug", "log")
        if self.debug:
            color = config.get("debug", "color")
            self.oh = OutputHelper("KBLoader", color)


    # load n3 file
    def load_n3_file(self, sib_ip, sib_port, sib_name, sib_protocol, step, filename):

        """This method load the triples contained in the n3 file
        specified by filename into the given SIB"""

        ### TODO: yet to implement

        # connect to the sib
        
        # copy data

        # return
        

    # load owl file
    def load_owl_file(self, sib_host, sib_port, sib_name, sib_protocol, step, filename):

        """This method load the triples contained in the owl
        file specified by filename into the given SIB"""

        # debug print
        if self.debug:
            self.oh.p("load_owl_file", "Loading %s into %s (%s:%s)" % (filename, sib_name, sib_host, sib_port))

        # work variables
        kp = None

        # parse the owl file
        g = rdflib.Graph()
        try:
            g.parse(filename, format='xml')
        except Exception as e:
            if self.debug:
                self.oh.p(load_owl_file, "Insertion failed!", True)
                print traceback.print_exc()
            return False

        # connect to the sib        
        if sib_protocol == "SSAP":
            try:
                kp = m3_kp_api(False, sib_host, sib_port)
            except Exception as e:
                if self.debug:
                    self.oh.p(load_owl_file, "Insertion failed!", True)
                    print traceback.print_exc()
                return False
        else:
            return False
        
        # copy data
        triple_list = []
        for triple in g:
    
            # subject
            if unicode(type(triple[0])) == "<class 'rdflib.term.URIRef'>":
                sub = URI(unicode(triple[0]))
            else:
                sub = bNode(unicode(triple[0]))
                
            # predicate
            pred = URI(unicode(triple[1]))
    
            # object
            if unicode(type(triple[2])) == "<class 'rdflib.term.URIRef'>":
                ob = URI(unicode(triple[2]))
            elif unicode(type(triple[2])) == "<class 'rdflib.term.Literal'>":
                ob = Literal(triple[2].encode('utf-8'))
            else:
                ob = bNode(unicode(triple[2]))
    
            # build the triple and add it to the list
            a = Triple(sub, pred, ob)
            triple_list.append(a)

            # proceed to insert them into the SIB if the
            # number of triples is equal to the step
            if len(triple_list) == step:
                if sib_protocol == "SSAP":
                    try:                    
                        kp.load_rdf_insert(triple_list)
                        triple_list = []
                    except Exception as e:
                        if self.debug:
                            self.oh.p(load_owl_file, "Insertion failed!", True)
                            print traceback.print_exc()
                        return False
                else:
                    return False

        # insert remaining triples
        if len(triple_list) > 0:
            if sib_protocol == "SSAP":
                try:                    
                    kp.load_rdf_insert(triple_list)
                except Exception as e:
                    if self.debug:
                        self.oh.p(load_owl_file, "Insertion failed!", True)
                        print traceback.print_exc()                    
                    return False
            else:
                return False
            
        # return
        return True
