#!/usr/bin/env python
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c)2016, Lawrence Livermore National Security, LLC. 
# Produced at the Lawrence Livermore National Laboratory. 
# Written by Jim Leek <leek2@llnl.gov>. 
# LLNL-CODE-704100. 
# All rights reserved.
#
# This file is part of SoRa.  For details, see https://github.com/llnl/SoRa.
# Please also read SoRa/LICENSE
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from dataReader import *
from dataFilters import *
import sys, os

def main():    
  parser = OptionParser()
  parser.usage = "This reads data from a file in a format determined by the extension. \n" + \
                 "It then optionally modifies the data, and writes it out to a new file.\n\n" + \
                 "This script takes 1 argument, json configuration file.\n\n" + \
                 "usage: %prog [options] configFile"

  add_options(parser)

  (options, args) = parser.parse_args()

  if(len(args) != 1):
    print parser.print_help()
    exit(2)

  configFilename = args[0]
  configfile = open(configFilename, "r")
  config = json.load(configfile)
  configfile.close()

  setConfigDefaults(config)

  #If the user passed in files on the command line, overwrite whatever was in the configuration file
  if(options.inputFile != None):
      (config["infile"], config["infileExtension"]) = os.path.splitext(options.inputFile)

  if(options.outputFile != None):
      (config["outfile"], config["outfileExtension"]) = os.path.splitext(options.outputFile)

  #splitext includes the "." on the extension, but most people don't.  So hack it off.
  if(config["infileExtension"][0] == "."):
      config["infileExtension"] = config["infileExtension"][1:]
  if(config["outfileExtension"][0] == "."):
      config["outfileExtension"] = config["outfileExtension"][1:]

  #read the input files into labels and data
  (labels, data) = readDataAndApplyFilters(config)

  #output the resulting file
  if(config["outfileExtension"].lower() == "csv"):
      writeCSVFile(".".join([config["outfile"], config["outfileExtension"]]), labels, data)
  else:
      writeSRFile(".".join([config["outfile"],  config["outfileExtension"]]), labels, data)
  
if __name__ == "__main__":
  main()
