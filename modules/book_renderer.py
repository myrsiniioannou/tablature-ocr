
from domain_model import *
import json
from jinja2 import Environment, FileSystemLoader

def setParagraphPagesAndHeadings():
    paragraphs = {
        "IA":[1,4],
        "IB": [3,5]
    }
    headings = {
        "doubleHeading": [*range(1,8), *range(18,30)],
        "singleHeading": [*range(8,18), *range(30,40)]
    }
    return paragraphs, headings


def render(JSON):
    # Load JSON BOOK FILE
    with open(JSON, 'r') as f:
        bookInJsonFormat = json.load(f)
    file_loader = FileSystemLoader("templates")
    env = Environment(loader = file_loader)

    paragraphs, headings = setParagraphPagesAndHeadings()


    # ask for I Paragraph




    # FTIAKSE TO DICT TOU DATA SCTRUCTURE STH MORFH POY PREPEI GIA NA RENTAREIS META



    #render = env.get_template("base.mscx").render(
    #    NumberOfStrings = bookInJsonFormat["numberofstrings"],
    #    dataaa = 'CONTENT',
    #    variab = "Hello to you too")

    #print(render)

    #musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\book.mscx"
    ##with open(f"{musescoreOutputFile}", "w") as f:
    #    f.write(render)







if __name__ == '__main__':

    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    render(JSON_book_directory)