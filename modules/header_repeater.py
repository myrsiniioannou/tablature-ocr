from pathlib import Path
import os
import pandas as pd
import copy
import numpy as np

def addZeroToNumberIfOneDigit(number):
    return "0" + str(number) if len(str(number)) == 1 else str(number)


def generateHeaderDirectory(dir, headerPage):
    for section in headerPage:
        if section != "page":
            dir = os.path.join(dir,section+addZeroToNumberIfOneDigit(headerPage[section]))
        else:
            dir = os.path.join(dir,addZeroToNumberIfOneDigit(headerPage[section]))
    return dir


def copyDFs(root, measures):
    listOfMeasureHeaderDfs = []
    for measure in measures:
        if measure.endswith('.csv'):
            measureDirectory = os.path.join(root, measure)
            measureDF = pd.read_csv(measureDirectory)
            listOfMeasureHeaderDfs.append(measureDF[measureDF["String"] == 0].reset_index(drop=True))
    return listOfMeasureHeaderDfs


def concatenateDFs(root, measures, listOfMeasureHeaderDfs):
    index = 0
    for measure in measures:
        if measure.endswith('.csv'):
            measureDirectory = os.path.join(root, measure)
            measureDF = pd.read_csv(measureDirectory)
            try:
                measureDFwithNoHeader = measureDF[measureDF["String"] != 0]
            except:
                pass
            try:
                newMeasureDf = pd.concat([listOfMeasureHeaderDfs[index], measureDFwithNoHeader], ignore_index=True)
                newMeasureDf = newMeasureDf.sort_values(by=['Position'], ascending=True, ignore_index=True)
                newMeasureDf.to_csv(measureDirectory,index = False, encoding='utf-8')
            except:
                pass
            index += 1
            
   
def headerRepeaterOLD(directory, headerPages: dict):
    listOfHeaderPages = []
    listOfMeasureHeaderDfs = []
    # Iterates through the pages that their header should be copied. They are added by the user.
    # It generates the directories of the pages that have header in order to iterate on them.
    for headerPage in headerPages:
        listOfHeaderPages.append(generateHeaderDirectory(directory, headerPage))
    # Iterating through every folder and page
    for root, dirs, measures in os.walk(directory):
        # If this is a page with a header, then call copyDFs, copy the measures and store them in a list
        if root in listOfHeaderPages:
            listOfMeasureHeaderDfs = copyDFs(root, measures)
        # else call concatenateDFs to concatenate the previous list to the headerless measures
        else:
            if listOfMeasureHeaderDfs:
                concatenateDFs(root, measures, listOfMeasureHeaderDfs)
    print("Header Repeating Process Done!")



#----------------------------------------------------------




def addPatternToMeasures(directory, elementIndexes, fingeringPatterns, measures):
    for measure in measures:
        measureDirectory = os.path.join(directory, measure)
        measureDF = pd.read_csv(measureDirectory)
        for i in range(len(elementIndexes)):
            measureDF.loc[(measureDF["Position"]==elementIndexes[i]) & (measureDF["String"]==0), "Label"] = fingeringPatterns[i]
        measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


def findElementIndexAndFingeringPatternForPage(pageIndex, patterns):
    for key, value in patterns.items():
        if pageIndex in value["pages"]:
            elementIndexes = copy.deepcopy(value["elementIndex"])
            fingeringPatterns = copy.deepcopy(value["fingeringPattern"])
    return elementIndexes, fingeringPatterns


def patternRepeater(directory, pageIndex, patterns, measures):
    # Check if this page has a pattern and if it does add it to the measures
    if pageIndex in [page for values in patterns.values() for page in values["pages"]]:
        elementIndexes, fingeringPatterns = findElementIndexAndFingeringPatternForPage(pageIndex, patterns)
        addPatternToMeasures(directory, elementIndexes, fingeringPatterns, measures)





def repeatPartialMeasuresAndSaveThem(pageIdx, value, measures, directory):
    if pageIdx in value["pages"]:
        print("pageIdx: ", pageIdx)
        print('headerElementsToRepeat: ', value['headerElementsToRepeat'])
        for measure in measures:
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            #print(measureDF[(measureDF['Position'].isin(value['headerElementsToRepeat'])) & (measureDF['String'] == 0)])

            totalElements = len(measureDF['Position'].unique())
            repeatingTimes = totalElements//len(value['headerElementsToRepeat'])
            
            for element in value['headerElementsToRepeat']:
                print("----------------------------------------------")
                for a in range(1, repeatingTimes):




                    ##### EDO EIMAIIIIIIIIII
                    ## PREPEI NA GINETAI ASSIGN TO 1 STO 6, TO 2 STO 7 , 3 STO 8 KTL
                    repeatedIndex = a*len(value['headerElementsToRepeat'])+int(element)
                    print(measureDF[(measureDF['Position'] == a) & (measureDF['String'] == 0)])
                    print("-------------------------")
                    print(measureDF[(measureDF['Position'] == repeatedIndex) & (measureDF['String'] == 0)])
                    print("----##################------")
                
            
            print(measureDF)

def partialHeaderRepeater(pageIdx, partialHeaderRepeater, measures, directory):
    if pageIdx in [page for values in partialHeaderRepeater.values() for page in values["pages"]]:
        for key, value in partialHeaderRepeater.items():
            repeatPartialMeasuresAndSaveThem(pageIdx, value, measures, directory)


def headerRepeatingProcesses(directory, pageIdx, headerPages, measures):

    #1 pattern repeater
    #patternRepeater(directory, pageIdx, headerPages["patterns"], measures)
    #2 partial header repeater
    partialHeaderRepeater(pageIdx, headerPages["partialHeaderRepeater"], measures, directory)
    #3 column repeater
    #4 first row repeater
    #5 whole page repeater





def headerRepeater(directory, headerPages, measures):
    for root, dirs, measures in os.walk(directory):
        pageNumber = os.path.basename(Path(root))
        # Keep only the CSV files
        CSVmeasures = list(filter(lambda measure: measure.endswith('.csv'), measures))
        if CSVmeasures:
            headerRepeatingProcesses(root, int(pageNumber), headerPages, CSVmeasures)
        print("------------------------------------------------------------------")


        


if __name__ == '__main__':

    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book2"
    headerRepeaterValues = {
        "wholePage" : [1, 2, 3],
        "firstRowToWholePage" : [4, 5, 6],
        "columnRepeat" : [7, 8, 9],
        "partialHeaderRepeater" : {
            "Pattern1" : {
                "pages" :[1, 2],
                "headerElementsToRepeat" : [1,2,3,4,5]
            },
            "Pattern2" : {
                "pages" :[3, 4],
                "headerElementsToRepeat" : [1,2,3]
            }
        },
        "patterns" : {
            "Pattern1" : {
                "pages" : [1,2],
                "elementIndex" : [4,5,6,7,8],
                "fingeringPattern" : ["e", "e", "e", "e", "e"]
            },
            "Pattern2" : {
                "pages" : [3],
                "elementIndex" : [9,10,11,12,13],
                "fingeringPattern" : ["t", "t", "t", "t", "t"]
            },
            "Pattern3" : {
                "pages" : [4,5,6],
                "elementIndex" : [14,15,16],
                "fingeringPattern" : ["q", "q", "q", "q", "q"]
            }
        }
    }

    # Part of Rendering Values
    bookValues = {
        "measures" : {
            "Horizontal": 2,
            "Vertical" : 6
        }
    }


    headerRepeater(extractedBookDirectory, headerRepeaterValues, bookValues["measures"])
    


