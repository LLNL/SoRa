# SoRa: Symbolic Regression Code
Jim Leek
leek2@llnl.gov

## Overview

Symbolic Regression (SR) is a genetic programming algorithm for
finding mathematical functions that match a given set of data.  It
works by evolving an approximation function from a set of primitives.
This makes it able to discover the form of the function, in addition
to it's coefficients.  It has even been shown to be able to discover 
natural physical laws from experimental data [^1].

Given that SR is one of the biggest success stories in genetic
programming, it's surprising that there doesn't seem to be an
easy-to-use, open-source SR program available.  

SoRa attempts to fill that gap.  With SoRa any user should easily
be able to provide experimental data and write a simple configuration
file such that SoRa can find a set of good mathematical functions to
match the data.

### Using SoRa

##### 1. Requirements

  ###### SoRa requires:
  * Python 2.7.5 - 2.7.11.  SoRa doesn't currently support Python 3.

  * DEAP 1.1.0 (or newer).  Distributed Evolutionary Algorithms in
Python is the Genetic Programming framework SoRa is built around.
In many ways SoRa is just a front-end for DEAP. Get DEAP at
https://github.com/DEAP/deap.

  * numpy 1.9.2 (or newer):  Numpy is mostly used to speed up function
evaluation.

  ###### SoRa optional libraries:
  * SymPy: Symbolic Python is a symbolic mathematics library for
