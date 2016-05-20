#!/usr/bin/python

# system wide requirements
from smart_m3.m3_kp_api import *
import rdflib


# class OWLException
class OWLException(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# get_triples_from_owlfile
def get_triples_from_owlfile(filename):

    """Utility that build the triple list from an owl file"""

    # parsing
    g = rdflib.Graph()
    try:
        g.parse(filename, format='xml')
    except Exception as e:
        raise OWLException("Parsing failed!")

    # initializing the list
    triple_list = []

    # retrieving triples
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

    # return
    return triple_list
