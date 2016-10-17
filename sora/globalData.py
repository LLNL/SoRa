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
# There are some variables that required in multiple Symbolic Regression files.
# Define those here.
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
from deap import gp



#Try global toolbox
toolbox = base.Toolbox()
