#!/usr/bin/python

# requirements
import ujson as json
import datetime
import time
import uuid
import socket
import threading
from rdflib import *
from fyzz import parse

# SSAP - JSON
# message_type -> mt
# transaction_type -> tt
# transaction_id -> tid
# node_id -> nid
# space_id -> sid
# credentials -> auth 
# status -> code
# triple_list -> tl
# triple -> t
# object_type -> ot
# subject -> s
# predicate -> p
# object -> o
# encoding -> enc
# subscription_id -> subid
# indication_sequence -> indid
# added_triple_list -> atl
# removed_triple_list -> rtl
# update_text -> ut

# constants
SIB_ANY_URI = 'http://www.nokia.com/NRC/M3/sib#any'

class BasicHandler:
    
    def __init__(self):
        print "handler inizializzato"
        pass

    def handle(self, added, removed):
        
        print "New results: " + str(len(added))
        for i in added:
            print added

        print "Old results: " + str(len(removed))
        for i in removed:
            print removed


# class Triple
class Triple:
    
    def __init__(self, s, p, o):
        
        # init
        self.s = None
        self.p = None
        self.o = None
        self.s_type = None
        self.p_type = None
        self.o_type = None

        # setting the subject
        if s:
            self.s = s
            if s.__class__.__name__ == "URIRef":
                self.s_type = "uri"
            elif s.__class__.__name__ == "BNode":
                self.s_type = "bnode"
        else:
            self.s = URIRef(SIB_ANY_URI)
            self.s_type = "URIRef"
                
        # setting the predicate
        if p:
            self.p = p
            self.p_type = "uri"
        else:
            self.p = URIRef(SIB_ANY_URI)
            self.p_type = "URIRef"
        
        # setting the object
        if o:
            self.o = o
            if o.__class__.__name__ == "URIRef":
                self.o_type = "uri"
            elif o.__class__.__name__ == "BNode":
                self.o_type = "bnode"
            elif o.__class__.__name__ == "Literal":
                self.o_type = "literal"
        else:
            self.o = URIRef(SIB_ANY_URI)
            self.o_type = "URIRef"
            
    def get_subject(self):
        return self.s.__str__()
    
    def get_predicate(self):
        return self.p.__str__()

    def get_object(self):
        return self.o.__str__()


