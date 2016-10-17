import json
import random
from optparse import OptionParser
import dataReader

defaultData = { "infile"            : "foo",
                "infileExtension"   : "in",
                "outfile"           : "foo",
                "outfileExtension"  : "out",
                "filters"           : []
                }


def setConfigDefaults(indict):
    thisData = defaultData.copy()
    thisData.update(indict)

    return thisData
        

def add_options(op):
    """
    """
    assert(isinstance(op, OptionParser))

    # Paging
    op.add_option("-i", "--input-file", 
                  action="store_true", dest="inputFile", default=None,
                  help="The name of the input file")
    op.add_option("-o", "--output-file", 
                  action="store_false", dest="outputFile", default=None,
                  help="The name of the output file ")

def readDataAndApplyFilters(config):
    """ This is a helper function that does the main work of the dataFilters library
    in one place.  It takes a configuration dictionary, reads the file it points to, and applies any
    filters requested, and returns the data.


    :param config: A configuration dictionary. It MUST contain 'infile' and 'infileExtension' entries.
        it MAY contain a filters array, with entries like 'fullRandom'

    return : (labels, data):  Labels: The column headers. Data: The data in the read file, with any requested filters applied.
             Note that all data columns are full, uniques are not removed, even from the axis columns

    """

    if(config["infileExtension"].lower() == "csv"):
        (labels, data) = dataReader.readCSVFile(".".join([config["infile"], config["infileExtension"]]))
    else:
        (labels, data) = dataReader.readDatFileWithHeaders(".".join([config["infile"], config["infileExtension"]]))

    #apply the filters to input data
    filters = []
    for filterdict in config["filters"]:
        filters.append(modifierFactory(filterdict))

    for filterObj in filters:
        data = filterObj.apply(labels, data)

    return (labels, data)


#FullRandom takes removes points from the data completely randomly, as in, the resulting file will no longer be a full grid
#It takes arguments:
#seed:       The random seed to use.  0 will pull from os.urandom
#removalFraction: Defaults to 50%
#remainingPoints: An alternative to removal fraction.  Gives the number of points we should have left after removal.  <= 0 will go with removalFraction instead.

class fullRandom(object):

    def __init__(self, indict):
        indict = self.setDefaults(indict)
        self.seed = indict["seed"]
        self.removalFraction = indict["removalFraction"]
        self.remainingPoints = indict["remainingPoints"]

    def setDefaults(self, indict):
        thisData = { "type"  : "fullRandom",
                     "seed"  : 0,
                     "removalFraction" : 0.5,
                     "remainingPoints"  : 0
                     }
        thisData.update(indict)
        return thisData

    def apply(self, labels, data):
        print "Entering the fullRandom filter"
        outdata = list(data)  #copy the input data
        startNumPoints = len(outdata[0])
        endNumPoints = self.remainingPoints  #First figure out how many points we want to end with
        if(endNumPoints <= 0):
            endNumPoints = int(startNumPoints * self.removalFraction)
            
        if(startNumPoints <= endNumPoints):  #If we already have fewer points than that, just go back
            return outdata

        if(self.seed == 0):  #Default to os.urandom, unless the user set a seed
            random.seed()
        else:
            random.seed(self.seed)
            
        pointsToDelete = startNumPoints - endNumPoints
        for ii in range(0, pointsToDelete):
            pointToDelete = random.randint(0, startNumPoints - (ii + 1))
            for column in range(0,len(data)):
                outdata[column].__delitem__(pointToDelete)

        return outdata
        

#GridRandom removes grid points from the data completely randomly.  The result will be a grid, but not an even one
#It assumes a 2D grid, so it needs to know which variables are the axes
#It will not remove the grid boundry, so the lowest and highest X and Y will remain
#It takes arguments:
#seed:       The random seed to use.  0 will pull from os.urandom
#xAxisName:  The name of the X axis
#yAxisName:  The name of the Y axis
#xAxisRemovalFraction: The fraction of the X axis to remove. Defaults to 50%
#yAxisRemovalFraction: The fraction of the Y axis to remove. Defaults to 50%
#xAxisRemainingPoints: An alternative to removal fraction.  Gives the number of points we should have left after removal.  <= 0 will go with removalFraction instead.
#yAxisRemainingPoints: An alternative to removal fraction.  Gives the number of points we should have left after removal.  <= 0 will go with removalFraction instead.

