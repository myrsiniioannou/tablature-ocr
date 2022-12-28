from pathlib import Path
import os
import pandas as pd
import copy
from dataclasses import dataclass


def addPatternToMeasures(directory, elementPositions, fingeringPatterns, measures):
    for measure in measures:
        measureDirectory = os.path.join(directory, measure)
        measureDF = pd.read_csv(measureDirectory)
        # Delete header elements that were found in the positions of the pattern elements
        for i in range(len(elementPositions)):
            headerFingering = measureDF.loc[(measureDF["Position"]==elementPositions[i]-1) & (measureDF["String"]==0)]
            if not headerFingering.empty:
                measureDF = measureDF.drop(index=[headerFingering.index[0]])
        headerZeroList = [0] * len(elementPositions)
        adjustedElementPositions = [x - 1 for x in elementPositions]
        newHeaderRowsToAdd = pd.DataFrame(list(zip(fingeringPatterns, headerZeroList, adjustedElementPositions)),
                    columns =['Label', 'String', 'Position'])
        measureDF = pd.concat([measureDF, newHeaderRowsToAdd], ignore_index=True).sort_values(by=['Position']).reset_index(drop=True)
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


def assignValues(headerElementsToRepeat, measures, repeatingTimes, directory):
    for measure in measures:
        measureDirectory = os.path.join(directory, measure)
        measureDF = pd.read_csv(measureDirectory)
        headerDF = measureDF.loc[(measureDF['String'] == 0)]
        headerElementsToRepeatIdxList = headerDF.loc[headerDF['Position'].isin(headerElementsToRepeat)==True].index.tolist()
        repeatedHeaderFingeringList = measureDF.iloc[headerElementsToRepeatIdxList]["Label"].tolist() * repeatingTimes
        lengthOfRepeatedHeader = len(measureDF.iloc[headerElementsToRepeatIdxList]["Position"].tolist()) * repeatingTimes
        listOfRepeatedHeaderPositions = [*range(lengthOfRepeatedHeader)]
        listOfZerosToFillStringColumn = [0]*lengthOfRepeatedHeader
        headerIDXstoDrop = measureDF.loc[(measureDF['String'] == 0)].index.tolist()
        measureDF = measureDF.drop(headerIDXstoDrop)
        newHeaderDf = pd.DataFrame(list(zip(repeatedHeaderFingeringList, listOfZerosToFillStringColumn, listOfRepeatedHeaderPositions)), columns = ['Label', 'String', 'Position'])
        measureDF = pd.concat([measureDF, newHeaderDf], ignore_index=True).sort_values('Position').reset_index(drop=True)
        measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')
     

def repeatParts(pages, headerElementsToRepeat, pageIdx, measures, directory, pagesToRepeatHeader):
    if pageIdx in pages:
        headerElementsToRepeatIndexAdjustment = [element-1 for element in headerElementsToRepeat]
        for numberOfHeaderNotes, pages in pagesToRepeatHeader.items():
            if pageIdx in pages["pages"]:
                repeatingTimes = int(numberOfHeaderNotes)//len(headerElementsToRepeatIndexAdjustment)
                assignValues(headerElementsToRepeatIndexAdjustment, measures, repeatingTimes, directory)


def partialHeaderRepeater(pageIdx, partialHeaderRepeatPages, measures, directory, pagesToRepeatHeader):
    #Meaning, repeat a certain range inside a measure's header, n times
    if pageIdx in [page for values in partialHeaderRepeatPages.values() for page in values["pages"]]:
        for key, value in partialHeaderRepeatPages.items():
            repeatParts(value['pages'], value['headerElementsToRepeat'], pageIdx, measures, directory, pagesToRepeatHeader)


def columnRepeater(pageIdx, columnRepeatPages, pageMeasureDimensions, measures, directory, horizontalNumberOfMeasures):
    if pageIdx in columnRepeatPages:
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            if measureIdx % horizontalNumberOfMeasures == 0:
                headerToCopy = measureDF.loc[measureDF['String'] == 0]
            else:
                currentHeader = measureDF.loc[measureDF['String'] == 0]
                headerIndexesToDrop = currentHeader.index.tolist()
                measureDF = measureDF.drop(headerIndexesToDrop)
                measureDF = pd.concat([measureDF, headerToCopy], ignore_index=True).sort_values('Position').reset_index(drop=True)
                measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


def firstRowRepeater(pageIdx, firstRowRepeatPages, measures, directory, horizontalNumberOfMeasures):
    if pageIdx in firstRowRepeatPages:
        list0fheadersToCopy = []
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            if measureIdx < horizontalNumberOfMeasures:
                headerToCopy = measureDF.loc[measureDF['String'] == 0]
                list0fheadersToCopy.append(headerToCopy)
            else:
                currentHeader = measureDF.loc[measureDF['String'] == 0]
                headerIndexesToDrop = currentHeader.index.tolist()
                measureDF = measureDF.drop(headerIndexesToDrop)
                correspondingMeasureIndexToCopy = int(measureIdx % horizontalNumberOfMeasures)
                measureDF = pd.concat([measureDF, list0fheadersToCopy[correspondingMeasureIndexToCopy]], ignore_index=True).sort_values('Position').reset_index(drop=True)
                measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


