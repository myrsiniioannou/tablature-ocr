from stat import SF_APPEND
from tkinter.messagebox import NO
from matplotlib.dviread import Box
from soupsieve import closest
from domain_model import *
import json
import copy
from jinja2 import Environment, FileSystemLoader
import math


def loadValues():
    # Set Values on paragraphs, headings, measures, and side frame text
    # PAGE NUMBERS HERE ARE THE SAME AS IN THE BOOK. Don't deduct 1 in order to start from 0.
    values = {
        "timeSignature" : {
            "fourFour": {       
                "pages": [*range(1,6)],
                "numerator": 4,
                "denominator": 4
            }
        },
        "measures" : {
            "Horizontal": 2,
            "Vertical" : 6
        },
        "paragraphs" : {
            "IA": [1, 8],
            "IB": [5, 6]
        },
        "headings" : {
            "singleHeading": [*range(4,18), *range(30,40)],
            "doubleHeading": [*range(1,4), *range(18,30)]
        },
        "sideFrameTextExistence" : {
            "sideFrameTextExistencePages" : [*range(1,5)],
            "sameFrameTextInMultiMeasuredRow" : [*range(1,5)],
            "sideFrameLetter" : {
                "A" : [1,2],
                "B" : [3,4,5,6,7]
            }
        },
        "headerLetter" : {
            "F" : [1,2],
            "E" : [3,4,5,6,7],
        }
    }

    pageBreakPatterns  = {
        "pattern1" : {
            "pages" : [range(1,2)],
            "pageBreaks" : [5,8]
        },
        "pattern2" : {
            "pages" : [range(2,3)],
            "pageBreaks" : [7,16]
        },
        "pattern3" : {
            "pages" : [range(3,200)],
            "pageBreaks" : [9]
        }
    }
    values["pageBreaksRanges"] = findPageBreaks(pageBreakPatterns)
    return values


def findPageBreaks(patterns):
    pageBreaksRanges = dict()
    for pattern, vals in patterns.items():
        for pageRange in vals["pages"]:
            for page in pageRange:
                pageBreaksRanges[page] = vals["pageBreaks"]
    return pageBreaksRanges


def loadJSON(JSONFile):
    with open(JSONFile, 'r') as f:
        book = json.load(f)
    return book


def templateLoading():
    file_loader = FileSystemLoader("templates")
    env = Environment(loader = file_loader)
    return env


def renderSectionPage(env, sectionPage):
    sectionPageTitle = sectionPage["sectionpagetitle"].upper()
    sectionPageRendering = env.get_template("sectionPage.mscx").render(pageTitle = sectionPageTitle)
    return sectionPageRendering

          
def findNotePitch(noteOnString, string):
    defaultStringPitches = [64, 59, 55, 50, 45, 40]    
    return (defaultStringPitches[string - 1] + noteOnString) if noteOnString else 45
    

def findNoteString(string):
    return string if string else None


def isBeamContinued(chordIdxPlusOne, notationPageIdx, userInputtedValues):
    previousIndex = chordIdxPlusOne-1
    return False if (previousIndex in userInputtedValues['pageBreaksRanges'][notationPageIdx]) or previousIndex == 1 else True


def findStemOffsetLengthFingeringOffset(chord):
    if chord["stringFingering"]["string"] == 6:
        offset = 7.60
    elif chord["stringFingering"]["string"] == 5:
        offset = 6.10
    elif chord["stringFingering"]["string"] == 4:
        offset = 4.50    
    elif chord["stringFingering"]["string"] == 3:
        offset = 3.10
    elif chord["stringFingering"]["string"] == 2:
        offset = 1.60
    else:
        offset = 0    
    return offset


def findArticulationOffset(chord):
    offset = {
        "16th": {
            "up" : 2.5,
            "down" : 1.5
        },
        "eighth": {
            "up" : 2,
            "down" : 1
        },
        "quarter": {
            "up" : 1,
            "down" : 0
        },
        "half": {
            "up" : 1.5,
            "down" : 0.5
        },
        "whole": {
            "up" : 0,
            "down" : 0
        }
    }
    try:
        chordTypeOffset = offset[chord["duration"]][chord["articulation"]]
    except:
        chordTypeOffset = 0
    stemOffset = findStemOffsetLengthFingeringOffset(chord)
    finalOffset = '{:.2f}'.format(round(chordTypeOffset - stemOffset, 2))
    return finalOffset

def findTripletYoffset(noteString):

    firstTripletoffset = 5.5 + (noteString-1)*1.5
    thirdTripletOffset = 0



    return '{:.2f}'.format(firstTripletoffset), '{:.2f}'.format(thirdTripletOffset)


