from stat import SF_APPEND
from tkinter.messagebox import NO
from matplotlib.dviread import Box
from soupsieve import closest
from domain_model import *
import json
import copy
from jinja2 import Environment, FileSystemLoader
import math


def loadValues(values, doubleBeamBreaks, singleBeamBreaks):
    values["doubleBeamBreakRanges"] = findPageBreaks(doubleBeamBreaks)
    values["singleBeamBreakRanges"] = findPageBreaks(singleBeamBreaks)
    return values


def findPageBreaks(patterns):
    beamBreakRanges = dict()
    for pattern, vals in patterns.items():
        for pageRange in vals["pages"]:
            for page in pageRange:
                beamBreakRanges[page] = vals["beamBreaks"]
    return beamBreakRanges


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
    

def isBeamBreaking(chordIdx, beamBreakRanges):
    return True if (chordIdx in beamBreakRanges) or chordIdx == 1 else False


def findStemOffsetLengthFingeringOffset(chordString):
    if chordString == 6:
        offset = 7.6
    elif chordString == 5:
        offset = 6.1
    elif chordString == 4:
        offset = 4.6 
    elif chordString == 3:
        offset = 3.1
    elif chordString == 2:
        offset = 1.6
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
    stemOffset = findStemOffsetLengthFingeringOffset(chord["stringFingering"]["string"])
    finalOffset = '{:.2f}'.format(round(chordTypeOffset - stemOffset, 2))
    return finalOffset

def findTripletYoffset(stringOfCurrentNoteInChord, stringOfThirdTripletOfCurrentChord):
    stringOfCurrentNoteInChord = stringOfCurrentNoteInChord - 1 if stringOfCurrentNoteInChord else 0
    stringOfThirdTripletOfCurrentChord = stringOfThirdTripletOfCurrentChord - 1 if stringOfThirdTripletOfCurrentChord else 0
    stringDifference = stringOfCurrentNoteInChord - stringOfThirdTripletOfCurrentChord
    firstTripletoffset = -5.5 - stringOfCurrentNoteInChord*1.5
    thirdTripletOffset = 0 + (stringOfCurrentNoteInChord - stringOfThirdTripletOfCurrentChord)*1.5
    return '{:.2f}'.format(firstTripletoffset), '{:.2f}'.format(thirdTripletOffset)



def renderChords(env, chord, chordIdx, notationPageIdx, userInputtedValues, stringOfThirdTripletOfCurrentChord):
    stemYOffsetStemLengthFingeringOffset = findStemOffsetLengthFingeringOffset(chord["stringFingering"]["string"]) 
    firstTripletYoffset, thirdTripletYoffset = findTripletYoffset(chord["note"]["string"], stringOfThirdTripletOfCurrentChord)
    chordRendering = env.get_template("chord.mscx").render(
        duration = chord["duration"],
        hasBox = chord["hasBox"],
        hasAccent = chord["hasAccent"],
        articulationDirection = chord["articulation"],
        articulationYOffset = f'"{findArticulationOffset(chord)}"', 
        slur = chord["slur"],
        triplet = chord["triplet"],
        noteNoteOnStringFret = chord["note"]["noteOnString"],
        noteStringMinusOne = chord["note"]["string"] - 1 if chord["note"]["string"] else None,
        headerFingering = chord["headerFingering"],
        stringFingeringTypeFingering = chord["stringFingering"]["typeFingering"],
        pitch = findNotePitch(chord["note"]["noteOnString"], chord["note"]["string"]),
        doubleBeamBreaking = isBeamBreaking(chordIdx, userInputtedValues['doubleBeamBreakRanges'][notationPageIdx]),
        singleBeamBreaking = isBeamBreaking(chordIdx, userInputtedValues['singleBeamBreakRanges'][notationPageIdx]),
        stemYOffsetFingeringOffset = f'"{stemYOffsetStemLengthFingeringOffset}"',
        stemYOffsetFingeringOffsetWithouNoteOffset = f'"{stemYOffsetStemLengthFingeringOffset - (1.5*(chord["note"]["string"]-1) if chord["note"]["string"] else 0)}"', 
        stemLength = stemYOffsetStemLengthFingeringOffset,
        firstTripletYoffset = f'"{firstTripletYoffset}"',
        thirdTripletYoffset = f'"{thirdTripletYoffset}"'
        )
    return chordRendering


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
            measureFrameText += str(measureIndex + 1) # Because we start from 0
    return measureFrameText


def renderMeasure(env, measureIndex, measure, notationPageIndex, userValues, timeSignNumerator, timeSignDenominator):
    renderedChords = ""
    # Measures contain multiple chords that should be rendered first.
    for chordIndex, chord in enumerate(measure["chords"], start = 1):
        # if this is the first note of the triplet and the third one exist then return the string of the third one
        # third one's index is chordIndex + 1 because we start enumeration from 1, therefore the indexes are one unit ahead.
        # So, in order to reach 2 chords down, we use chordIndex + 1
        if chord["triplet"] == 1 and measure["chords"][chordIndex+1]:
            stringOfThirdTriplet = measure["chords"][chordIndex+1]["note"]["string"]
        else:
            stringOfThirdTriplet = None
        renderedChords += renderChords(env, chord, chordIndex, notationPageIndex, userValues, stringOfThirdTriplet)
    
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


def renderBook(JSON, values, doubleBeamBreaks, singleBeamBreaks):
    # Load the Set Values of the book.
    setValues = loadValues(values, doubleBeamBreaks, singleBeamBreaks)

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
            "singleHeading": [],
            "doubleHeading": [*range(1,8)]
        },
        "sideFrameTextExistence" : {
            "sideFrameTextExistencePages" : [],
            "sameFrameTextInMultiMeasuredRow" : [],
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
    doubleBeamBreaks  = {
        "pattern1" : {
            "pages" : [range(1,2)],
            "beamBreaks" : [5,10]
        },
        "pattern2" : {
            "pages" : [range(2,3)],
            "beamBreaks" : [7,16]
        },
        "pattern3" : {
            "pages" : [range(3,200)],
            "beamBreaks" : [9]
        }
    }
    singleBeamBreaks  = {
        "pattern1" : {
            "pages" : [range(1,2)],
            "beamBreaks" : [13]
        },
        "pattern2" : {
            "pages" : [range(2,3)],
            "beamBreaks" : [9,11]
        },
        "pattern3" : {
            "pages" : [range(3,200)],
            "beamBreaks" : [15]
        }
    }


    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    renderBook(JSON_book_directory, values, doubleBeamBreaks, singleBeamBreaks)