class gridRandom(object):

    def __init__(self, indict):
        indict = self.setDefaults(indict)
        self.seed = indict["seed"]
        self.xAxisName = indict["xAxisName"]
        self.yAxisName = indict["yAxisName"]
        self.xRemovalFraction = indict["xRemovalFraction"]
        self.yRemovalFraction = indict["yRemovalFraction"]
        self.xRemainingPoints = indict["xRemainingPoints"]
        self.yRemainingPoints = indict["yRemainingPoints"]

    def setDefaults(self, indict):
        thisData = { "type"  : "gridRandom",
                     "seed"  : 0,
                     "xAxisName" : "rho",
                     "yAxisName" : "T",
                     "xRemovalFraction" : 0.5,
                     "yRemovalFraction" : 0.5,
                     "xRemainingPoints" : 0,
                     "yRemainingPoints" : 0
                     }
        thisData.update(indict)
        return thisData

    def apply(self, labels, data):
        print "Entering the gridRandom filter"
        if(self.seed == 0):  #Default to os.urandom, unless the user set a seed
            random.seed()
        else:
            random.seed(self.seed)

        #First we have to find the axes and make the unique so we can figure out what to cut.
        #We assume the axes are in acending order
        xAxisIdx = labels.index(self.xAxisName)
        yAxisIdx = labels.index(self.yAxisName)

        xAxis = dataReader.unique(list(data[xAxisIdx]))
        yAxis = dataReader.unique(list(data[yAxisIdx]))

        #Now that we have have x and y axes, we can randomly pare them down.
        startNumXPoints = len(xAxis)
        startNumYPoints = len(yAxis)
        endNumXPoints = self.xRemainingPoints  #figure out how many points we want to end with
        endNumYPoints = self.yRemainingPoints  
        if(endNumXPoints <= 0): #If user declared removalFraction instead, use that
            endNumXPoints = int(startNumXPoints * self.xRemovalFraction)
        if(endNumYPoints <= 0): 
            endNumYPoints = int(startNumYPoints * self.yRemovalFraction)

        #If we don't need to do anything, don't do anything.
        if(startNumXPoints <= endNumXPoints and startNumYPoints <= endNumYPoints): 
            return data

        #If we need to delete points, we'll do it my making a list of all the indexes.  Then we loop through
        #deleteing those index points at random.  Afterwords we can make a new data array that only has those indexes
        xPoints = range(1, len(xAxis)-1) #Don't delete the end points of the axes, we want those
        if(startNumXPoints > endNumXPoints):
            xNumPointsToDelete = startNumXPoints - endNumXPoints 
            for ii in range(0, xNumPointsToDelete):
                pointToDelete = random.randint(0, len(xPoints)-1)
                xPoints.__delitem__(pointToDelete)

        xPoints.insert(0,0)  #Stick the boundry points back on.
        xPoints.append(len(xAxis)-1)

        yPoints = range(1, len(yAxis)-1) #Don't delete the end points of the axes, we want those
        if(startNumYPoints > endNumYPoints):
            yNumPointsToDelete = startNumYPoints - endNumYPoints 
            for ii in range(0, yNumPointsToDelete):
                pointToDelete = random.randint(0, len(yPoints)-1)
                yPoints.__delitem__(pointToDelete)

        yPoints.insert(0,0)  #Stick the boundry points back on.
        yPoints.append(len(yAxis)-1)

        returnData = []
        for indata in data:  #Copy each column over into outdata, ignoring the points we don't want
            outdata = []
            for yy in yPoints:
                for xx in xPoints:
                    outdata.append(indata[yy*len(xAxis) + xx])  #I guess we have to assume it's in row-major order
            returnData.append(outdata)

        return returnData
        
