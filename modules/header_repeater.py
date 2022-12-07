from pathlib import Path
import os
import pandas as pd
import copy
from dataclasses import dataclass


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


def assignValues(headerElementsToRepeatIndexAdjustment, measureDF, repeatingTimes):
    for elementIdx, element in enumerate(headerElementsToRepeatIndexAdjustment):
        dfToAssign = measureDF.loc[(measureDF['Position'] == elementIdx) & (measureDF['String'] == 0), "Label"].values
        valueToAssign = dfToAssign[0] if dfToAssign.any() else None
        if valueToAssign:
            for iteration in range(1, repeatingTimes):
                repeatedIndex = iteration*len(headerElementsToRepeatIndexAdjustment)+elementIdx
                measureDF.loc[(measureDF['Position'] == repeatedIndex) & (measureDF['String'] == 0), "Label"] = valueToAssign


def repeatPartialMeasuresAndSaveThem(pageIdx, value, measures, directory):
    if pageIdx in value["pages"]:
        headerElementsToRepeatIndexAdjustment = [element-1 for element in value['headerElementsToRepeat']]
        for measure in measures:
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            totalElements = len(measureDF['Position'].unique())
            repeatingTimes = totalElements//len(headerElementsToRepeatIndexAdjustment)
            assignValues(headerElementsToRepeatIndexAdjustment, measureDF, repeatingTimes)


def partialHeaderRepeater(pageIdx, partialHeaderRepeatPages, measures, directory):
    if pageIdx in [page for values in partialHeaderRepeatPages.values() for page in values["pages"]]:
        for key, value in partialHeaderRepeatPages.items():
            repeatPartialMeasuresAndSaveThem(pageIdx, value, measures, directory)


def columnRepeater(pageIdx, columnRepeatPages, pageMeasureDimensions, measures, directory, horizontalNumberOfMeasures):
    if pageIdx in columnRepeatPages:
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            if measureIdx % horizontalNumberOfMeasures == 0:
                headerToCopy = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
                headerToCopy.insert(1, 'String', int(0))
            else:
                currentHeader = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
                measureDF = measureDF.drop(currentHeader.index)
                measureDF = pd.concat([measureDF, headerToCopy], ignore_index=True).sort_values('Position')
                measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


def firstRowRepeater(pageIdx, firstRowRepeatPages, pageMeasureDimensions, measures, directory, horizontalNumberOfMeasures):
    if pageIdx in firstRowRepeatPages:
        list0fModuloDFs = []
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            if measureIdx < horizontalNumberOfMeasures:
                headerToCopy = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
                headerToCopy.insert(1, 'String', int(0))
                list0fModuloDFs.append(headerToCopy)
            else:
                currentHeader = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
                measureDF = measureDF.drop(currentHeader.index)
                measureDF = pd.concat([measureDF, list0fModuloDFs[int(measureIdx % horizontalNumberOfMeasures)]], ignore_index=True).sort_values('Position').reset_index(drop=True)
                measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


@dataclass
class wholePageDFlist:
    dfList = list
    def updateList(self, value):
        self.dfList.append(value)


def wholePageRepeater(pageIdx, wholePageRepeatPages, measures, directory, list0fWholePageHeadersToRepeat):
    if pageIdx in wholePageRepeatPages:
        list0fWholePageHeadersToRepeat.dfList = []
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            headerToCopy = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
            headerToCopy.insert(1, 'String', int(0))
            list0fWholePageHeadersToRepeat.updateList(headerToCopy)
    else:
        for measureIdx, measure in enumerate(measures):
            measureDirectory = os.path.join(directory, measure)
            measureDF = pd.read_csv(measureDirectory)
            currentHeader = measureDF.loc[measureDF['String'] == 0, ["Label", "Position"]]
            measureDF = measureDF.drop(currentHeader.index)
            measureDF = pd.concat([measureDF, list0fWholePageHeadersToRepeat.dfList[measureIdx]] , ignore_index=True).sort_values('Position').reset_index(drop=True)
            measureDF.to_csv(measureDirectory, index = False, encoding='utf-8')


def headerRepeatingProcesses(directory, pageIdx, headerPages, measures, pageDimensions, list0fWholePageHeadersToRepeat):
    horizontalNumberOfMeasures = int(pageDimensions["Horizontal"])
    #1 pattern repeater
    patternRepeater(directory, pageIdx, headerPages["patternRepeat"], measures)
    #2 partial header repeater
    partialHeaderRepeater(pageIdx, headerPages["partialHeaderRepeat"], measures, directory)
    #3 column repeater
    columnRepeater(pageIdx, headerPages["columnRepeat"], pageDimensions, measures, directory, horizontalNumberOfMeasures)
    #4 first row repeater
    firstRowRepeater(pageIdx, headerPages["firstRowRepeat"], pageDimensions, measures, directory, horizontalNumberOfMeasures)
    #5 whole page repeater
    wholePageRepeater(pageIdx, headerPages["wholePageRepeat"], measures, directory, list0fWholePageHeadersToRepeat)


def headerRepeater(directory, headerPages, pageDimensions):
    list0fWholePageHeadersToRepeat =  wholePageDFlist()
    for root, dirs, measures in os.walk(directory):
        pageNumber = os.path.basename(Path(root))
        # Keep only the CSV files
        CSVmeasures = list(filter(lambda measure: measure.endswith('.csv'), measures))
        if CSVmeasures:
            headerRepeatingProcesses(root, int(pageNumber), headerPages, CSVmeasures, pageDimensions, list0fWholePageHeadersToRepeat)
    print("Header Repeating Process Done!")



if __name__ == '__main__':
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\bookTest"
    headerRepeaterValues = {
        "wholePageRepeat" : [1, 3 ], # Put the pages that we want to use as a template for the next ones. Ie if we want to copy page 1 to 2,3,4 then put [1] 
        "firstRowRepeat" : [1, 2, 3, 4],
        "columnRepeat" : [1, 2, 3, 4],
        "partialHeaderRepeat" : {
            "Pattern1" : {
                "pages" :[1, 3],
                "headerElementsToRepeat" : [1,2,3,4,5]
            },
            "Pattern2" : {
                "pages" :[3, 4],
                "headerElementsToRepeat" : [1,2,3]
            }
        },
        "patternRepeat" : {
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
    


