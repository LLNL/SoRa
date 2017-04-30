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
try:
    from mpi4py import MPI
    mpi = True
except ImportError:
    mpi = False
try:
    import sympy
except ImportError:
    pass

#This file contains the sympy code used for pretty printing equasions.
#It's in a seperate function to avoid polluting the namespace shared
#with the numpy math functions

class printLogging:

    def __init__(self, logFilename, printLevel, allRanksPrint, varslist, prettyPrint=True):
        """This class handles all the printing and logging of the run.
        All print statements come with a 'printLevel' that determines if they need to be printed
        or ignored. The printlevel corrosponds with:
            0: CRITICAL
            1: ERROR
            2: WARN
            3: INFO - Normal Output
            4: INFO - Extra Output
            5: DEBUG

        :param logFilename:   The filename to write the log to.  May be None
        :param printLevel:    How much output the user wants, see above
        :param allRanksPrint: Boolean, if true printing comes from all ranks, false, only from rank 0
        :param varslist:   A list of the variables in the run.  Usually pulled from config['inVars']
        :param varslist:   A bool, attempt sympy pretty printing or not
        """
        self.printLevel = printLevel
        self.allRanksPrint = allRanksPrint
        self.varslist = varslist
        self.prettyPrint = prettyPrint
        self.logFile = None
        if mpi:
            comm = MPI.COMM_WORLD
            self.rank = comm.Get_rank()
        else:
            self.rank = 0

        if(logFilename):
            self.logFile = open(logFilename, "w")

    def __del__(self):
        if(self.logFile):
            close(self.logFile)
        self.logFile = None

    def printOut(self, printLevel, outString):
        if(self.printLevel >= printLevel and (self.rank == 0 or self.allRanksPrint)):
            print outString

    def log(self, outString):
        if(self.logFile and (self.rank == 0 or self.allRanksPrint)):
            self.logFile.write(outString + "\n")

    def printLog(self, printLevel, outString):
        self.printOut(printLevel, outString)
        self.log(outString)
        

    def printPopulation(self, printLevel, population):
        """Print out a population of solutions for the symbolic regression.
        It attempts to 'pretty print' by using sympy to simplify the expression.
        If that fails it just prints what's there.
        
        Every expression is printed with its index in the population and fitness measurement.
        Example from a Hall of Fame:
        12 : (0.88512316341642705, 2.0) : sqrt(T)
        
        This is the 12th best expression, it has a fitness of .885 and a tree size of 2.
        The expression is 'sqrt(T)'
        
        :param population: The population in question.  May be a list or a Hall of Fame.
        :returns: None
        """
    
        if(self.printLevel >= printLevel and (self.rank == 0 or self.allRanksPrint)):
            print "population size: %d" % len(population)

            if(not sympy or not self.prettyPrint):  #simple case, no pretty printing
                for (idx, indiv) in enumerate(population):
                    print idx, ":", indiv.fitness, ":", indiv  

            else:
                #All the functions from symbreg_primitives must be represented here in a
                #way sympy can understand (I think having them here means if you don't have sympy
                #this cde will still work)


                from numpy import subtract as sub
                from numpy import multiply as mul
                from numpy import true_divide as div
                from numpy import negative as neg
                from numpy import add, square
                from sympy import sqrt
                from sympy import asin, acos, atan, atan2
                from sympy import sinh, cosh, tanh
                from sympy import asinh, acosh, atanh
                
                #Make sympy.symbols out of all the variables in the symbolic regression
                print self.varslist
                symlist = sympy.symbols(" ".join(self.varslist))
                if(not isinstance(symlist, tuple)): #Dumb workaround for symbols not returning a tuple if there is only one symbol
                    symlist = [symlist]
                print symlist
                for ii in range(0, len(self.varslist)):
                    varname = self.varslist[ii]
                    exec("%s = symlist[ii]" % varname)

                for (idx, indiv) in enumerate(population):
                    try:
                        exec("expr = %s" % str(indiv))
                        print idx, ":", indiv.fitness, ":", expr
                    except:   #Backup case if symbreg can't handle simplifing the expression for some reason
                        print idx, ":", indiv.fitness, ":", indiv


    def logPopulation(self, population):
        """Write the population to the log file.
        This version is just for debugging, so it doesn't bother with pretty printing.
        
        :param population: The population in question.  May be a list or a Hall of Fame.
        :returns: None
        """
        if(logFile and (self.rank == 0 or self.allRanksPrint)):
            logFile.write("Rank %d population size: %d" % (self.rank, len(population)))
            for (idx, indiv) in enumerate(population):
                logFile.write("%d: %s : %s" %( idx, str(indiv.fitness), str(indiv)))  