@dataclass
class wholePageDFlist:
    dfList = list
    def updateList(self, value):
        self.dfList.append(value)


def wholePageRepeater(pageIdx, wholePageRepeatPages, measures, directory, list0fWholePageHeadersToRepeat):
    if pageIdx in wholePageRepeatPages and wholePageRepeatPages:
        list0fWholePageHeadersToRepeat.dfList = []
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            headerToCopy = measureDF.loc[measureDF['String'] == 0]
            list0fWholePageHeadersToRepeat.updateList(headerToCopy)
    elif (pageIdx not in wholePageRepeatPages) and wholePageRepeatPages:
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            currentHeader = measureDF.loc[measureDF['String'] == 0].index.tolist()
            measureDF = measureDF.drop(currentHeader)
            measureDF = pd.concat([measureDF, list0fWholePageHeadersToRepeat.dfList[measureIdx]] , ignore_index=True).sort_values('Position').reset_index(drop=True)
            measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')



def headerRepeatingProcesses(directory, pageIdx, headerPages, measures, pageDimensions, list0fWholePageHeadersToRepeat, headerNumberOfPages):
    horizontalNumberOfMeasures = int(pageDimensions["Horizontal"])
    #1 pattern repeater
    patternRepeater(directory, pageIdx, headerPages["patternRepeat"], measures)
    #2 partial header repeater
    partialHeaderRepeater(pageIdx, headerPages["partialHeaderRepeat"], measures, directory, headerNumberOfPages)
    #3 column repeater
    columnRepeater(pageIdx, headerPages["columnRepeat"], pageDimensions, measures, directory, horizontalNumberOfMeasures)
    #4 first row repeater
    firstRowRepeater(pageIdx, headerPages["firstRowRepeat"], measures, directory, horizontalNumberOfMeasures)
    #5 whole page repeater
    wholePageRepeater(pageIdx, headerPages["wholePageRepeat"], measures, directory, list0fWholePageHeadersToRepeat)


def headerRepeater(directory, headerPages, pageDimensions, headerNumberOfPages):
    print("Header Repeating Process Starting..")
    list0fWholePageHeadersToRepeat =  wholePageDFlist()
    for root, dirs, measures in os.walk(directory):
        pageNumber = os.path.basename(Path(root))
        # Keep only the CSV files
        CSVmeasures = list(filter(lambda measure: measure.endswith('.csv'), measures))
        if CSVmeasures:
            headerRepeatingProcesses(root, int(pageNumber), headerPages, CSVmeasures, pageDimensions, list0fWholePageHeadersToRepeat, headerNumberOfPages)
    print("Header Repeating Process Done!")



if __name__ == '__main__':
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\bookTest4"
    headerRepeaterValues = {
        "wholePageRepeat" : [], # Put the pages that we want to use as a template for the next ones. Ie if we want to copy page 1 to 2,3,4 then put [1] 
        "firstRowRepeat" : [*range(1,347)],
        "columnRepeat" : [],
        "partialHeaderRepeat" : {
            # "Pattern1" : {
            #    "pages" : [*range(1,2)],
            #    "headerElementsToRepeat" : [*range(1,5)],
            # },
            # "Pattern2" : {
            #    "pages" : [*range(2,3)],
            #    "headerElementsToRepeat" : [*range(1,7)],
            # }
        },
        "patternRepeat" : {
            "Pattern1" : {
                "pages" : [*range(1,347)],
                "elementIndex" : [4,5,6,7,8,12,13,14,15,16,20,21,22,23,24,28,29,30,31,32],
                "fingeringPattern" : ["p", "p", "p", "p", "p","p", "p", "p", "p", "p","p", "p", "p", "p", "p","p", "p", "p", "p", "p"]
            }#,
            #"Pattern2" : {
            #    "pages" : [3],
            #    "elementIndex" : [9,10,11,12,13],
            #    "fingeringPattern" : ["t", "t", "t", "t", "t"]
            #}
        }
    }
    # Part of Rendering Values
    bookValues = {
        "measures" : {
            "Horizontal": 2,
            "Vertical" : 6
        }
    }

    pageValues = {
        "headerNumber": {
            "32": {
                "pages": [*range(1,2)],
            },
            "36": {
                "pages": [*range(2,347)],
            }
        }
    }



    headerRepeater(extractedBookDirectory, headerRepeaterValues, bookValues["measures"], pageValues["headerNumber"])
    


