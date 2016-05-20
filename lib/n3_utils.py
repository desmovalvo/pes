#!/usr/bin/python

# system wide requirements
from smart_m3.m3_kp_api import *
import rdflib


# class N3Exception
class N3Exception(Exception):

    def __init__(self, value):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)


# get_triples_from_n3file
def get_triples_from_n3file(filename):

    """Utility that build the triple list from an n3 file"""

    # parsing
    try:
        g = rdflib.Graph()
        res = g.parse(filename, format='n3')
    except Exception as e:
        raise N3Exception("Parsing failed!")

    # extracting triples
    triple_list = []
    for triple in res:
        
        # build the triple
        s = []
        for t in triple:
    
            if type(t).__name__  == "URIRef":
                s.append(URI(t))
                
            elif type(t).__name__  == "Literal":
                s.append(Literal(t))
    
            elif type(t).__name__  == "BNode":
                s.append( bNode(t) )

        # add the triple to the list
        triple_list.append(Triple(s[0], s[1], s[2]))

    # return
    return triple_list
