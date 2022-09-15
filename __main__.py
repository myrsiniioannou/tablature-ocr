import sys
from header_repeater import headerRepeater
sys.path.append('modules')

from measure_detection_and_extraction import *
from measure_analysis import *
from book_parser import *


if __name__ == '__main__':
    # 1st Step - Exctract Measures
    bookDirectory = r"../books_to_analyze/book1"
    measureDetectionAndExtraction(bookDirectory)
    
    
    # 2nd Step - Analyze measures and create dfs for each one
    model_path = r"../model/model2.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings)



    ############HEREE--------------------------------------------------------------
    # 3rd Step - Header Repeater
    headerRepeater()

    # 4th Step - Parse Book
    parseBook(bookDirectory, numberOfStrings)

    # 5th Step - Render Book

    
    
    print("Book Done!")