def renderChords(env, chord, chordIdx, notationPageIdx, userInputtedValues):
    #stemYOffsetStemLengthFingeringOffset = findStemOffsetLengthFingeringOffset(chord)
    noteString = findNoteString(chord["note"]["string"])
    #if chord["triplet"] == 1:
        
        # print("chordIdx: ",chordIdx-1, "String: ",noteString)

        # print(chord["note"]["string"])
        # print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        # # Chord Idx + 1 because the index starts from 1. We need 2 notes after, therefore +1
        # print("chordIdx3: ", chordIdx + 1, "String: ",noteString)

        # print('---------------------------------')


    
    # firstTripletYoffset, thirdTripletYoffset = findTripletYoffset(noteString)

    # chordRendering = env.get_template("chord.mscx").render(
    #     duration = chord["duration"],
    #     hasBox = chord["hasBox"],
    #     hasAccent = chord["hasAccent"],
    #     articulationDirection = chord["articulation"],
    #     articulationYOffset = f'"{findArticulationOffset(chord)}"', 
    #     slur = chord["slur"],
    #     triplet = chord["triplet"],
    #     noteNoteOnStringFret = chord["note"]["noteOnString"],
    #     noteStringMinusOne = noteString - 1,
    #     headerFingering = chord["headerFingering"],
    #     stringFingeringTypeFingering = chord["stringFingering"]["typeFingering"],
    #     pitch = findNotePitch(chord["note"]["noteOnString"], chord["note"]["string"]),
    #     beamContinued = isBeamContinued(chordIdxPlusOne, notationPageIdx, userInputtedValues),
    #     stemYOffsetFingeringOffset = f'"{stemYOffsetStemLengthFingeringOffset}"',
    #     stemLength = stemYOffsetStemLengthFingeringOffset,
    #     firstTripletYoffset = firstTripletYoffset,
    #     thirdTripletYoffset = thirdTripletYoffset
    #     )
    return ""#chordRendering


def isMeasureFirstInRow(idx, col):
    return idx % col == 0


def isMeasureLastInRow(idx, col):
    return idx % col == col-1


def isMeasureLastInPage(idx, col, rows):
    return idx == (rows*col-1)


