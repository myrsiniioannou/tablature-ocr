from stat import SF_APPEND
from tkinter.messagebox import NO
from matplotlib.dviread import Box
from soupsieve import closest
from domain_model import *
import json
import copy
from jinja2 import Environment, FileSystemLoader


def loadValues():
    # Set Values on paragraphs, headings, measures, and side frame text
    # PAGE NUMBERS HERE ARE THE SAME AS IN THE BOOK. Don't deduct 1 to start from 0.
    values = {
        "paragraphs" : {
            "IA": [1, 8],
            "IB": [5, 6]
        },
        "headings" : {
            "singleHeading": [*range(4,18), *range(30,40)],
            "doubleHeading": [*range(1,4), *range(18,30)]
        },
        "sideFrameTextExistence" :{
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
        },
        "measures" : {
            "Horizontal": 2,
            "Vertical" : 6
        }
    }
    return values


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





def renderChords(env, chord):


    #print(chord)
    #print("---------------------------------")

    #generateDataTransferObject

    # DATA TRANSFER OBJECT FUNCTION


    # chord = env.get_template("chord.mscx").render(

       
    #    # Chords


    # 1  duration = "16th", #"eighth",


    # 2  slur = 0,


    # 3  isBeamContinued = True, # YOU NEED TO CALCULATE THIS 

    # 4  triplet = 0,


    # 5  articulationDirection = "up",


    # 6  articulationYOffset = -5, # YOU NEED TO CALCULATE THE OFFSET ACCORDING TO THE NOTEE
    #    # TO ARTICULATION EINAI -5 OTAN EXEI STEM ME STRING FINGERING
    #    # TO STEM SYSXETIZETAI KAPOS ME TO OFFSET TOU STRING FINGERING


    # 7  hasAccent = False,



    # 8  stemYoffset = 7.6, # YOU NEED TO CALCULATE THIS 



    # 9  stemLength = 7.5, # YOU NEED TO CALCULATE THIS 



    # 10 stringFingeringStringOffset = 7.6, # YPOLOGIZETAI ANALOGA ME THN KATHE XORDH
    #    # KAI ISOS TO POIO GRAMMA EXEI PANO. H KATHE XORDH EXEI ENA SYGKEKRIMENO OFFSET.
    #    # KANE TEST
    #    # paizei na sxetizetai me to stemYoffset



    # 11 stringFingeringTypeFingering = "p",


    # 12 headerFingering = "p",


    # 13 noteOnStringFret = 1,


    # 14 pitch = whichStringPitch + noteOnStringFret, # to whichStringPitch einai to pitch ths ekastote xordhs + TO FRET


    # 15 whichStringMinusOne = 0
    #    )



    return ""



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



def renderMeasure(env, measureIndex, measure, notationPageIndex, userValues):
    renderedChords = ""
    # Measures contain multiple chords that should be rendered first.
    for chord in measure["chords"]:
        renderedChords += renderChords(env, chord)
    measureRendering = env.get_template("measure.mscx").render(
        chordContent = renderedChords,
        sideFrameText = findSideFrameTextOfMeasure(measureIndex, notationPageIndex, userValues)
        )
  
    #     isMeasureFirstInRow = False, # YOU NEED TO CALCULATE THIS    
    #     isMeasureLastInRow = False, # YOU NEED TO CALCULATE THIS - FOR VERTICAL BOX BREAK  
    #     isMeasureLastInPage = False, # YOU NEED TO CALCULATE THIS - PAGE BREAK 
       

    # FTIAKSE TO horizontal kaiiiii to vertical BOXXXXXXXXX


    return ""#measureRendering


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


def renderNotationPage(env, notationPageIdx, notationPage, userInputtedValues):
    renderedMeasures = ""
    # Notation Pages contain multiple measures that should be rendered first.
    for measureIndex, measure in enumerate(notationPage["measures"]):
        renderedMeasures += renderMeasure(env,measureIndex, measure, notationPageIdx, userInputtedValues)
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
    # musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\renderedBook.mscx"
    # with open(f"{musescoreOutputFile}", "w") as f:
    #     f.write(output)





if __name__ == '__main__':
    #
    # YOU NEED TO GIVE SOME INPUT AT THE TOP OF THE CODE
    #
    #
    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    renderBook(JSON_book_directory)