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
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp

from globalData import *

#This is a basic error function that sums up all the absolute errors
#and squares them.  At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class totalAbsErrorSquared(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            sqerror = numpy.sum((func(*self.inVarValues) - self.targetVarValues)**2)

            if(numpy.isnan(sqerror)):
                return (sys.float_info.max,)
            return (sqerror,)
        except :
            return (sys.float_info.max,)


#This is a basic error function that finds the average of all the squared absolute errors
#At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class avgAbsErrorSquared(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            sqerror = numpy.average((func(*self.inVarValues) - self.targetVarValues)**2)
            if(numpy.isnan(sqerror)):
                return (sys.float_info.max,)
            return (sqerror,)
        except NameError as ne:
            print ne
            print ne.message
        except Exception as e:
            return (sys.float_info.max,)


#This is a basic error function that returns the maximum absolute error
# At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class maxAbsErrorSquared(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            error = numpy.max(func(*self.inVarValues) - self.targetVarValues)

            if(numpy.isnan(error)):
                return (sys.float_info.max,)
            return (error,)
        except :
            return (sys.float_info.max,)

#This is a basic error function that finds the average of all the relative errors.
#Note that your data set should not contain any 0 values.  That will cause a "divide by zero" error.
#At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class avgRelError(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable
        if(self.targetVarValues.__contains__(0)):
            raise ValueError("Relative error (avgRelError) cannot deal with 0's in the target data")

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            error = numpy.fabs(func(*self.inVarValues) - self.targetVarValues) / self.targetVarValues
            avgerror = numpy.average(error)
            
            if(numpy.isnan(avgerror)):
                return (sys.float_info.max,)
            return (avgerror,)
        except NameError as ne:
            print ne
            print ne.message
        except Exception as e:
            return (sys.float_info.max,)

#This is a basic error function that finds the total of all the relative errors.
#Note that your data set should not contain any 0 values.  That will cause a "divide by zero" error.
#At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class totRelError(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable
        if(self.targetVarValues.__contains__(0)):
            raise ValueError("Relative error (totRelError) cannot deal with 0's in the target data")

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            error = numpy.fabs(func(*self.inVarValues) - self.targetVarValues) /  self.targetVarValues
            sumerror = numpy.sum(error)
            
            if(numpy.isnan(sumerror)):
                return (sys.float_info.max,)
            return (sumerror,)
        except NameError as ne:
            print ne
            print ne.message
        except Exception as e:
            return (sys.float_info.max,)

#This is a basic error function that finds the maximum of all the relative errors.
#Note that your data set should not contain any 0 values.  That will cause a "divide by zero" error.
#At initialization time, it gets the data to compare against.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class maxRelError(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable
        if(self.targetVarValues.__contains__(0)):
            raise ValueError("Relative error (maxRelError) cannot deal with 0's in the target data")

    def weight(self):
        return (-1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            error = numpy.fabs((func(*self.inVarValues) - self.targetVarValues)) / self.targetVarValues
            maxerror = numpy.max(error)
            
            if(numpy.isnan(maxerror)):
                return (sys.float_info.max,)
            return (maxerror,)
        except NameError as ne:
            print ne
            print ne.message
        except Exception as e:
            return (sys.float_info.max,)

#R^2 is a common regression measurement to find how much variance is explained by the approximation.
#It works well early on in the calcuation, but loses percision has the approximation becomes close.
#
# The data is a list of lists, the labels give the names of interesting data.
# The config file defines which data lists are of use.
# All data lists are expected to be of equla length.  Repeated values are perfectly OK.
# The config file defines a set of "inVars" which are the input variables.  (e.g. rho, T)
# it also defines a single "targetVar" which is the array of function values.
class rSquared(object):
    
    def __init__(self, labels, data, config):
        self.inVarValues = []
        for inVar in config["inVars"]:
            inVarIdx = labels.index(inVar)
            self.inVarValues.append(numpy.array(data[inVarIdx]));  #Make a copy of each variable list

        targetVarIdx = labels.index(config["targetVar"])
        self.targetVarValues = numpy.array(data[targetVarIdx])     #Make a copy of the target variable
        self.meanTarget = numpy.average(self.targetVarValues)
        self.variance = sum((self.targetVarValues-self.meanTarget)**2)

    def weight(self):  #We want to maximize R^2
        return (1.0,)

    def __call__(self, individual):
        try:
            # Transform the tree expression in a callable function
            func = toolbox.compile(expr=individual)

            sumSqErrors = sum((func(*self.inVarValues) - self.targetVarValues)**2)
            r2 = 1 - (sumSqErrors/self.variance)
            
            if(numpy.isnan(r2)):
                return (sys.float_info.max,)
            return (r2,)
        except NameError as ne:
            print ne
            print ne.message
        except Exception as e:
            return (-sys.float_info.max,)



def errorFuncFactory(indict, labels, data, config):
    modtype = indict["errorfunc"]

    if(modtype.lower() == "rsquared"):
        return rSquared(labels, data, config)
    if(modtype.lower() == "avgabserrorsquared"):
        return avgAbsErrorSquared(labels, data, config)
    if(modtype.lower() == "totalabserrorsquared"):
        return totalAbsErrorSquared(labels, data, config)
    if(modtype.lower() == "maxabserrorsquared"):
        return maxAbsErrorSquared(labels, data, config)
    if(modtype.lower() == "avgrelerror"):
        return avgRelError(labels, data, config)
    if(modtype.lower() == "totrelerror"):
        return totRelError(labels, data, config)
    if(modtype.lower() == "maxrelerror"):
        return maxRelError(labels, data, config)

    return None

#The paretoErrorWrapper is just a wrapper that adds the other (size/complexity)
#dimension to the fitness function.  That way we can use the same error functions
#for both single and multi objective optimization
class paretoErrorWrapper:
    def __init__(self, singleErrorFunc):
        self.errorFunc = singleErrorFunc

    def weight(self):  #We want to maximize R^2
        singleWeight = self.errorFunc.weight()
        return singleWeight + (-1.0,)

    def __call__(self, individual):
        fitness = self.errorFunc(individual)
        complexity = len(individual)  #Still using the rough complexity measure for now
        return fitness + (complexity,)

def paretoErrorFuncFactory(indict, labels, data, config):
    singleErrorFunc = errorFuncFactory(indict, labels, data, config)
    return paretoErrorWrapper(singleErrorFunc)
