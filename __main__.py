import sys
import os
sys.path.append('modules')
from measure_detection_and_extraction import *
from measure_analysis import *
from header_repeater import headerRepeater
from book_parser import *
from book_renderer import *


if __name__ == '__main__':


    # ENTER THE BOOK FILE IN FOLDER "BOOKS TO ANALYZE" and NUMBER OF STRINGS
    bookFile = "book1"
    numberOfStrings = 6
    pagesWithHeader = [
        {"chapter": 1, "unit": 1, "page": 1},
        {"chapter": 1, "unit": 2, "page": 3}
    ]


    # 1st Step - Exctract Measures
    bookDirectory = os.path.join(r"../books_to_analyze/",  bookFile)
    measureDetectionAndExtraction(bookDirectory)

    # 2nd Step - Analyze measures and create dfs for each one
    model_path = r"../model/model2.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = os.path.join(r"../extracted_measures/",  bookFile)
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings)
    
    # 3rd Step - Header Repeater
    headerRepeater(extractedBookDirectory, pagesWithHeader)

    # 4th Step - Parse Book
    parseBook(bookDirectory, numberOfStrings)

    # 5th Step - Render Book
    JSON_book_directory = os.path.join(r"../JSON_book_outputs/",  bookFile)
    renderBook(JSON_book_directory)
    
    print("Book Done!")
    
    
