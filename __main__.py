import sys
import os
sys.path.append('modules')
from measure_detection_and_extraction import *
from measure_analysis import *
from header_repeater import headerRepeater
from book_parser import *
from book_renderer import *


if __name__ == '__main__':
    bookFile = "firstBook"
    numberOfStrings = 6
    
    # 1. Measure Analysis Values
    pageValues = {
        "stringNumber" : 6, 
        "noteNumber": {
            "8": {
                "pages": [*range(1,3)],
            },
            "10" : {
                "pages": [*range(3,4)],
            },
            "12" : {
                "pages": [*range(4,6)],
            }
        },
        "fingeringNumber": {
            "15": {
                "pages": [*range(1,3)],
            },
            "16" : {
                "pages": [*range(3,4)],
            },
            "17" : {
                "pages": [*range(4,6)],
            }
        },
        "chordNumber": {
            "15": {
                "pages": [*range(1,3)],
            },
            "16" : {
                "pages": [*range(3,4)],
            },
            "17" : {
                "pages": [*range(4,6)],
            }
        },
        "headerNumber": {
            "15": {
                "pages": [*range(1,3)],
            },
            "16" : {
                "pages": [*range(3,4)],
            },
            "17" : {
                "pages": [*range(4,6)],
            }
        },
        "headerExistence": {
            True: {
                "pages": [*range(1,3)],
            },
            False : {
                "pages": [*range(3,6)],
            }
        },
        "noteStringExistence": {
            True: {
                "pages": [*range(1,3)],
            },
            False : {
                "pages": [*range(3,6)],
            }
        },
        "noteStrings": {
            "1": {
                "pages": [*range(1,3)],
            },
            "2" : {
                "pages": [*range(3,6)],
            }
        }
    }

    # 2. Headery Reoeater Values
    headerRepeaterValues = {
        "wholePageRepeat" : [1, 3 ], # Put the pages that we want to use as a template for the next ones. Ie if we want to copy page 1 to 2,3,4 then put [1] 
        "firstRowRepeat" : [1, 2, 3, 4],
        "columnRepeat" : [1, 2, 3, 4],
        "partialHeaderRepeat" : {
            "Pattern1" : {
                "pages" :[1, 3],
                "headerElementsToRepeat" : [1,2,3,4,5]
            },
            "Pattern2" : {
                "pages" :[3, 4],
                "headerElementsToRepeat" : [1,2,3]
            }
        },
        "patternRepeat" : {
            "Pattern1" : {
                "pages" : [1,2],
                "elementIndex" : [4,5,6,7,8],
                "fingeringPattern" : ["e", "e", "e", "e", "e"]
            },
            "Pattern2" : {
                "pages" : [3],
                "elementIndex" : [9,10,11,12,13],
                "fingeringPattern" : ["t", "t", "t", "t", "t"]
            },
            "Pattern3" : {
                "pages" : [4,5,6],
                "elementIndex" : [14,15,16],
                "fingeringPattern" : ["q", "q", "q", "q", "q"]
            }
        }
    }

    # 3. Book Parser Values
    measureValues = {
        "valueSet1" : {
            "pages": [*range(1,3)],
            'chordDurationInteger': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'triplet': ["up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up", "up"],
            'articulation': [1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0],
            'slur': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'hasBox': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'hasAccent': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        },
        "valueSet2" : {
            "pages": [*range(3,4)],
            'chordDurationInteger': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'triplet': [1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0],
            'articulation': ["down", None, None, "down", None, None, None, "down", None, None, None, None, "down", None, None, "down", None, "down", None, None],
            'slur': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasBox': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasAccent': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        "valueSet3" : {
            "pages": [*range(4,6)],
            'chordDurationInteger': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            'triplet': [1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0],
            'articulation': ["up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down"],
            'slur': [0, 1, 2, 0, 0, 0, 1, 0, 2, 0, 0, 0, 1, 2, 0, 0, 1, 0, 2, 0],
            'hasBox': [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasAccent': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]
        }
    } 

    # 4. Book Renderer Values
    bookValues = {
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

    # 1st Step - Exctract Measures
    bookDirectory = os.path.join(r"../books_to_analyze/",  bookFile)
    measureDetectionAndExtraction(bookDirectory)

    # 2nd Step - Analyze measures and create dfs for each one
    model_path = r"../model/model3NEW.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = os.path.join(r"../extracted_measures/",  bookFile)
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings, pageValues)
    
    # 3rd Step - Header Repeater
    headerRepeater(extractedBookDirectory, headerRepeaterValues, bookValues["measures"])

    # 4th Step - Parse Book
    parseBook(bookDirectory, numberOfStrings)

    # 5th Step - Render Book
    JSON_book_directory = os.path.join(r"../JSON_book_outputs/",  bookFile)
    renderBook(JSON_book_directory, bookValues, doubleBeamBreaks, singleBeamBreaks)

    
    print("Book Done!")
    
    
