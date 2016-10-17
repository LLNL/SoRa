
import glob
import json
import numpy
import csv

# Takes a list of filenames with wildcards, and returns a list of actual resolved filenames.
# Throws an IOError if no files were found
#
def globFilenames(filenames):

    outFilenames = []  #The use could list multiple names, or globs, so make
    for filename in filenames:  #all that into one list
        globednames = glob.glob(filename)
        for name in globednames:
            outFilenames.append(name)
            
    if(len(outFilenames) == 0):
        errstr = "";
        for filename in filenames:
            errstr = errstr + " " + filename
        raise IOError("no files found from list: " + errstr)

    return outFilenames


#Outputs columns of float data, can output any number of columns, but they all must be the same length
def writeColumns(outputFilename, labels, data):
    outputfile = open(outputFilename, "w");
    outputfile.write("# ");
    for ii in range(0, len(labels)):
        outputfile.write("%s \t" % labels[ii])
    outputfile.write("\n");

    columnLen = len(data[0])
    numColumns = len(data)

    for vv in range(0, columnLen):
        for cc in range(0, numColumns):
            outputfile.write("%.15E " % data[cc][vv])
        outputfile.write("\n")

    outputfile.close()

#Outputs columns of float data in csv, can output any number of columns, but they all must be the same length
def writeCSVFile(outputFilename, labels, data, delimiter=","):
    with open(outputFilename, "wb") as outputfile:
        csvwriter = csv.writer(outputfile, delimiter=delimiter)
        csvwriter.writerow(labels)

        columnLen = len(data[0])
        numColumns = len(data)

        for vv in range(0, columnLen):
            row = []
            for cc in range(0, numColumns):
                row.append(data[cc][vv])  #Force 15 wide floats in scientific format
#                row.append("%.15E " % data[cc][vv])  #Force 15 wide floats in scientific format
            csvwriter.writerow(row)
    
#Writes out out SR format column file.  That means even columns of numbers, with uncommented labels on top 
#The axes are expected to be fully expanded  
def writeSRFile(outputFilename, labels, data):
    outputfile = open(outputFilename, "w");
    for label in labels:
        outputfile.write("%s \t" % (label))
    outputfile.write("\n")

    numRows = len(data[0])
    
    for rr in range(0,numRows):
        for cc in range(0, len(data)): #in numColumns
            outputfile.write("%.15E \t" % (data[cc][rr]));
        outputfile.write("\n");
                                 
    outputfile.close();


def writeConfigFile(thisfig, configFilename):
    configfile = open(configFilename, "w")
    json.dump(thisfig, configfile, indent=2)
    configfile.close()

#Data is in the [rho, temp, data] format, such that len(data) = len(rho) * len(temp)
def writeEOSFileFromData(outputFilename, labels, data):
    outputfile = open(outputFilename, "w");
    outputfile.write("# %s \t%s \t%s\n" % (labels[0], labels[1], labels[2]))

    tempLen = len(data[0])
    rhoLen = len(data[1])
    
    for tt in range(0,tempLen):
        for rr in range(0,rhoLen):
            outputfile.write("%.15E \t%.15E \t%.15E\n" % (data[0][tt], data[1][rr], data[2][tt*rhoLen + rr]));
                                 
    outputfile.close();


#Reads columns into multiple lists, it returns a list of those lists
#The first non-comment line is expected to be column names
#Returns (labels, data)
def readCSVFile(filename, delimiter = ","):
    import csv
    data = []
    fp = open(filename)
    rdr = csv.reader(filter(lambda row: row[0]!='#', fp), delimiter=delimiter)  #Filters out comments
    for row in rdr:
        data.append(row)
    fp.close()

    #convert everything except the 1st row to floats
    columnLen = len(data)
    numColumns = len(data[0])

    for vv in range(1, columnLen):
        for cc in range(0, numColumns):
            data[vv][cc] = float(data[vv][cc])
    
    return(data[0], data[1:])

#Reads columns of doubles into multiple lists, it returns a list of those lists
#Every column is expected to be a numeral.
#lines starting with '#' are ignored as comments
#The values returned are floats. 
def readUltraFile(filename):
    retList = []
    infile = open(filename, "r");
    linenum = 0
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == "" or line[0] == '#'):
            continue;

        splitline = line.split();
        if(len(splitline) != len(retList)):
            if(len(retList) == 0):
                for ii in range(0, len(splitline)):
                    retList.append([]);
            else:
                print "ERROR, file %s line %d has %d columns, but relList only has %d columns" % (filename, linenum, len(splitline), len(retList));
                
                
        for ii in range(0, len(splitline)):
            retList[ii].append(float(splitline[ii]))

    infile.close()
    return retList

#Seeks to a specified ultra "block" (blocks are seperated by '#' comments)
#Reads columns of doubles into multiple lists, it returns a list of those lists
#Every column is expected to be a numeral.
def readBlockFromUltraFile(filename, targetBlock, targetBlockName):
    retList = []
    headers = []
    infile = open(filename, "r");
    linenum = 0
    blockNum = 1
#    lastLineWasAComment = True; #Skip counting blockNum if the first line is a comment
    newBlock = True
    blockName = ""
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == ""):
            continue
        if(line == "end"):
            blockNum = blockNum + 1
            newBlock = True
            blockName = ""
            continue
        if(line[0] == '#'):
            comment = line[1:].strip()
            if(comment == targetBlockName):  #These should be our headers
                targetBlock = blockNum                
            if(blockNum == targetBlock):
                blockName = comment
                headers = blockName.split("vs")

#            lastLineWasAComment = True
            continue
        else:
