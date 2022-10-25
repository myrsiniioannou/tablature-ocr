
from domain_model import *
import json
from jinja2 import Environment, FileSystemLoader


def setValues():
    # Set Values on paragraphs, headings, measures, and side frame text
    paragraphs = {
        "I A":[1,4],
        "I B": [3,5]
    }
    headings = {
        "doubleHeading": [*range(1,8), *range(18,30)],
        "singleHeading": [*range(8,18), *range(30,40)]
    }
    measures = {
        "Horizontal": 2,
        "Vertical" : 6
    }
    sideFrameTextExistence = True
    return paragraphs, headings, measures, sideFrameTextExistence


def loadJSON(JSONFile):
    with open(JSONFile, 'r') as f:
        book = json.load(f)
    return book


def templateLoading():
    file_loader = FileSystemLoader("templates")
    env = Environment(loader = file_loader)
    return env


def initializeBookRendering(env, JSONbook):
    bookStart = env.get_template("book_start.mscx").render(
    NumberOfStrings = JSONbook["numberofstrings"]
    )
    return bookStart



def finalizeBookRendering(env):
    bookEnd = env.get_template("book_end.mscx").render()
    return bookEnd


def renderSectionPage(env, content):
    sectionPageTitle = content["sectionpagetitle"].upper()
    sectionPageRendering = env.get_template("section_page.mscx").render(pageTitle = sectionPageTitle)
    return sectionPageRendering


def renderNotationPage(env, content):
    print(content["measures"])








def renderBook(JSON):
    # Load JSON Book File
    bookInJsonFormat = loadJSON(JSON)

    # Template Loading
    environment = templateLoading()

    # Set Values on paragraphs, headings, measures, and side frame text
    paragraphs, headings, measures, sideFrameTextExistence = setValues()

    # Initialize the book and append rendered book_start
    bookRendering = initializeBookRendering(environment, bookInJsonFormat)





    # 3. For every page in JSON file, render notation and section pages

    for pageList in bookInJsonFormat["pages"]:
        for pageType, pageContent in pageList.items():
            if pageType == "sectionpage" and pageContent:
                bookRendering += renderSectionPage(environment, pageContent)
            elif pageType == "notationpage" and pageContent:
                #bookRendering += renderNotationPage(environment, pageContent)
                renderNotationPage(environment, pageContent)
            print("---------------------------------------------------------")






    #generateDataTransferObject

    # DATA TRANSFER OBJECT FUNCTION


    # render = env.get_template("notationPage.mscx").render(
    #    singleHeading = False, # YOU NEED TO CALCULATE THIS ACCORDING TO PAGES. EASY
    #    doubleHeading = True,
    #    paragraph = "I A",
    #    paragraphSymbol = "F",
    #    paragraphText1 = "1A",
    #    paragraphText2 = "1B",
       
    #    # Sideframe
    #    sideFrames = sideFrameTextExistence,
    #    sideFrameTextOnTheLeft = "F2",
    #    isMeasureFirstInRow = False, # YOU NEED TO CALCULATE THIS MOTHERFUCKER
    #    isMeasureLastInRow = False, # YOU NEED TO CALCULATE THIS - FOR VERTICAL BOX BREAK 
    #    isMeasureLastInPage = False, # YOU NEED TO CALCULATE THIS - PAGE BREAK 
       
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






    # Finalizing book rendering by appending the end template
    bookRendering += finalizeBookRendering(environment)






    #print(bookRendering)





    # Save musescore file
    # musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\bookRendering.mscx"
    # with open(f"{musescoreOutputFile}", "w") as f:
    #     f.write(bookRendering)



if __name__ == '__main__':
    #
    # YOU NEED TO GIVE SOME INPUT AT THE TOP OF THE CODE
    #
    #
    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    renderBook(JSON_book_directory)