#GridRegular removes grid points from the data at regular points.  The result will be the same grid, but missing grid points
#It assumes a 2D grid, so it needs to know which variables are the axes
#It will not remove the grid boundries, so the lowest and highest X and Y will remain
#The algorithm works by taking the removal fraction, and adding it at each point.  If the result > 1, the grid point is kept (and -1 taken from the sum), if < 1, the point is deleted
#Note that, due to the end points being kept, usually a slightly higher number of points will be kept than the removal fraction asks for.
#It takes arguments:
#seed:       The random seed to use.  0 will pull from os.urandom (Only used for
#startValue: start value determines how the algorithm gets started.  0 will all ways remove the first point.  1 will always keep it.  -1 will get a random float [0,1]
#xAxisName:  The name of the X axis
#yAxisName:  The name of the Y axis
#xAxisRemovalFraction: The fraction of the X axis to remove. Defaults to 50%
#yAxisRemovalFraction: The fraction of the Y axis to remove. Defaults to 50%
#xAxisRemainingPoints: An alternative to removal fraction.  Gives the number of points we should have left after removal.  <= 0 will go with removalFraction instead.
#yAxisRemainingPoints: An alternative to removal fraction.  Gives the number of points we should have left after removal.  <= 0 will go with removalFraction instead.
class gridRegular(object):

    def __init__(self, indict):
        indict = self.setDefaults(indict)
        self.seed = indict["seed"]
        self.startValue = indict["startValue"]
        self.xAxisName = indict["xAxisName"]
        self.yAxisName = indict["yAxisName"]
        self.xRemovalFraction = indict["xRemovalFraction"]
        self.yRemovalFraction = indict["yRemovalFraction"]
        self.xRemainingPoints = indict["xRemainingPoints"]
        self.yRemainingPoints = indict["yRemainingPoints"]
        

    def setDefaults(self, indict):
        thisData = { "type"  : "gridRegular",
                     "seed"  : 0,
                     "startValue" : -1,
                     "xAxisName" : "rho",
                     "yAxisName" : "T",
                     "xRemovalFraction" : 0.5,
                     "yRemovalFraction" : 0.5,
                     "xRemainingPoints" : 0,
                     "yRemainingPoints" : 0
                     }
        thisData.update(indict)
        return thisData

    def apply(self, labels, data):
        print "Entering the gridRegular filter"
        if(self.seed == 0):  #Default to os.urandom, unless the user set a seed
            random.seed()
        else:
            random.seed(self.seed)
        if(self.startValue < 0):
            self.startValue = random.uniform(0,1)

        #First we have to find the axes and make the unique so we can figure out what to cut.
        #We assume the axes are in acending order
        xAxisIdx = labels.index(self.xAxisName)
        yAxisIdx = labels.index(self.yAxisName)

        xAxis = dataReader.unique(list(data[xAxisIdx]))
        yAxis = dataReader.unique(list(data[yAxisIdx]))

        #Now that we have have x and y axes, we can use our algorithm to pare them down.
        startNumXPoints = len(xAxis)
        startNumYPoints = len(yAxis)

        #removal fraction is the default, and is used in the calculation.  But remaining points can override it.
        if(self.xRemainingPoints >= 3):
            self.xRemovalFraction =  float(self.xRemainingPoints-2) / float(startNumXPoints)
        if(self.yRemainingPoints >= 3):
            self.yRemovalFraction =  float(self.yRemainingPoints-2) / float(startNumYPoints)
            
        #If we don't need to do anything, don't do anything.
        if(self.xRemovalFraction >= 1 and self.yRemovalFraction >= 1): 
            return data

        #If we need to delete points, we'll do by making an array to hold the indexes to keep.
        #Then we walk though, copying points into the index array that we want to keep.
        xPoints = [] #Don't delete the end points of the axes, we want those
        runSum = self.startValue
        for ii in range(1, len(xAxis)-1):
            runSum += self.xRemovalFraction
            if(runSum >= 1.0):
                xPoints.append(ii)
                runSum -= 1
                
        xPoints.insert(0,0)  #Stick the boundry points back on.
        xPoints.append(len(xAxis)-1)

        yPoints = [] #Don't delete the end points of the axes, we want those
        runSum = self.startValue
        for ii in range(1, len(yAxis)-1):
            runSum += self.yRemovalFraction
            if(runSum >= 1.0):
                yPoints.append(ii)
                runSum -= 1
                
        yPoints.insert(0,0)  #Stick the boundry points back on.
        yPoints.append(len(yAxis)-1)


        returnData = []
        for indata in data:  #Copy each column over into outdata, ignoring the points we don't want
            outdata = []
            for yy in yPoints:
                for xx in xPoints:
                    outdata.append(indata[yy*len(xAxis) + xx])  #I guess we have to assume it's in row-major order
            returnData.append(outdata)

        return returnData