#            lastLineWasAComment = False;
            newBlock = False

        if(blockNum == targetBlock):
            splitline = line.split();
            if(len(splitline) != len(retList)):
                if(len(retList) == 0):
                    for ii in range(0, len(splitline)):
                        retList.append([]);
                else:
                    print "ERROR, line %d has %d columns, but relList only has %d columns" % (linenum, len(splitline), len(retList));
                
                
            for ii in range(0, len(splitline)):
                retList[ii].append(float(splitline[ii]))

    infile.close()
    return (headers, retList)


# Reads columns into multiple lists, it returns a list of those lists
# The first uncommented row is expected to be 
# Every other row is expected to be a numeral (float).
# lines starting with '#' are ignored as comments
# Returns as many columns are there are columns in the file
# doesn't remove duplicate values from the axes, that can be done seperately with unique_list
# Same as readUltraFile, except that it may be able to ignore unexpect comment lines.
def readDatFileWithHeaders(filename):
    retList = []
    infile = open(filename, "r");
    linenum = 0
    seenHeaders = False
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == "" or line[0] == '#'):
            continue;

        splitline = line.split();
        if(not seenHeaders):      #First row should be column names
            headers = splitline
            seenHeaders = True
            continue
        try:
          ff = float(splitline[0])
        except ValueError:
          continue #Some EOS files don't use '#' for comments.
        
        if(len(splitline) != len(retList)):
            if(len(retList) == 0):
                for ii in range(0, len(splitline)):
                    retList.append([]);
            else:
                print "ERROR, line %d has %d columns, but relList only has %d columns" % (linenum, len(splitline), len(retList));
                
        for ii in range(0, len(splitline)):
            retList[ii].append(float(splitline[ii])) #The data

    infile.close()
    return (headers, retList)


# Reads columns into multiple lists, it returns a list of those lists
# Every other column is expected to be a numeral (float).
# lines starting with '#' are ignored as comments
# Returns as many columns are there are columns in the file
# doesn't remove duplicate values from the axes, that can be done seperately with unique_list
# Same as readUltraFile, except that it may be able to ignore unexpect comment lines.
def readEOSFile(filename):
    retList = []
    infile = open(filename, "r");
    linenum = 0
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == "" or line[0] == '#'):
            continue;

        splitline = line.split();
        try:
          ff = float(splitline[0])
        except ValueError:
          continue #Some EOS files don't use '#' for comments.
        
        if(len(splitline) != len(retList)):
            if(len(retList) == 0):
                for ii in range(0, len(splitline)):
                    retList.append([]);
            else:
                print "ERROR, line %d has %d columns, but relList only has %d columns" % (linenum, len(splitline), len(retList));
                
        for ii in range(0, len(splitline)):
            retList[ii].append(float(splitline[ii])) #The data

    infile.close()
    return retList


#Reads columns into multiple lists, it returns a list of those lists
# **** The first column is expected to be a name of the row ***
# Every other column is expected to be a numeral (float).
# lines starting with '#' are ignored as comments
def readColumnsFile(filename):
    retList = []
    infile = open(filename, "r");
    linenum = 0
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == "" or line[0] == '#'):
            continue;

        splitline = line.split();
        if(len(splitline) != len(retList)):
            if(len(retList) == 0):
                for ii in range(0, len(splitline)):
                    retList.append([]);
            else:
                print "ERROR, line %d has %d columns, but relList only has %d columns" % (linenum, len(splitline), len(retList));
                
        retList[0].append(splitline[0]) #The row name
        for ii in range(1, len(splitline)):
            retList[ii].append(float(splitline[ii])) #The data

    infile.close()
    return retList

    


# Reads columns into multiple lists, it returns a list of those lists
# lines starting with '#' are ignored as comments
#No expectations are made of the data at all, except that they are whitespace seprated columns
def readColumnsFileAsStrings(filename):
    retList = []
    infile = open(filename, "r");
    linenum = 0
    for line in infile.readlines():
        linenum += 1; 
        line = line.strip()
        if(line == "" or line[0] == '#'):
            continue;

        splitline = line.split();
        
        if(len(splitline) != len(retList)):
            if(len(retList) == 0):
                for ii in range(0, len(splitline)):
                    retList.append([]);
            else:
                print "ERROR, line %d has %d columns, but relList only has %d columns" % (linenum, len(splitline), len(retList));
                
        retList[0].append(splitline[0]) #The row name
        for ii in range(1, len(splitline)):
            retList[ii].append(splitline[ii]) #The data

    infile.close()
    return retList



#Determine if two values are equal within some tolerance (hardcoded to 1e-1 here.
#It checks both absolute and relative equality
def fuzzyEquals(a, b):
    epsilon = 1e-3;
    if(math.fabs(a - b) < epsilon):  #Here we're using epsilon as absolute error
        return True;

    relativeError = 0;
    if (math.fabs(b) > math.fabs(a)):
      relativeError = math.fabs((a - b) / b);
    else:
      relativeError = math.fabs((a - b) / a);
  
    if (relativeError <= epsilon): #and here epsilon is relative
      return True;
    else:
      return False;

#This unique takes a list of floats
#It returns the uniques in sorted order, small to large
def unique(lof):  #lof stands for list of floats

    lof.sort();

    prev = lof[0]
    retList = [prev]
    
    for ii in range(1, len(lof)):
        if(lof[ii] != prev):
            retList.append(lof[ii])
            prev = lof[ii]

    return retList

#tuple transpose takes a list of columns, and makes a list of tuples.
#So data: [ [ 1, 2, 3], [4, 5, 6] ]
#becomes: [ (1,4), (2,5), (3,6) ]
# loc = list of columns
# lot = list of tuples

def tuple_transpose(loc):
    lot = []
    for ii in range(0,len(loc[0])):
        this_tuple = []
        for cc in range(0, len(loc)):
            this_tuple.append(loc[cc][ii])
        lot.append(tuple(this_tuple))

    return lot


