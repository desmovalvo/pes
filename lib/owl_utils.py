#!/usr/bin/python

# system wide requirements
from smart_m3.m3_kp_api import *
from rdflib import Graph
from rdflib import URIRef
from rdflib import Literal as JLiteral

# local libraries
from lib.JSON_kpi import Triple as JTriple


# class OWLException
class OWLException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# get_triples_from_owlfile
def get_triples_from_owlfile(filename, protocol):

    """Utility that build the triple list from an owl file"""

    # parsing
    g = Graph()
    try:
        g.parse(filename, format='xml')
    except Exception as e:
        raise OWLException("Parsing failed!")

    # initializing the list
    triple_list = []

    # retrieving triples
    for triple in g:

        sub = pred = ob = None

        # subject
        if unicode(type(triple[0])) == "<class 'rdflib.term.URIRef'>":
            if protocol == "SSAP":
                sub = URI(unicode(triple[0]))
            elif protocol == "JSSAP":
                sub = URIRef(unicode(triple[0]))
        else:
            sub = bNode(unicode(triple[0]))
            
        # predicate
        if protocol == "SSAP":
            pred = URI(unicode(triple[1]))
        elif protocol == "JSSAP":
            pred = URIRef(unicode(triple[1]))

        # object
        if protocol == "SSAP":
            if unicode(type(triple[2])) == "<class 'rdflib.term.URIRef'>":
                ob = URI(unicode(triple[2]))
            elif unicode(type(triple[2])) == "<class 'rdflib.term.Literal'>":
                ob = Literal(triple[2].encode('utf-8'))
            else:
                ob = bNode(unicode(triple[2]))
        if protocol == "JSSAP":
            if unicode(type(triple[2])) == "<class 'rdflib.term.URIRef'>":
                ob = URIRef(unicode(triple[2]))
            elif unicode(type(triple[2])) == "<class 'rdflib.term.Literal'>":
                ob = Literal(triple[2].encode('utf-8'))
            else:
                ob = bNode(unicode(triple[2]))    

        # build the triple and add it to the list
        if protocol == "SSAP":
            a = Triple(sub, pred, ob)
            triple_list.append(a)
        elif protocol == "JSSAP":
            a = JTriple(sub, pred, ob)
            triple_list.append(a)

    # return
    return triple_list