#RemoveCold subtracts the lowest temperature values from the rest of the grid.
#The result will be the same grid, but missing the cold term.
#It assumes a rho,T grid, so it needs to know which variables T and rho
#Assumes rho is the quickly varying axis.
#Unlike the other filters, this one actually edits data in place.
#It takes arguments:
#rhoAxisName:  The name of the rho axis
#TAxisName  :  The name of the T axis
#removeZero :  A boolean.  If it's false, the lowest isotherm will all be 0s, true, and the lowest isotherm will be deleted
#              This is a little dangerous, if you do this ALL functions will have their lowest isotherm deleted, whether they are in
#              the functions list or now.
#functions  :  The list of column names to remove the cold term from.  If it's an empty list, all will be done (except the rho and T axes of course.)
class removeCold(object):

    def __init__(self, indict):
        indict = self.setDefaults(indict)
        self.rhoAxisName = indict["rhoAxisName"]
        self.TAxisName = indict["TAxisName"]
        self.removeZero = False
        self.functions = indict["functions"]

    def setDefaults(self, indict):
        thisData = { "type"  : "removeCold",
                     "rhoAxisName" : "rho",
                     "TAxisName" : "T",
                     "removeZero" : 0,
                     "functions" : []
                     }
        thisData.update(indict)
        return thisData

    def apply(self, labels, data):
        print "Entering the removeCold filter"

        #First we have to find the axes and make them unique.
        #We assume the axes are in acending order
        rhoAxisIdx = labels.index(self.rhoAxisName)
        TAxisIdx = labels.index(self.TAxisName)

        rhoAxis = dataReader.unique(list(data[rhoAxisIdx]))
        TAxis = dataReader.unique(list(data[TAxisIdx]))

        if(len(self.functions) == 0):  #If the user wants us to do all the functions, set that up.
            for ii in range(0, len(labels)):
                if(ii == rhoAxisIdx or ii == TAxisIdx): #skip axes
                    continue
                self.functions.append(labels[ii])

        for funcname in self.functions:
            funcidx = labels.index(funcname)
            thisfunc = data[funcidx]
            coldterm = list(thisfunc[0:len(rhoAxis)])

            for yy in range(0,len(TAxis)):
                for xx in range(0,len(rhoAxis)):
                    thisfunc[yy*len(rhoAxis) + xx] -= coldterm[xx] #subtract off the cold term 

        if(self.removeZero):
            for ii in range(0, len(data)):  #If we remove the cold, the lowest isotherm must come off every function to keep grid and data consistent
                data[ii].__delslice__(0, len(rhoAxis))

        return data


def modifierFactory(indict):
    modtype = indict["type"]

    if(modtype.lower() == "fullrandom"):
        return fullRandom(indict)
    if(modtype.lower() == "gridrandom"):
        return gridRandom(indict)
    if(modtype.lower() == "gridregular"):
        return gridRegular(indict)
    if(modtype.lower() == "removecold"):
        return removeCold(indict)

    return None