# class JSON_kpi
class KP:

    ########################################################
    #
    # __init__
    #
    ########################################################

    def __init__(self, sib_host, sib_port, space_id, debug):
        """Constructor for the JSON_kpi class"""

        # reading parameters
        self.sib_host = sib_host
        self.sib_port = sib_port
        self.space_id = space_id
        self.debug = debug

        # initializing attributes
        self.transaction_id = 0
        self.node_id = str(uuid.uuid4())
        self.subscriptions = {}


    ########################################################
    #
    # join
    #
    ########################################################

    def join(self):
        
        # build a message
        msg_dict = {
            "tt" : "JOIN",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id            
        }

        # increment the transaction_id
        self.transaction_id += 1

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # leave
    #
    ########################################################

    def leave(self):
        
        # build a message
        msg_dict = {
            "tt" : "LEAVE",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id            
        }

        # increment the transaction_id
        self.transaction_id += 1

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # insert
    #
    ########################################################

    def insert(self, triple_list):
        """Inserts a list of triples"""
        
        # build the data structure
        ts = map(self.triple_formatter, triple_list)

        # build a message
        msg_dict = {
            "tt" : "INSERT",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "tl" : ts
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        msg = json.dumps(msg_dict)
        s.send(msg)
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # remove
    #
    ########################################################

    def remove(self, triple_list):
        """Removes a list of triples"""
        
        # build the data structure
        ts = []
        for triple in triple_list:
            t = {}
            t["s"] = triple.get_subject()
            t["p"] = triple.get_predicate()
            t["o"] = triple.get_object()
            t["ot"] = triple.o_type
            ts.append(t)

        # build a message
        msg_dict = {
            "tt" : "REMOVE",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "tl" : ts
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # update rdf
    #
    ########################################################

    def update_rdf(self, added_triple_list, removed_triple_list):
        """Updates a list of triples"""
        
        # build the data structure
        ats = []
        for triple in added_triple_list:
            t = {}
            t["s"] = triple.get_subject()
            t["p"] = triple.get_predicate()
            t["o"] = triple.get_object()
            t["ot"] = triple.o_type
            ats.append(t)

        # build the data structure
        rts = []
        for triple in removed_triple_list:
            t = {}
            t["s"] = triple.get_subject()
            t["p"] = triple.get_predicate()
            t["o"] = triple.get_object()
            t["ot"] = triple.o_type
            rts.append(t)

        # build a message
        msg_dict = {
            "tt" : "UPDATE",
            "mt" : "REQUEST",
            "enc": "rdf",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "atl" : ats,
            "rtl" : rts
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # update sparql
    #
    ########################################################

    def update_sparql(self, update_text):
        """Updates a list of triples"""
        
        # build a message
        msg_dict = {
            "tt" : "UPDATE",
            "mt" : "REQUEST",
            "enc": "SPARQL",
            "tid": self.transaction_id,
            "sid": self.space_id,
            "nid": self.node_id,
            "ut" : update_text
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    ########################################################
    #
    # query rdf
    #
    ########################################################

    def query_rdf(self, triple_list):
        """Performs an RDF query"""
        
        # build the data structure
        ts = map(self.triple_formatter, triple_list)

        # build a message
        msg_dict = {
            "tt" : "QUERY",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "enc" : "rdf",
            "tl" : ts
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # build the data structure to be returned
        results = []
        for triple in reply_dict["results"]:

            subj = pred = obj = None
            
            # determine the subject
            if triple["subject"]["type"] == "URIRef":
                subj = URIRef(triple["subject"]["value"])
            elif triple["subject"]["type"] == "BNode":
                subj = BNode(triple["subject"]["value"])

            # determine the predicate
            pred = URIRef(triple["predicate"]["value"])

            # determine the object
            if triple["object"]["type"] == "URIRef":
                obj = URIRef(triple["object"]["value"])
            elif triple["object"]["type"] == "BNode":
                obj = BNode(triple["object"]["value"])
            else:
                obj = Literal(triple["object"]["value"])
                
            # add the result to the list
            results.append(Triple(subj, pred, obj))

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True, results
        else:
            return False, None


    ########################################################
    #
    # query sparql
    #
    ########################################################
    
    def query_sparql(self, query_text):
        """Performs a SPARQL query"""

        # check if it is a select / ask - currently the only supported 
        # pay attention: fyzz is not reliable! -- see SP2B
        try:
            fyzz_parsed = parse(query_text)            
            if not(fyzz_parsed.type.lower() in ["select", "ask"]):
                return False, None
        except:
            pass

        # build a message
        msg_dict = {
            "tt" : "QUERY",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "enc" : "sparql",
            "qt" : query_text
        }

        # increment the transaction_id
        self.transaction_id += 1

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply
        reply = ""
        msg_check = False
        while not msg_check:
            
            # receive a chunk
            reply = reply + s.recv(4096)

            # parse the reply
            try:                
                reply_dict = json.loads(reply)
                msg_check = True
            except:
                # message incomplete
                pass
        
        # close the connection
        s.close()

        # if it is a select
        if reply_dict["qt"].lower() == "select":
            res_list = reply_dict["results"]
            
        # if it is an ask
        elif reply_dict["qt"].lower() == "ask":            
            res_list = [reply_dict["results"]]

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True, res_list
        else:
            return False, None


    ########################################################
    #
    # subscribe rdf
    #
    ########################################################

    def subscribe_rdf(self, triple_list, handlerClass):
        """Performs an RDF subscription"""
        
        # build the data structure
        ts = map(self.triple_formatter, triple_list)

        # build a message
        msg_dict = {
            "tt" : "SUBSCRIBE",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "enc" : "rdf",
            "tl" : ts
        }

        # increment the transaction_id
        self.transaction_id += 1            

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply 
        complete_reply = ""
        complete = False
        while not complete:
            reply = s.recv(4096)
            complete_reply = complete_reply + reply
            
            try:
                # parse the reply
                reply_dict = json.loads(complete_reply)
                complete = True
            except Exception as e:
                # uncomplete message
                pass

        # build the data structure to be returned
        results = []
        for triple in reply_dict["results"]:

            subj = pred = obj = None
            
            # determine the subject
            if triple["subject"]["type"] == "URIRef":
                subj = URIRef(triple["subject"]["value"])
            elif triple["subject"]["type"] == "BNode":
                subj = BNode(triple["subject"]["value"])

            # determine the predicate
            pred = URIRef(triple["predicate"]["value"])

            # determine the object
            if triple["object"]["type"] == "URIRef":
                obj = URIRef(triple["object"]["value"])
            elif triple["object"]["type"] == "BNode":
                obj = BNode(triple["object"]["value"])
            else:
                obj = Literal(triple["object"]["value"])
                
            # add the result to the list
            results.append(Triple(subj, pred, obj))

        # return
        if reply_dict["code"].lower() == "m3:success":

            # spawn a thread
            t = threading.Thread(target = self.indication_handler, args = (s, handlerClass,))
            t.start()

            # add the thread to a proper structure
            self.subscriptions[reply_dict["subid"]] = {}
            self.subscriptions[reply_dict["subid"]]["thread"] = t
            self.subscriptions[reply_dict["subid"]]["socket"] = s

            return True, reply_dict["subid"], results
        else:
            return False, None, None


    ########################################################
    #
    # subscribe sparql
    #
    ########################################################
    
    def subscribe_sparql(self, query_text, handlerClass):
        """Performs a SPARQL query"""

        # check if it is a select - currently the only supported for subscriptions
        # pay attention: fyzz is not reliable! -- see SP2B
        try:
            fyzz_parsed = parse(query_text)            
            if fyzz_parsed.type.lower() != "select":
                return False, None, None
        except:
            pass
        
        # build a message
        msg_dict = {
            "tt" : "SUBSCRIBE",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "enc" : "sparql",
            "qt" : query_text
        }

        # increment the transaction_id
        self.transaction_id += 1

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply 
        complete_reply = ""
        complete = False
        while not complete:
            reply = s.recv(4096)
            complete_reply = complete_reply + reply
            
            try:
                # parse the reply
                reply_dict = json.loads(complete_reply)
                complete = True
            except Exception as e:
                # uncomplete message
                pass

        res_list = [reply_dict["results"]]
    
        # return
        if reply_dict["code"].lower() == "m3:success":

            # spawn a thread
            t = threading.Thread(target = self.indication_handler, args = (s, handlerClass,))
            t.start()

            # add the thread to a proper structure
            self.subscriptions[reply_dict["subid"]] = {}
            self.subscriptions[reply_dict["subid"]]["thread"] = t
            self.subscriptions[reply_dict["subid"]]["socket"] = s

            # return
            return True, reply_dict["subid"], res_list

        else:
            return False, None, None


    ########################################################
    #
    # unsubscribe
    #
    ########################################################

    def unsubscribe(self, sub_id):
        """Unsubscription"""

        # build a message
        msg_dict = {
            "tt" : "UNSUBSCRIBE",
            "mt" : "REQUEST",
            "tid" : self.transaction_id,
            "sid" : self.space_id,
            "nid" : self.node_id,
            "subid" : sub_id
        }

        # increment the transaction_id
        self.transaction_id += 1

        # send the request
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.sib_host, self.sib_port))
        s.send(json.dumps(msg_dict))
        s.send("\n")

        #  wait for the reply 
        complete_reply = ""
        complete = False
        while not complete:
            reply = s.recv(4096)
            complete_reply = complete_reply + reply
            
            try:
                # parse the reply
                reply_dict = json.loads(complete_reply)
                complete = True
            except Exception as e:
                # uncomplete message
                pass

        # close the subscription socket
        sub = self.subscriptions[sub_id]
        sub["socket"].close()
        del sub["socket"]

        # return
        if reply_dict["code"].lower() == "m3:success":
            return True
        else:
            return False


    # indication handler
    def indication_handler(self, socket, handlerClass):
    
        # initialize the handler
        if handlerClass:
            handler_object = handlerClass()

        # initialize the needed variables
        data = ""

        # read from the socket
        while True:
                    
            try:
                time.sleep(1)
                data += socket.recv(4096)
                if len(data.strip()) > 0:

                    # parse the reply
                    try:                
                        # parse the message
                        reply_dict = json.loads(data)

                        # if the message is complete the exception is not thrown
                        # so we can proceed to empty the data variable
                        # since we already parsed the indication
                        data = ""

                    except:
                        # message incomplete
                        pass

                    # call the handler if an handler class has been specified
                    if handlerClass:
                        handler_object.handle(reply_dict["new_results"], reply_dict["old_results"])

            except Exception as e:
                break
                

    def triple_formatter(self, triple):

        t = {}
        t["s"] = triple.get_subject()
        t["p"] = triple.get_predicate()
        t["o"] = triple.get_object()
        t["ot"] = triple.o_type
        return t
