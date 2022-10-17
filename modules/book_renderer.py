
from domain_model import *
import json
from jinja2 import Environment, FileSystemLoader

def setValues():
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


def render(JSON):
    # Load JSON BOOK FILE
    with open(JSON, 'r') as f:
        bookInJsonFormat = json.load(f)
    file_loader = FileSystemLoader("templates")
    env = Environment(loader = file_loader)

    paragraphs, headings, measures, sideFrameTextExistence = setValues()



    render = env.get_template("book.mscx").render(
       NumberOfStrings = bookInJsonFormat["numberofstrings"],
       singleHeading = False, # YOU NEED TO CALCULATE THIS ACCORDING TO PAGES. EASY
       doubleHeading = True,
       paragraph = "I A",
       paragraphSymbol = "F",
       paragraphText1 = "1A",
       paragraphText2 = "1B",
       
       # Sideframe
       sideFrames = sideFrameTextExistence,
       sideFrameTextOnTheLeft = "F2",
       isMeasureFirstInRow = False, # YOU NEED TO CALCULATE THIS MOTHERFUCKER
       isMeasureLastInRow = False, # YOU NEED TO CALCULATE THIS - FOR VERTICAL BOX BREAK 
       isMeasureLastInPage = False, # YOU NEED TO CALCULATE THIS - PAGE BREAK 
       
       # Chords
       duration = ["16th", "eighth", "16th", "eighth"],
       slur = [0, 1, 2],
       isBeamContinued = True,
       triplet = 1
       )

    print(render)

    musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\bookRENDER.mscx"
    with open(f"{musescoreOutputFile}", "w") as f:
        f.write(render)







if __name__ == '__main__':
    #
    # YOU NEED TO GIVE SOME INPUT AT THE TOP OF THE CODE
    #
    #
    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    render(JSON_book_directory)