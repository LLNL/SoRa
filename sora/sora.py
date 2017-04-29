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

import sys, os
import operator
import math
import random
import multiprocessing
import numpy
import json
import cPickle
from optparse import OptionParser

import dataReader 
import dataFilters 
import sr_factories
import sr_migration
import sr_primitives
import printLogger

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

import sr_errorfuncs
from globalData import *

try:
  from mpi4py import MPI
except ImportError:
  pass



def main():

  try:
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
  except NameError:
    rank = 0
    size = 1
  #When searching around we can easily get bad functions that divide by 0
  #and whatnot.  In those cases we raise an exception, and throw away the
  #whole function.
  numpy.seterr(all='raise') 

  #Command Line arguments
  parser = OptionParser()
  parser.usage = "SoRa is a symbolic regression tool.  It reads data from a file an input file \n" + \
                 " (format determined by the extension), then attempts to find a mathematical \n" +\
                 "that fits the data.  It is able to handle multi-dimensional functions.\n\n" + \
                 "This script takes 1 argument, json configuration file.\n\n" + \
                 "usage: %prog [options] configFile"

  sr_factories.add_options(parser)

  (options, args) = parser.parse_args()  

  #Parse configuration file
  if(len(args) != 1):
    print args
    print parser.print_help()
    exit(2)
  configFilename = args[0]
  configfile = open(configFilename, "r")
  config = json.load(configfile)
  configfile.close()  
  config = sr_factories.setDefaults(config, sr_factories.defaultConfigData)

  #Set up logging and printing
  logger = printLogger.printLogging(config["logFilename"], options.printLevel,
                                      options.allRanksPrint, config["inVars"],
                                      config["prettyPrint"])
  
  #If the user passes input file information on the command line, it overrides the inputfile
  #information in the configuration file.  Do that here
  if(options.inputFile != None):
      (config["infile"], config["infileExtension"]) = os.path.splitext(options.inputFile)

  #splitext includes the "." on the extension, but most people don't.  So hack it off.
  if(config["infileExtension"][0] == "."):
      config["infileExtension"] = config["infileExtension"][1:]

  #Read the infile data 
  (labels, data) = dataFilters.readDataAndApplyFilters(config)

  #Set up the variables and primitives
  pset = gp.PrimitiveSet("MAIN", len(config["inVars"]))  #Pass in the number of inVars here
  sr_primitives.primitiveFactory(config["primitives"], pset)
  sr_factories.constantFactory(config["constants"], pset)

  #Rename the arguments to match the configuration file
  rename_kwargs = {}
  for ii in range(0, len(config["inVars"])):
      rename_kwargs["ARG%d" % ii] = config["inVars"][ii]
  pset.renameArguments(**rename_kwargs) 

  #Create and register the error / evaluation function
  hof = sr_factories.hofFactory(config)
  errorObj = None
  if(type(hof) == type(tools.ParetoFront())):
    errorObj =  sr_errorfuncs.paretoErrorFuncFactory(config, labels, data, config)
  else:
    errorObj =  sr_errorfuncs.errorFuncFactory(config, labels, data, config)
  toolbox.register("evaluate", errorObj)
  creator.create("FitnessMin", base.Fitness, weights=errorObj.weight()) 
  creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)

  #Setup basic stuff for symbolic regression, expression generator, etc.
  sr_factories.exprFactory("expr", config, toolbox, pset) 
  toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
  toolbox.register("population", tools.initRepeat, list, toolbox.individual)
  toolbox.register("compile", gp.compile, pset=pset)
  
  #Pick a selection algorithm
  sr_factories.selectionFactory("select", rank, config, toolbox)
  
  #Set up the mating system, it turns out there is only one that works for Primitive Tree
  toolbox.register("mate", gp.cxOnePoint)

  #TODO: Setting up the expression generator for the mutation, but that only makes sense
  #if we have picked the uniform mutator.  This needs to be optional somehow.
  sr_factories.exprFactory("expr_mut", config, toolbox, pset) 
  sr_factories.registerMutator(config, toolbox, pset)

  #Simple bloat control, set the depth limit (90 is the python limit, so it must be less <= 90)
  toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter("height"), max_value=config["depthLimit"]))  
  toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter("height"), max_value=config["depthLimit"]))

  #Turn on optional multiprocessing as passed on command line.
  if(options.numThreads > 1):
    pool = multiprocessing.Pool(processes=options.numThreads)
    toolbox.register("map", pool.map)
      
  if(config["seed"] == 0):  #a seed == 0 get the default seed os.urandom
    random.seed()
  else:
    random.seed(config["seed"])

  #Statistics setup
  stats_fit = tools.Statistics(lambda ind: ind.fitness.values[0])
  stats_size = tools.Statistics(len)
  mstats = tools.MultiStatistics(fitness=stats_fit, size=stats_size)
  mstats.register("avg", numpy.mean)
  #mstats.register("std", numpy.std)
  mstats.register("min", numpy.min)
  mstats.register("max", numpy.max)

  #Do we have MPI islands? If so, get the configuration for them
  islandConfig = {}
  if(config.has_key("islands")):
    islandConfig = config["islands"]
  islandConfig = sr_factories.setDefaults(islandConfig, sr_factories.islandsDefaults)

  sr_factories.selectionFactory("emmigrantSelect", rank, islandConfig, toolbox)
  sr_factories.selectionFactory("replacementSelect", rank, islandConfig, toolbox)

  #And get the checkpoint configuration before we start
  checkpointsConfig = {}
  if(config.has_key("checkpoints")):
    checkpointsConfig = config["checkpoints"]
  checkpointsConfig = sr_factories.setDefaults(checkpointsConfig, sr_factories.checkpointsDefaults)

  algoArgs = config["algo"]  #Just a shorter name because the algorithm configuration is used a lot
  algoArgs = sr_factories.registerAlgorithm(algoArgs, toolbox, mstats, hof,
                                    verbose=(options.printLevel >=2 and (rank == 0 or options.allRanksPrint)));

  #If the user passed in a command line argument to load a checkpoint, see if a
  #checkpoint exists for this rank.
  pop = None
  checkpointFilename = None
  if (options.loadCheckpoint != None):
    checkpointFilename = "%s.%d.pkl" % (options.loadCheckpoint, rank)
    if(not os.path.exists(checkpointFilename)):  #Make up the checkpoint filename, if it exists, we'll load it
      logger.printOut(2, "Was unable to find checkpoint file %s for rank %d" % (checkpointFilename, rank))
      checkpointFilename = None

  # If a checkpoint filename was recieved, and it exists for this node, load it.
  # Otherwise everything starts from scratch.
  if(checkpointFilename):
    logger.printOut(4,"Loading checkpoint file %s on rank %d" % (checkpointFilename, rank))
    with open(checkpointFilename, "r") as cp_file:
      cp = cPickle.load(cp_file)
    pop = cp["population"]
    hof = cp["halloffame"] #Will overwrite the old HoF, so, hopefully they are the same type...
    random.setstate(cp["rndstate"])
  else:
    # If no checkpoint file was found, make an initial random population
    pop = toolbox.population(n=algoArgs["initialPopulationSize"])


  logger.printOut(5, "Initial population on rank %d" % rank)
  logger.printPopulation(5, pop)


  #The replacement selection picks the individuals to be replaced by migrating immigrants.
  #If replacement select is 'None', the leaving emmigrants are replaced.
  #Unfortunately I can't register None in the toolbox,
  #so instead I have to catch an exception to check for no
  replaceSelect = None
  try:
    replaceSelect = toolbox.replacementSelect
  except AttributeError:
    pass

  #vvvvvvvvvvvvvvvvvvvvvvvvvvvvv Main Loop vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
  #Main Loop runs for "numGenerations" stopping every "stopFrequency" to see if something
  #needs to be done. The two things that can be done are migration or taking a checkpoint.
  migrationCounter = 0
  checkpointCounter = 0
  for ii in range(0, algoArgs["numGenerations"], algoArgs["stopFrequency"]):
    logger.printOut(3, "Starting Generation %d" % ii)
    logger.printOut(4, "Hall of Fame on rank: %d" % rank)
    logger.printPopulation(4,hof)

    toolbox.algorithm(pop)

    logger.printOut(5, "Population of rank: %d" % rank)
    logger.printPopulation(5, pop)


    #If the migration counter is over the migration freqency, it's time to migrate (if we have multiple islands)
    migrationCounter += algoArgs["stopFrequency"]
    if(migrationCounter >= islandConfig["migrationFreq"] and size > 1):  
      migrationCounter = 0
      sr_migration.MPIMigRing(comm, pop, islandConfig["numMigrants"], toolbox.emmigrantSelect, replaceSelect, logger)

    #If the checkpoint counter is over the checkpoint freqency, it's time to checkpoint
    checkpointCounter += algoArgs["stopFrequency"]
    if(checkpointsConfig["filenamebase"] and checkpointCounter >= checkpointsConfig["frequency"]):  
      checkpointCounter = 0
      cp = dict(population=pop, halloffame=hof, rndstate=random.getstate())
      with open("%s.%d.pkl" % (checkpointsConfig["filenamebase"], rank), "wb") as cp_file:
        cPickle.dump(cp, cp_file, 2)
  #^^^^^^^^^^^^^^^^ Main loop ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

  #vvvvvvvvvvvvvvvv Run is done, compile all Hall of Fames from all ranks vvvvvvvv
  #mpi4py doesn't allow gather for object, so I wrote my own gather
  if(size > 0):
    if(rank == 0):
      for ii in range(1,size):
        inpop = comm.recv(source=MPI.ANY_SOURCE)
        hof.update(inpop)
    else:
      comm.send(hof.items, dest=0)


  #Print out the final global Hall of Fame
  logger.printPopulation(0, hof)


if __name__ == "__main__":
    main()