python.  Currently SoRa only uses it to simplify and pretty print
the functions that come out of the evolution.  Without it the output
is a bit uglier:
      * Without SymPy: mul(0.234, mul(X, X)
      * With SymPy   : 0.234 * X**2
  
  * mpi4py:  mpi4py is an MPI (Message Passing Interface) python
library.  It is used to handle multiple islands (demes) for greater
parallelism. 

##### 2. Running SoRa

###### 2a. Command Line Arguments
  
   
   SoRa is mostly configured by a JSON configuration file, but there
are also some important command line options:

usage: sora.py [options] configFile

Options:
  * -h, --help            show this help message and exit
  * -i INPUTFILE, --input-file=INPUTFILE
*The name of the input file*
  * -t NUMTHREADS, --num-threads=NUMTHREADS
*The number of threads (actually processes) to use for evaluation*
  * -p PRINTLEVEL, --print-level=PRINTLEVEL
*Print level defines the verbosity of the output.  Lower numbers give less output.  
0: Errors and hall of fame only  
1: Warning and Errors  
2: Errors, Warnings, and generational statistics  
3: Info  
4: High Info  
5: All debugging output*
  * -r, --all-ranks-print  
*All Ranks Print describes how the printlevel is applied on different ranks.  By default only rank 0 outputs anything.* 
  * -c LOADCHECKPOINT, --load-checkpoint=LOADCHECKPOINT
To restart a run pass the checkpoint file basename to load.  The Resulting filename will be "<name>.<rank>.check".
For example "TF.0.check".  All ranks that find a checkpoint file will load it, otherwise they
will generate a new population.


###### 2b. Configuration File

SoRa is primarily configured with a JSON configuration file.
If a configuration item has an oddly named argument, it probably
matches a named argument in DEAP.  See:
https://deap.readthedocs.io/en/master. 

  You can find example configuration files in the test_sr directory.
test_sr/HARM2Dconfig.json the data is sin(x^2 + y^2)
so, unlike my original testing data, a correct answer is possible. 
Occasionally I run and it actually finds that answer. 
Most of the time it comes back with some complicated nonsense. 

   Below is the default configuration file.  Most of the items in the
configuration file have defaults, which, amounts more or less to the
below.  Each item and section will get a more complete explanation
further on in the documentation.  Also note that the hash (#) comments
are not allowed in actual JSON files, so you would have to remove them
to actually run the file below.
```
{
  "infile"            : "foo",  #The base input filename
  "infileExtension"   : "dat",  #The input filename extension. foo.dat
  "inVars"   : [ "x" ],         #The axis variables
  "targetVar" : "target",       #The variable SoRa is trying to match
  "seed"   : 0,                 #Random Seed
  "depthLimit" : 17,            #Maximum depth of any function 
  "prettyPrint" : true,         #Use SymPy to pretty print functions
  "errorfunc": "avgAbsErrorSquared", #Error function guides evolution     
  "primitives" : ["add", "sub", #The primitives to make functions 
                  "mul", "div", #out of.  No defaults!
                  "neg", "sqrt"],
  "HallOfFame" : {              #Type of Hall Of Fame to use
        "type" : "pareto"       
  }, 
  "select" : [                  #Selection algorithm and args
        { 
        "type" : "selTournament",
        "tournsize" : 4
        } ],
  "expr"   : { "type" : "genHalfAndHalf",  #Initial function generation
               "min_" : 1,
               "max_" : 4
             },
  "expr_mut": { "type" : "genHalfAndHalf",  #Mutation expressions
               "min_" : 0,
               "max_" : 3
             },

  "islands" : {                 #Control of islands and migration
    "migrationFreq" : 50,
    "numMigrants" : 10,
    "emmigrantSelect"     : [ { 
        "type" : "selRandom"
        } ],
    "NOreplacementSelect" : [ { "type" : "selWorst" } ]
  },
  "algo"   : {                  #Evolution arguments and configuration
    "type" : "eaMuCommaLambda",
    "initialPopulationSize" : 400,
    "stopFrequency"  : 100,     #How often to stop and migrate/checkpoint
    "numGenerations" : 400,     #How many generation to run for
    "populationSize" : 400,     #Population to select each generation
    "children" : 600,           #Children generated per generation
    "cxpb"     : 0.7,           #Crossover probability
    "mutpb"    : 0.2            #Mutation probability
  },
  "mate"     : "cxOnePoint",    #Crossover algorithm
  "mutator"  : {                #mutation operation and args
    "type" : "mutUniform",
  },
  "checkpoints" : {             #Checkpointing configuration
     "filenamebase" : "None",   #If no filename, don't write checkpoints
     "allRanks"     : false,    #If false only rank 0 checkpoints
     "frequency"    : 100       #Checkpoint every 100 generations
  },
  "constants"  : [ {            #How to generate constants
        "type" : "uniform",     #A uniform distribution (-3,3)
        "min"  : -3,
        "max"  : 3
        } ] 

}
```
###### 2c. Data file

  SoRa allows two datafile formats.  Comma Seperated Values format (CSV) and ASCII column format (AKA "dat" format).  

  2c.1: CSV format. 
     If "infileExtension" : "csv" in the configuration file, then
SoRa attempts to read the file as a CSV.  CSV is a standard
spreadsheet format.  SoRa sees a CSV file as a set of columns, where
the first value in each column is the name of the column, then every
other value in the column should be a double.  Comments are not
allowed. 

This example has 3 columns:

temp,rho,SabsErr
1.000000000000000E-06,1.000000000000000E-09,-9.215922916587857E-02
1.000000000000000E-06,1.467800000000000E-09,-9.215925486108226E-02
1.000000000000000E-06,2.154430000000000E-09,-9.215929362427140E-02
1.000000000000000E-06,3.162280000000000E-09,-9.215935277990283E-02

This comes from a 2D function SabsErr(temp,rho).  As you can see,
the first column is named temp, the second rho, and the third
SabsErr.  In the config file you would have this:

  "infile"            : "foo",
  "infileExtension"   : "csv",
  "inVars"    : [ "temp", "rho" ],
  "targetVar" : "SabsErr",      

  2c.2: DAT format.
      DAT is a white space separated ASCII data column format.
Unfortunately it is not nearly as standardized as CSV format, but
variations of it are commonly used.
      Currently SoRa assumes DAT format if the infileExtension is
NOT .csv.  So: .dat, .in, .foo, etc. will all result in SoRa trying
to read DAT format.
      DAT as implemented by SoRa allows # at the beginning of a
line to designate a comment.  Aside from that it is very similar to
CSV, but with white space separators instead of commas.  The first row
is expected to be the column variable names.  Like this:

\# Experimental cold energy data 7.2003
T 	rho  	E 	S 	
9.999999999999999E-10 	1.000000000000000E-15 	0.000000000000000E+00 	5.136477167200000E-02 	
9.999999999999999E-10 	1.122018000000000E-15 	0.000000000000000E+00 	5.950234464700000E-02 	
9.999999999999999E-10 	2.818383000000000E-15 	0.000000000000000E+00 	5.457897012000000E-02 	
9.999999999999999E-10 	7.079458000000000E-15 	0.000000000000000E+00 	6.013146606200000E-02 

And in the config file:

  "infile"            : "foo",
  "infileExtension"   : "dat",
  "inVars"    : [ "T", "rho" ],
  "targetVar" : "E",      
        
Note that this configuration will ignore the S column
completely!  SoRa will only try to match the function E(T,rho).

###### 2d. Actually launching a run:

  If you look in the test directory, there are multiple tests ready to
go.  Let's try HARMconfig.json, which uses the HARM-GP algorithm, the
best in DEAP for symbolic regression.

  2d.1: A simple serial run:
     From the test directory:
        ../sora.py HARM2Dconfig.json
```
                           fitness                      size       
                -----------------------------   -------------------
gen     nevals  avg     max     min             avg     max     min
0       1000    -inf    0.89588 -1.79769e+308   5.263   28      2  
1       1000    -inf    0.885123        -1.79769e+308   4.138   28      1  
2       1000    -inf    0.885123        -1.79769e+308   3.894   20      1  
3       1000    -inf    0.885123        -1.79769e+308   3.497   19      1  
4       1000    -inf    0.896556        -1.79769e+308   2.857   21      1  
```
Well, the output could be prettier, but it looks OK, and you can see
that the best fitness is improving.  But the whole thing runs a bit
slowly.  

  2d.2: A multiprocessor run
        DEAP allows us to speed up the evaluation of each function by
parallelizing the evaluations across multiple processes with the
python multiprocessing library.  If our computer has 4 processors, we
can use them all with:

../sora.py -t3 HARM2Dconfig.json
```
                               fitness                          size       
                -------------------------------------   -------------------
gen     nevals  avg     max             min             avg     max     min
0       1000    -inf    0.885123        -1.79769e+308   4.879   25      2  
1       1000    -inf    0.885123        -1.79769e+308   3.994   20      2  
2       1000    -inf    0.890786        -1.79769e+308   3.721   23      1  
3       1000    -inf    0.908352        -1.79769e+308   3.278   18      1  
```
Well, that's going a lot faster.  Let's see how well the CPUS are
being used.
```
  PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND  
 89946 leek2     20   0  502m  32m 7488 S 62.5  0.1   0:04.42 python            
 89947 leek2     20   0  299m  22m 1944 R 42.0  0.0   0:02.46 python            
 89948 leek2     20   0  299m  22m 1936 R 42.0  0.0   0:02.47 python            
 89949 leek2     20   0  299m  22m 1936 R 41.3  0.0   0:02.45 python 
```
We can see that the main thread is using more CPU, but they are fairly
even.  

  2d.3: An MPI run
        However SoRa can allow us to do even more paralleism by
having MPI processes that run their own islands of evolution, where
the best candidates migrate between islands occasionally.  For this you
will need an "islands" section in your configuration file, which
HARM2Dconfig.json has.  So let's try it.  Our MPI cluster has 20
processors per node, so we can run a lot on one node.  We'll run 6
islands on one node, with 4 sub-evaluators.  (This is a bit of an
overload, but should be find.) 

srun -N1 -n6 ../doSR.py -t4 HARMTFconfig.json
```
  PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND           
 60746 leek2     20   0  528m  29m 8284 R 69.6  0.0   0:19.67 python            
 60742 leek2     20   0  528m  29m 8284 R 61.2  0.0   0:19.76 python            
 60747 leek2     20   0  528m  29m 8284 S 59.1  0.0   0:16.59 python            
 60744 leek2     20   0  528m  29m 8288 R 57.0  0.0   0:19.77 python            
 60743 leek2     20   0  529m  30m 8284 R 54.9  0.0   0:20.36 python            
 60745 leek2     20   0  528m  29m 8284 S 52.7  0.0   0:16.15 python            
 60869 leek2     20   0  325m  18m 1948 R 46.4  0.0   0:08.20 python            
 60866 leek2     20   0  325m  18m 1948 S 44.3  0.0   0:06.59 python            
```

-----
That's all the basics of doing a SoRa run.  

##### 3. Reference section

  SoRa has a lot of options.  This section has documentation on each
major section and the choices therein.  

###### 3a. Input file arguments
   
  "infile"            : "foo",
  "infileExtension"   : "dat",

<<<<<<< HEAD:sr/README.rst
  This will cause SoRa to look for a file named foo.dat.  Which will
assume ASCII white-space seperated column (DAT) format.  Any extension
=======
This will cause SaRang to look for a file named foo.dat.  Which will
assume ASCII white-space separated column (DAT) format.  Any extension
    >>>>>>> 7787acd2988272900e5edbf2fdf5b38000de494d:sr/README
other than CSV will be read as a DAT file.
  infileExtension may also be CSV, which will open the file as a
comma-separated value file.

###### 3b. Variable definition

  SoRa needs to know which column in the input file are important
variables.  There are two types of variables, the input variables
define the dimensionality of the problem, and that target variable is
the variable we're trying to match with the function.  So for a
function E(rho, T), we would use the following in the configuration file:

  "inVars"   : [ "rho", "T" ],
  "targetVar" : "E",

###### 3c. Random seed

  The user may supply a random seed, but that's not usually very
useful, and there isn't any way to set a different one for each
island, which would make multiple islands useless if you use just on
seed between them.  Defining the seed as "0" will result in the seed
being pulled from os.urandom() which should be purely random.

  "seed"   : 0,

###### 3d. Depth Limit

  DEAP includes a simple bloat control.  A simple "Depth Limit".  Each
function generated by symbolic regression is actually a parse tree
internally.  So, for example, 3 * (x + 4)  is:
  ```
     *
   /  \
 3    +
      / \
     x   4
```
This tree has a depth of "3".  The depth limit is enforced by throwing
away any individual that has a depth greater than the limit. Python
cannot handle a tree deeper than "90" because it hits a recursion
limit.   So the depth limit must be <= 90.  17 was originally
suggested by Koza.

  "depthLimit" : 30,

###### 3e. Pretty Print

  Currently this doesn't actually pretty print, it simplifies the
output of the individuals.  Internally all calls are functions, so:
3*(x+4) is internally represented as mul(3, add(x, 4)).  
  That can be difficult to read, so SymPy may be used to simplify it.
This also results in simplifying silly expressions like:
  add( 1, cos(0)) -> "2"

This is pretty useful, but it does require SymPy to be installed, and
it does cause the output to happen more slowly.
  
  "prettyPrint" : true,

###### 3f. Error Function
  
  "errorfunc": "rSquared",

The error function is probably the most important determinant of how
your symbolic regression goes.  It determines how well the function
fits the data, and therefore guides how the evolution progresses.
There are currently 7 choices:

  3f.1: rSquared
        RSquared is a measure of error vs the error from the mean
line.  (Wikipedia has an OK explanation.)  It resembles a percentage.
1.0 would be a perfect match.
        
Generally RSquared works well early on in the run, finding a
good coarse fit, but error can start to creep in later when .99994
still isn't as good a fit as you might like.

  3f.2: Absolute error:
        Absolute Error is simply the approximation function minus the
actual value, so: |(Value - Approx)|

There are three Absolute Error functions:
* avgAbsErrorSquared   : Average Absolute Error
* totalAbsErrorSquared : Total Absolute Error
* maxAbsErrorSquared   : Max absolute error

Average and Total give very similar evolutionary results.  Max
concentrates on just improving the currently worst point.  They have
their places, but I don't generally find these to work well for
symbolic regression as they concentrate very strongly on the points
of greatest magnitude.
        
These are minimization functions.  "0.0" would be perfect
approximation. 

  3f.3: Relative Error:
        Relative error incorporates the magnitude of the value being
matched into the calculation.  It is: |(Value - Approx) / Value)|.
This avoids the problem absolute error has with ignoring the points of
small magnitude.  All points have equal value to the result, but it
may actually make the tiny points TOO important.
        
        
WARNING: No zeros are allowed as values in relative error,
because that results in a divide by zero error.
        
There are three Relative Error functions:

* avgRelError : Average Relative Error
* totRelError : Total Relative Error
* maxRelError : Maximum Relative Error

maxRelativeError tends to not be very effective, because it
concentrates too much on improving the currently worst point, rather
than the overall fit.


###### 3g: Hall of Fame

  The Hall of Fame records the best functions from every generation.
There are two choices for a hall of fame, "hof" and "pareto."  

  3g.1: hof
        The hof Hall of Fame is very simple. It simply records the X
best functions generated.  So you have say how big you want the hall
of fame to be:  
```
        "HallOfFame" : {
                "type" : "hof",
                "size" : 10
        }
```
This type of hall of fame has the serious disadvantage that
you usually end up with X functions with only trivial differences.

  3g.2: Pareto
        A "Pareto Front" gives the dominant solutions according to
multiple dimensions of metrics.  In SoRa's case, that means "fitness
vs function size."  This provides a nice trade off between function
complexity and fitness.  This is the recommended type.  The pareto
front grows as large as necessary to hold all the "dominant" functions.
```
  "HallOfFame" : {
        "type" : "pareto"       
  }, 
```
```
       R Squared error     size    function
0 : (0.99981390380331492, 9.0) : 0.144495201928092*sqrt(T**2*atan(atan(T)))
1 : (0.99980927751092796, 8.0) : 0.144758631974528*T - 0.000266440720473395
2 : (0.99896867989805338, 3.0) : 0.140651393141985*T
3 : (0.88512316341642705, 2.0) : sqrt(T)
4 : (-5.7872080461152109e-09, 1.0) : 0.727431686266
```
###### 3h: Selection
  Selection defines how the next generations population is chosen.
Generally many more children will be generated per generation than are
allowed in the population.  Somehow SoRa must choose which of these
children will go on to breed.  That's defined by the selection
algorithm.  All of which currently come from DEAP, so you can learn
more about the choices in the DEAP documentation:
https://deap.readthedocs.io/en/master/api/tools.html#deap.tools.selTournament
All of the argument names to selection functions purposely match the
DEAP arguments, so DEAP really has the best documentation for this.

NOTE: One oddity is that in the config file, "select" takes an ARRAY
of selectors.  The reason is that you can define a different selector
for different islands.  This didn't turn out to be terribly useful,
but there it is.  See 3h.2 for an example

3h.1: selRandom: Select survivors randomly.  Makes an OK
replacement selector.

3h.2: selTournament: The most traditional selector.  Selects k
individuals randomly and holds a fitness tournament.  The winner
survives.  Works surprisingly well, despite lacking elitism.
```  
  "select" : [ 
        { 
        "type" : "selTournament",
        "tournsize" : 4
        } ],
 ```

3h.3: selBest: Selects the X individuals with best fitness.  This
discourages diversity too much.  Mostly used as a baseline for
experiments I think.

3h.4: selWorst: Selects the X individals with the worst fitness.
Only useful as a replacement selector, and not even great for that.  
    
3h.5: selRoulette: Selects k individuals via k spins of a
roulette, weighted by fitness somehow.  Doesn't work with minimization
problems or where fitness may be 0.

3h.6: selDoubleTournament: Holds 2 tournaments, one on fitness and
one on SIZE, preferring the smaller individuals.  This produces
minimization pressure on the size, which is good.  The arguments are a
bit odd though, look them up in the DEAP docs.
http://deap.readthedocs.io/en/master/api/tools.html#deap.tools.selDoubleTournament
```
  "select" : [ 
        { 
        "type" : "selDoubleTournament",
        "fitness_size" : 4, 
        "parsimony_size" : 1.4, 
        "fitness_first" : false
        } ],
 ```
3h.7: SPEA2
        SPEA2 is a multi-objective optimizer, which, in this case,
means it tries to select both for fitness and size. It works well, but
is slow, so using the HARM-GP algorithm seems to work better for
keeping size down.

3h.8: NSGA2
        Like SPEA2, NSGA2 is a multi-objective optimizer, which in
SoRa, tries to select both for fitness and size.  It's faster than
SPEA2, but has really big problems with maintaining diversity.  So the
results aren't very good.

3i: Initial function generation

  expr defines how the initial population of functions gets
generated.  (expr is short for "expression").  
  
  There are three choices for how to make the functions: genFull,
genGrow, and genHalfAndHalf.  All of them take "min_" and "max_" which
define the minimum and maximum initial tree depth.
```
"expr"   : { "type" : "genHalfAndHalf",
               "min_" : 1,
               "max_" : 4
             },
```
  Generally genHalfAndHalf is the best one, but if you want to learn
about the other choices see the DEAP documentation:
https://deap.readthedocs.io/en/master/api/tools.html#deap.gp.genFull 

###### 3j: Islands

  If you decide to use MPI to increase the parallelism of the
evolution, you need to have an islands section.  Each MPI process is
an island that has it's own population and evolution and what-not.
Then every so often, migration happens and a few selected individuals
move from rankX to rankX+1.  All of that is defined in the islands
section. 
  Here's an example:
```
  "islands" : {
    "migrationFreq" : 50,
    "numMigrants" : 10,
    "emmigrantSelect"     : [ { 
        "type" : "selRandom"
        } ],
    "replacementSelect" : [ { "type" : "selWorst" } ]
  },
```
  3j.1:  migrationFreq (migration frequency) defines how many
generations pass before migrants are sent on and immigrants received.
Note that this number is only checked which "stopFrequency" in the
algorithm section (3k) comes up. So, even if migrationFreq is 5, if
stopFrequency is 50, migrants will only move every 50 generations.

  3j.2: numMigrants.  The number of individuals to send and receive.

  3j.3: emmigrantSelect selects the individuals who are copied to the
next island.  Generally good migrants should be selected.
  
  3j.4: replacementSelect determines which individuals will be
eliminated to make room for the immigrants.  This is OPTIONAL. If it is
not defined, the immigrants simply replace the emigrants. 

###### 3k: Algorithms

  The Algorithm is the main loop of the evolution.  It determines
the size of the population, how many generations, how much crossover and
mutation occur, etc. There are current 3 algorithms supported in
SoRa (all from DEAP).

  3k.1: HARM-GP
        HARM-GP is an algorithm that runs a fairly normal evolution,
except that it tries to limit the size of the answers.  This is the
best algorithm for Symbolic Regression in my opinion.  The following
paper explains the details. [^2]
[^2]: Gardner, M. A., Gagn\E9, C., & Parizeau, M. (2015). Controlling code
growth by dynamically shaping the genotype size distribution. Genetic
Programming and Evolvable Machines, 16(4), 455-498. 
```
  "algo"   : {
    "type" : "harm",                #Algorithm name
    "initialPopulationSize" : 1000, #Size of the population
    "numGenerations" : 1000,        #Number of generations to run
    "stopFrequency"  : 50,          #stop and maybe checkpoint or migrate
    "cxpb"     : 0.7,               #cross over probability
    "mutpb"    : 0.3,               #mutation probability
    "alpha"    : 0.05,              #see the paper above
    "beta"     : 10,                #see the paper above
    "gamma"    : 0.25,              #see the paper above
    "rho"      : 0.9,               #see the paper above
    "nbrindsmodel" : -1,            #Hard to explain.  See DEAP docs.  
    "mincutoff" : 20                #The absolute minimum value for the cutoff point. 
  },
```
  3k.2: eaMuPlusLambda
        This is a very basic algorithm where crossover and mutation
are computed separately.  See the DEAP docs.  This one works well if
you don't want to use HARM.
```
  "algo"   : {
    "type" : "eaMuPlusLambda",
    "initialPopulationSize" : 1000, #Initial population size 
    "populationSize" : 200,         #Population normally
    "numGenerations" : 400,         #Number of generations to run
    "children" : 400,               #Children generated per gen
    "cxpb"     : 0.7,               #cross over probability
    "mutpb"    : 0.3                #mutation probability
  },
```
  3k.2: eaMuCommaLambda
        This is a very basic algorithm where only crossover OR mutation
may happen to an individual.  See the DEAP docs.
```
  "algo"   : {
    "type" : "eaMuCommaLambda",
    "initialPopulationSize" : 1000, #Initial population size 
    "populationSize" : 200,         #Population normally
    "numGenerations" : 400,         #Number of generations to run
    "children" : 400,               #Children generated per gen
    "cxpb"     : 0.7,               #cross over probability
    "mutpb"    : 0.3                #mutation probability
  },
```
###### 3l. mate
   Actually, currently there is only one use-able crossover operator in
DEAP, so this doesn't actually do anything.
```
  "mate"     : "cxOnePoint",
```
###### 3m. mutation
   DEAP comes with multiple mutators that will work with symbolic
regressions, and SoRa adds the "multiMutOr", which allows the user
to use multiple mutators.
   
   The selected mutator will only be called with the probability of
"mutpb" in the "algo" configuration block. In the above case, that's
on .3 or 30% of reproduction.

  3m.1: mutUniform
        Randomly select a point in the tree individual, then replaces
the subtree at that point as a root by the expression generated using
expr_mut from the config file.  This is the most powerful mutator.

  3m.2: mutNodeReplacement
        Replaces a randomly chosen primitive from individual by a
randomly chosen primitive with the same number of arguments from the
pset attribute of the individual. 

  3m.3: mutShrink
        Shrinks the individual by randomly choosing a branch and
replacing it with one of the branch~s arguments .

  3m.4: mutEphemeral 
        This operator works on the constants of the tree individual,
it replaces the chosen constant with a newly generated one.
        mutEphemeral takes one argument: "mode" all / one.
        In mode "one", it will change the value of one of the
individual ephemeral constants by calling its generator function. In
mode "all", it will change the value of all the ephemeral constants. 

          {
            "type" : "mutEphemeral",
            "mode" : "one"
          }

  3m.5: mutInsert
        Inserts a new branch at a random position in individual. The subtree at the chosen position is used as child node of the created subtree, in that way, it is really an insertion rather than a replacement. Note that the original subtree will become one of the children of the new primitive inserted, but not perforce the first (its position is randomly selected if the new primitive has more than one child).

  3m.6: multiMutOr
        Allows the user to select multiple mutators to use, each
having it's own probability.  These probability must sum <= 1.0.  If
they don't add to 1.0, the remaining probability simply results in
reproduction.
        
Note that this internal probability is applied AFTER the
overall mutpb found in the "algo" configuration block. 
        
So, if mutpb = .3, and multiMurOr has mutUniform with prob =
0.3, mutUniform will only be applied to .09 children generated per
generation. 
```
  "mutator" : { 
        "type" : "multiMutOr",
        "submutators" : [
          {
            "type" : "mutUniform",
            "prob" : 0.3
          },
          {
            "type" : "mutShrink",
            "prob" : 0.1
          },
          {
            "type" : "mutEphemeral",
            "prob" : 0.6,
            "mode" : "one"
          }
        ]
  },
```

###### 3n. constants
  
  In Symbolic Regression, constants in the function are call
"Ephemeral Constants.".  Constants are generated as terminals.  A
terminal is either a variable or a constant, so there are a lot of
constant generated.  
<<<<<<< HEAD:sr/README.rst
  SoRa allows the user to define distributation and ranges for
=======
  SaRang allows the user to define distribution and ranges for
     >>>>>>> 7787acd2988272900e5edbf2fdf5b38000de494d:sr/README
constant generation, and many can be defined.  For example, if you
think you may have one kind of constant around zero, and another kind
that an integer between (3,8), instead of generating a random number
between (0,8), it would probably be better two have two constants, one
(-1,1) and one randint (3,8).   
  
  Currently all of these come from DEAP, so see DEAP docs for more
information. 

Example:
```
   "constants"  : [ {
        "type" : "uniform",
        "min"  : -1,
        "max"  : 1
        },
        "type" : "randint",
        "min"  : 3,
        "max"  : 8
        },

 ] 
```
 3n.1: randint.  A random integer between (min, max)
 3n.2: uniform.  A random double from the uniform distribution (min,max)
 3n.3: normal.   A normal distribution, arguments: mu, sigma
 3n.4: gamma.    A gamma distribution, arguments: alpha, beta
 3n.5: constant  Just a value.  argument: value
 
 ### 4. DATA FILTERS / modifydata.py

When reading the input file data, SoRa can apply filters on the data
to make it easier to find a regression.  

However, while you can do that, it's fairly rare that a user would
want to.  More normally you want to modify the data first, then sanity
check it, THEN do the symbolic regression run.  That's what
modifydata.py is for, it just applies the data filters and outputs
them to a CSV or DAT file for reading by SoRa.

Example modifydata.py config file:

```
{
  "infile"            : "TF_xpthomas_March2013",
  "infileExtension"   : "dat",
  "outfile"           : "TF_xpthomas_March2013_noCold_gridReg",
  "outfileExtension"  : "csv",
  "filters"           : [
    { "type"  : "removeCold",
      "removeZero" : 0,
      "functions" : [ "E" ]
    },
    { "type"  : "gridRegular",
      "xAxisName" : "rho",
      "yAxisName" : "T",
      "xRemainingPoints" : 50,
      "yRemainingPoints" : 40
    }
  ]
}
```
As you can see, the modifydata.py configuration file is nearly the
same as the SoRa configuration, but SoRa doesn't require an
outfile or outfileExtension.

Either SoRa or modifydata.py can take the list of filters.  There
are currently 4 filters, with more to be added as required:

###### 4a. removeCold

removeCold solves a particular problem with equation of state data
sets.  In many EOS data-sets, there are two functions combined into
one.  One is a energy at 0K, or the "cold energy".  The other is the
thermal component, which goes up with temperature.  The cold energy
runs throughout the data set, but at the lowest possible temperature
in the data set, generally that's just the cold energy.
It can make some data sets significantly easier to match if the cold
term is removed.  So remove cold does that, such that the cold term is
subtracted from the whole data set.  Of course this means the lowest
temperature row becomes completely 0.
```
    { "type"  : "removeCold", #The type of the filter
      "removeZero" : false,   #Delete the lowest T, or leave it as zeros
      "functions" : [ "E" ]   #The column to act on in the data.
    },
```
###### 4b. fullRandom

fullRandom removes points from the data set completely randomly.  (For
DAT and CSV files, this is the equivalent of removing rows or lines
randomly.) 

fullRandom doesn't know anything about the grid or the underlying
data, so if there was some order to the points, it may not be
preserved.
```
    { "type"  : "fullRandom",
      "remainingPoints" : 50, #Leave 50 points 
    }
  
    { "type"  : "fullRandom",
      "removalFraction" : .4, #Leave 40% of the points
    }
```
###### 4c. gridRandom

gridRandom assumes a 2D grid of points.  So it needs to know which
column in the data is the X axis, and which is the Y axis.  Then it
eliminates whole rows and columns from the 2D data randomly.

The boundary points always remain though, the lowest and greatest X and Y values will remain to define the edge of the grid.  
```
    { "type"  : "gridRandom",
      "seed"      : 0,         #Optional argument, 0 gets seed from os.urandom
      "xAxisName" : "rho",     #The x Axis is called "rho"
      "yAxisName" : "T",       #The y Axis is called "T"
      "xRemainingPoints" : 50, #Leave 50 points in rho
      "yRemainingPoints" : 40  #Leave 40 points in T
    }
  
    { "type"  : "gridRandom",
      "xAxisName" : "rho",     #The x Axis is called "rho"
      "yAxisName" : "T",       #The y Axis is called "T"
      "xRemovalFraction" : .5, #Leave 50% of the points in rho
      "yRemovalFraction" : .4  #Leave 40% of the points in T
    }
```
###### 4d. gridRegular
gridRandom assumes a 2D grid of points.  So it needs to know which
column in the data is the X axis, and which is the Y axis.  Then it
eliminates whole rows and columns from the 2D data at regular
intervals.  It doesn't really understand the grid, so it doesn't
really keep the grid regular according whatever values are actually in
the axes, it just eliminates "every 5th X point" or something like that.

The boundary points always remain though, the lowest and greatest X and Y values will remain to define the edge of the grid.  
```
    { "type"  : "gridRegular",
      "xAxisName" : "rho",     #The x Axis is called "rho"
      "yAxisName" : "T",       #The y Axis is called "T"
      "xRemainingPoints" : 50, #Leave 50 points in rho
      "yRemainingPoints" : 40  #Leave 40 points in T
    }
    { "type"  : "gridRegular",
      "xAxisName" : "rho",     #The x Axis is called "rho"
      "yAxisName" : "T",       #The y Axis is called "T"
      "xRemovalFraction" : .5, #Leave 50% of the points in rho
      "yRemovalFraction" : .4  #Leave 40% of the points in T
    }
```
[^1]: [Schmidt, M., Lipson, H.
 Distilling Free-Form Natural Laws from Experimental Data.
 Science 324, 5923 (2009), 81-85.]
