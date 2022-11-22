from pathlib import Path
import os
import pandas as pd

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
            
   
def headerRepeater(directory, headerPages: dict):
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



if __name__ == '__main__':

    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    pagesWithHeader = [
        {"chapter": 1, "unit": 1, "page": 1},
        {"chapter": 1, "unit": 2, "page": 3}
    ]
    headerRepeater(extractedBookDirectory, pagesWithHeader)


