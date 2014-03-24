#!/usr/bin/python



def getAttributesFromFile(fname="/927bis/ccd/gitRepos/suivi/SuiviLigne_18-03-2014_13h57.txt"):
    exampleAttributes = []
    f = open(fname)
    fr = f.readlines()
    f.close()
    for item in fr[4:]:
        exampleAttributes.append(item.split(';')[0])
    return exampleAttributes

def alignLists(listToSort, referenceList):
    returnList = []
    for item in referenceList:
        if item in listToSort:
            returnList.append(item)
        else:
            print 'item %s not in listToSort' % item
    return returnList

def orderAttributes(attributes, exampleAttributes):
    orderedAttributes = alignLists(attributes, exampleAttributes)
    return orderedAttributes

def loadFile(filename):
    f = open(filename)
    text = f.read()
    f.close()
    return text

def main():    
    import optparse
    usage = "usage: %prog --file <filename>"
    parser = optparse.OptionParser(usage = usage)

    parser.add_option("-f", "--filename", default='/927bis/ccd/Database/Tables', help="File to heal.")
    parser.add_option("-e", "--example", default='/927bis/ccd/gitRepos/suivi/SuiviLigne_18-03-2014_13h57.txt', help="Example file with ordered attributes.")
    parser.add_option("-o", "--output", default='/927bis/ccd/Database', help="Output file directory.")
    
    (options, args) = parser.parse_args()
    print 'options, args', options, args
    
    originalAttributes = getAttributesFromFile(options.filename)
    exampleAttributes = getAttributesFromFile(ptions.example)
    
    orderedAttributes = orderAttributes