import os
from os.path import basename
from itertools import islice

def extractMetadataFromFile(filePath,numberOfMetadataLines):
    '''Just extracts the first N lines(which contains metadata) of a file in a list'''
    with open(filePath) as theFile:
        metadata = list(islice(theFile, numberOfMetadataLines))
    return metadata

def extractDataFromFile(filePath,numberOfMetadataLines):
    ''' extracts the data(skipping first N lines ,which are metadata) of a file in a list'''
    with open(filePath) as theFile:
        data = theFile.readlines()
    data = data[numberOfMetadataLines:]
    return data

def writeListToFile(data,filePath):
    '''writes a list to a file, each of the element of the list is a line'''
    with open(filePath,'w') as theFile:
        for item in data:
            theFile.write("%s" % item)

def seperateMetadataFromFiles(inputDirectory,outputDirectory,numberOfMetadataLines):
    '''
    Iterates through all the files in the inputDirectory. 
    Extracts the metadata and the data from each file.
    Writes the metadata and the data into seperate files into an outputDirectory keeping the same file name but different extensions.
    '''
    if not os.path.exists(outputDirectory):
        os.makedirs(outputDirectory)
    for root, dirs, files in os.walk(inputDirectory):
        for theFile in files:
            inputFilePath = os.path.join(root,theFile)
            outputFilePath = os.path.join(outputDirectory,os.path.splitext(theFile)[0])
            
            metadata = extractMetadataFromFile(inputFilePath,numberOfMetadataLines)
            data = extractDataFromFile(inputFilePath,numberOfMetadataLines)
            writeListToFile(metadata,outputFilePath+'.metadata')
            writeListToFile(data,outputFilePath+'.csv')


if __name__ == "__main__":
    numberOfMetadataLines = 9
    seperateMetadataFromFiles('data','data-and-metadata-seperated',numberOfMetadataLines)