def findSideFrameTextOfMeasure(measureIndex, notationPageIndex, userValues):
    measureFrameText = ""
    if notationPageIndex in userValues["sideFrameTextExistence"]["sideFrameTextExistencePages"]:
        frameText = [key for key, value in userValues["sideFrameTextExistence"]["sideFrameLetter"].items() if notationPageIndex in value]
        measureFrameText += frameText[0]
        if notationPageIndex in userValues["sideFrameTextExistence"]["sameFrameTextInMultiMeasuredRow"]:
            col = int(userValues["measures"]["Horizontal"])
            measureFrameText += str(abs(measureIndex%col - measureIndex)//col + 1)
        else:
            measureFrameText += measureIndex + 1 # Because we start from 0
    return measureFrameText


def renderMeasure(env, measureIndex, measure, notationPageIndex, userValues, timeSignNumerator, timeSignDenominator):
    renderedChords = ""
    # Measures contain multiple chords that should be rendered first.
    for chordIndex, chord in enumerate(measure["chords"], start = 1):
        # if this is the first note of the triplet and the third one exist then return the string of the third one
        if chord["triplet"] == 1 and measure["chords"][chordIndex+1]:
            print("IDX:", chordIndex)
            print(chord)
            print("IDX:", chordIndex+2)
            print(measure["chords"][chordIndex+1])
            print(measure["chords"][chordIndex+1]["note"]["string"])
            stringOfThirdTriplet = measure["chords"][chordIndex+1]["note"]["string"]
            print("--------------------------------------------------------")


        renderedChords += renderChords(env, chord, chordIndex, notationPageIndex, userValues)
    
    measureRendering = env.get_template("measure.mscx").render(
        chordContent = renderedChords,
        sideFrameText = findSideFrameTextOfMeasure(measureIndex, notationPageIndex, userValues),
        isMeasureFirstInRow = isMeasureFirstInRow(measureIndex, userValues["measures"]["Horizontal"]),
        isMeasureLastInRow = isMeasureLastInRow(measureIndex, userValues["measures"]["Horizontal"]),
        isMeasureLastInPage = isMeasureLastInPage(measureIndex, userValues["measures"]["Horizontal"], userValues["measures"]["Vertical"]),
        numerator = timeSignNumerator, 
        denominator = timeSignDenominator)
    return measureRendering


def findHeadingTexts(notationPageIdx, userInputtedValues):
    allParagraphPages = userInputtedValues["paragraphs"]["IA"] + userInputtedValues["paragraphs"]["IB"]
    allParagraphPages.sort()
    closestParagraphPage = min(allParagraphPages, key = lambda x:abs(x - notationPageIdx))
    if closestParagraphPage <= notationPageIdx:
        MINClosestParagraphPage = copy.deepcopy(closestParagraphPage)
    elif (closestParagraphPage > notationPageIdx and (allParagraphPages.index(closestParagraphPage) - 1) > 0):
        MINClosestParagraphPage = allParagraphPages[allParagraphPages.index(closestParagraphPage) - 1]
    else:
        MINClosestParagraphPage = allParagraphPages[0]
    if MINClosestParagraphPage in userInputtedValues["paragraphs"]["IA"]:
        paragraphLetter = "A"
    else:
        paragraphLetter = "B"
    paragraphAndNotationPageDifference = abs(notationPageIdx - MINClosestParagraphPage)
    hasPageSingleHeading = notationPageIdx in userInputtedValues["headings"]["singleHeading"]
    hasPageDoubleHeading = notationPageIdx in userInputtedValues["headings"]["doubleHeading"]
    if hasPageSingleHeading and not hasPageDoubleHeading:
        heading1 = str(paragraphAndNotationPageDifference + 1) + paragraphLetter
        heading2 = None
    elif hasPageDoubleHeading and not hasPageSingleHeading:
        heading1 = str((2*paragraphAndNotationPageDifference) + 1) + paragraphLetter
        heading2 = str((2*paragraphAndNotationPageDifference) + 2) + paragraphLetter
    else:
        heading1 = None
        heading2 = None       
    return heading1, heading2


def findParagraphText(notationPageIndex, userValues):
    if notationPageIndex in userValues["paragraphs"]["IA"]:
        text = "IA"
    elif notationPageIndex in userValues["paragraphs"]["IB"]:
        text = "IB"
    else:
        text = None
    return text


def findHeaderLetter(notationPageIndex, userValues):
    headerLetter = ""
    for letter in userValues["headerLetter"].keys():
        if notationPageIndex in userValues["headerLetter"][letter]:
            headerLetter = letter
    return headerLetter


def findTimeSignature(pageIndex, userInputtedValues):
    numerator = ""
    denominator = ""
    for timeSign, tSElements in userInputtedValues["timeSignature"].items():
        for element, value in tSElements.items():
            if (element == 'pages') and (pageIndex in value):
                numerator = tSElements["numerator"]
                denominator = tSElements["denominator"]
    return numerator, denominator


def renderNotationPage(env, notationPageIdx, notationPage, userInputtedValues):
    renderedMeasures = ""
    timeSignNumerator, timeSignDenominator = findTimeSignature(notationPageIdx, userInputtedValues)
    #Notation Pages contain multiple measures that should be rendered first.
    for measureIndex, measure in enumerate(notationPage["measures"]):
        renderedMeasures += renderMeasure(env,measureIndex, measure, notationPageIdx, userInputtedValues, timeSignNumerator, timeSignDenominator)
    paragraphText = findParagraphText(notationPageIdx, userInputtedValues)
    header_letter = findHeaderLetter(notationPageIdx, userInputtedValues)
    heading1Text, heading2Text = findHeadingTexts(notationPageIdx, userInputtedValues)

    notationPageRendering = env.get_template("notationPage.mscx").render(
        measureContent = renderedMeasures,
        singleHeading = notationPageIdx in userInputtedValues["headings"]["singleHeading"],
        doubleHeading = notationPageIdx in userInputtedValues["headings"]["doubleHeading"],
        paragraph = paragraphText,
        headerLetter = header_letter,
        heading1Text = heading1Text,
        heading2Text = heading2Text)
    return  notationPageRendering


def iterateOverPagesAndRenderTheirContent(env, JSONbook, userInputtedValues):
    notationPageIndex = 1
    renderedPages = ""
    for pageList in JSONbook["pages"]:
        for pageType, pageContent in pageList.items():
            if pageType == "sectionpage" and pageContent:
                renderedPages += renderSectionPage(env, pageContent)
            elif pageType == "notationpage" and pageContent:
                renderedPages += renderNotationPage(env, notationPageIndex, pageContent, userInputtedValues)
                notationPageIndex +=1 
    return renderedPages


def finalizeBookRendering(env, stringNumber, bookRenderedContent):
    book = env.get_template("book.mscx").render(
    NumberOfStrings = stringNumber,
    bookContent = bookRenderedContent)
    return book


def renderBook(JSON):
    # Load the Set Values of the book.
    setValues = loadValues()

    # Load JSON Book File
    bookInJsonFormat = loadJSON(JSON)

    # Template Loading
    environment = templateLoading()

    # Iterate over every page (section or notation) and render its content
    bookRendering = iterateOverPagesAndRenderTheirContent(environment, bookInJsonFormat, setValues)

    #Finalize the book by adding the book template XML-info
    stringNumber = bookInJsonFormat["numberofstrings"]
    output = finalizeBookRendering(environment, stringNumber, bookRendering)
    

    # Save the Musescore file
    musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\renderedBook1.mscx"
    with open(f"{musescoreOutputFile}", "w") as f:
         f.write(output)

    print("Book Rendering Done!")




if __name__ == '__main__':
    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    renderBook(JSON_book_directory)