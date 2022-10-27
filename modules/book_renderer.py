from domain_model import *
import json
from jinja2 import Environment, FileSystemLoader


def loadValues():
    # Set Values on paragraphs, headings, measures, and side frame text
    # PAGE NUMBERS HERE ARE THE SAME AS IN THE BOOK. Don't deduct 1 to start from 0.
    values = {
        "paragraphs" : {
            "IA":[1,10],
            "IB": [6,20]
        },
        "headings" : {
            "doubleHeading": [*range(1,8), *range(18,30)],
            "singleHeading": [*range(8,18), *range(30,40)]
        },
        "sideFrameTextExistence" : [*range(1,8), *range(18,30)],
        "headerLetter" : {
            "F" : [*range(1,41)]
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
    #    duration = "16th", #"eighth",
    #    slur = 0,
    #    isBeamContinued = True, # YOU NEED TO CALCULATE THIS 
    #    triplet = 0,
    #    articulationDirection = "up",
    #    articulationYOffset = -5, # YOU NEED TO CALCULATE THE OFFSET ACCORDING TO THE NOTEE
    #    # TO ARTICULATION EINAI -5 OTAN EXEI STEM ME STRING FINGERING
    #    # TO STEM SYSXETIZETAI KAPOS ME TO OFFSET TOU STRING FINGERING
    #    hasAccent = False,
    #    stemYoffset = 7.6, # YOU NEED TO CALCULATE THIS 
    #    stemLength = 7.5, # YOU NEED TO CALCULATE THIS 
    #    stringFingeringStringOffset = 7.6, # YPOLOGIZETAI ANALOGA ME THN KATHE XORDH
    #    # KAI ISOS TO POIO GRAMMA EXEI PANO. H KATHE XORDH EXEI ENA SYGKEKRIMENO OFFSET.
    #    # KANE TEST
    #    # paizei na sxetizetai me to stemYoffset
    #    stringFingeringTypeFingering = "p",
    #    headerFingering = "p",
    #    noteOnStringFret = 1,
    #    pitch = whichStringPitch + noteOnStringFret, # to whichStringPitch einai to pitch ths ekastote xordhs + TO FRET
    #    whichStringMinusOne = 0
    #    )



    return ""


def renderMeasure(env, measures):
    renderedChords = ""
    # Measures contain multiple chords that should be rendered first.
    for chord in measures["chords"]:
        renderedChords += renderChords(env, chord)
    chordRendering = env.get_template("measure.mscx").render(chordContent = renderedChords)
    return chordRendering








def renderNotationPage(env, notationPageIdx, notationPage, userInputtedValues):




    renderedMeasures = ""
    # Notation Pages contain multiple measures that should be rendered first.
    for measure in notationPage["measures"]:
        renderedMeasures += renderMeasure(env, measure)
    



    print("pageIndex:", notationPageIdx)
    print(notationPageIdx in userInputtedValues["paragraphs"]["IA"])
    print(notationPageIdx in userInputtedValues["paragraphs"]["IB"])
    print(notationPageIdx in userInputtedValues["headings"]["singleHeading"])
    print(notationPageIdx in userInputtedValues["headings"]["doubleHeading"])
    print(notationPageIdx in userInputtedValues["headerLetter"]["F"])
    print(notationPageIdx in userInputtedValues["sideFrameTextExistence"])

    print(userInputtedValues["measures"]["Horizontal"])
    print(userInputtedValues["measures"]["Vertical"])


    if notationPageIdx in userInputtedValues["paragraphs"]["IA"]:
        paragraphText = "IA"
    elif notationPageIdx in userInputtedValues["paragraphs"]["IB"]:
        paragraphText = "IB"
    else:
        paragraphText = "  "


    if notationPageIdx in userInputtedValues["headerLetter"]["F"]:
        header_letter = "F"
    else:
        header_letter = "  "
    



    def findHeadingTexts(notationPageIdx, paragraphText):

        pass

    if notationPageIdx in userInputtedValues["headings"]["singleHeading"]:
        pass



    print("---------------------------------")


    notationPageRendering = env.get_template("notationPage.mscx").render(
        measureContent = renderedMeasures,

        singleHeading = notationPageIdx in userInputtedValues["headings"]["singleHeading"],
        doubleHeading = notationPageIdx in userInputtedValues["headings"]["doubleHeading"],
        paragraph = paragraphText, # IA or IB
        headerLetter = header_letter,


        heading1Text, heading2Text = findHeadingTexts(notationPageIdx, paragraphText),

        heading1Text = "1" + paragraphText[-1],# YOU NEED TO CALCULATE THIS
        heading2Text = "2" + paragraphText[-1],# YOU NEED TO CALCULATE THIS
        


    #     # Sideframe
    #     sideFrames = sideFrameTextExistence,# YOU NEED TO CALCULATE THIS
    #     sideFrameTextOnTheLeft = "F2",# YOU NEED TO CALCULATE THIS


    
    #     isMeasureFirstInRow = False, # YOU NEED TO CALCULATE THIS
    #     isMeasureLastInRow = False, # YOU NEED TO CALCULATE THIS - FOR VERTICAL BOX BREAK 
    #     isMeasureLastInPage = False, # YOU NEED TO CALCULATE THIS - PAGE BREAK 
        
        
)
    return  "" #notationPageRendering


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