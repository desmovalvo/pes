#!/usr/bin/python

# system-wide libraries
import sys
import getopt
import ConfigParser

# local libraries
from lib.output_helpers import *
from lib.update_test import *
from lib.kb_loader import *

# main
if __name__ == "__main__":

    # work variables
    config_file = "pes.conf"

    # instantiate an OutputHandler
    oh = OutputHelper("main", "blue")

    # read command line parameters
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:j:i:t:o:n:cf:", ["ssibs=", "jsibs=", "iterations=", "test=", "owlfiles=", "n3files=", "clean", "testfile="])
    except getopt.GetoptError as err:
        oh.p("__main__", "Wrong arguments", True)

    # initial attributes        
    owl_files = []
    n3_files = []
    sibs = []
    iterations = 1
    clean = False
    test = None
    test_config_file = None

    for opt, arg in opts:
        if opt in ("-s", "--ssibs"):
            for sib in arg.split("%"):
                sib_host = sib.split(":")[0]
                sib_port = int(sib.split(":")[1])
                sib_name = sib.split(":")[2]
                sibs.append({"host":sib_host, "port":sib_port, "name":sib_name, "protocol":"SSAP"}) 
        elif opt in ("-s", "--jsibs"):
            for sib in arg.split("%"):
                sib_host = arg.split(":")[0]
                sib_port = int(arg.split(":")[1])
                sib_name = arg.split(":")[2]
                sibs.append({"host":sib_host, "port":sib_port, "name":sib_name, "protocol":"JSSAP"}) 
        elif opt in ("-n", "--n3files"):
            for n3_file in arg.split("%"):
                n3_files.append(n3_file)
        elif opt in ("-o", "--owlfiles"):
            for owl_file in arg.split("%"):
                owl_files.append(owl_file)
        elif opt in ("-i", "--iterations"):
            iterations = arg
        elif opt in ("-c", "--clean"):
            clean = True
        elif opt in ("-t", "--test"):
            test = arg
        elif opt in ("-f", "--testfile"):
            test_config_file = arg
        else:
            assert False, "unhandled option"

    # read the configuration file
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(open(config_file))
    kbloader_config_file = config.get("files", "kbloader")

    # load the KB into the SIBs
    kbl = KBLoader(kbloader_config_file)
    for sib in sibs:

        # clean the SIBs
        if clean:
            kbl.clean_sib(sib["host"], sib["port"], sib["name"], sib["protocol"])

        # loading OWL files
        for owl_file in owl_files:
            success = kbl.load_owl_file(sib["host"], sib["port"], sib["name"], sib["protocol"], owl_file)
            if not success:
                sys.exit(255)

        # loading N3 files
        for n3_file in n3_files:
            success = kbl.load_n3_file(sib["host"], sib["port"], sib["name"], sib["protocol"], n3_file)
            if not success:
                sys.exit(255)

    # test
    if test:
        if test.upper() == "UPDATE":

            # debug print
            oh.p("__main__", "Running the UPDATE test")
            
            # create an instance of the UpdateTest class
            upd = UpdateTest(sibs, test_config_file)

            # run the test
            success, errcode = upd.run()
            if not success:
                oh.p("__main__", "Failed with message: %s" % errcode, True)
                sys.exit(255)

        elif test == "QUERY":
            pass
        elif test == "SUBSCRIPTION":
            pass


