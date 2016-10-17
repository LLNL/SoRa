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
import numpy
import sys
import random

from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp
import sr_factories

from globalData import *
import sr_factories

#Chooses amoung a set of mutators to provide ONE mutation.  So mutation probabilities must add to <= 1.
#The configuration should be of the form:
#  "mutators" : {     #what mutators points to is what gets passed in from the mutationFactory
#        "type" : "multiMutOr",
#        "submutators" : [
#          {
#            "type" : "mutUniform",
#            "prob" : 0.3,
#          },
#          {
#            "type" : "mutShrink",
#            "prob" : 0.1,
#          },
#          {
#            "type" : "mutEphemeral",
#            "prob" : 0.6,
#            "mode" : "one"
#          }
#
#        ]
#  } ,

class multiMutOr:
    
    def __init__(self, config, toolbox, pset):
        self.mutators = []
        self.probabilities = []
        currentProbability = 0.0
        for entry in config["submutators"]:
            self.mutators.append(sr_factories.mutationFactory(entry, toolbox, pset)) #returns (mutator, kwargs)
            currentProbability += entry["prob"] #Each probability is greater than the last, so .3, .1, .6 -> .3, .4, 1.0 
            self.probabilities.append(currentProbability)
        if(currentProbability > 1.0):
            raise ValueError("multiMutOr probabilities must add to <= 1.0.")

        setattr(self, "__name__", "multiMutOr")
    
    def __call__(self, individual):                       
        randval = random.uniform(0,1)
        for ii in range(0, len(self.probabilities)):
            if(randval <= self.probabilities[ii]):
                (mutator, kwargs) = self.mutators[ii]
                new_ind = mutator(individual, **kwargs)
                return new_ind
        return individual
