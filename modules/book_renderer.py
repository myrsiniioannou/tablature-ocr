
from domain_model import *
import json
from jinja2 import Environment, FileSystemLoader


def render(JSON):
    # Load JSON BOOK FILE
    with open(JSON, 'r') as f:
        bookInJsonFormat = json.load(f)
    file_loader = FileSystemLoader("templates")
    env = Environment(loader = file_loader)


    # FTIAKSE TO DICT TOU DATA SCTRUCTURE STH MORFH POY PREPEI GIA NA RENTAREIS META
    # DLD KANE TOUS YPOLOGISMOUS POU PREPEI

    #eatShit = env.get_template("content.mscx").render()

    render = env.get_template("base.mscx").render(
        NumberOfStrings = bookInJsonFormat["numberofstrings"],
        dataaa = 'CONTENT',
        variab = "Hello to you too")

    print(render)

#"""
#musescoreOutputFile = r"C:\Users\merse\Desktop\Tablature OCR\final_musescore_outputs\book.mscx"
##with open(f"{musescoreOutputFile}", "w") as f:
#    f.write(render)
#"""







if __name__ == '__main__':

    JSON_book_directory = r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs\book1.json"
    render(JSON_book_directory)