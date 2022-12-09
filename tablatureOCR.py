import shutup; shutup.please()
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
            "12" : {
                "pages": [*range(1,347)],
            }
        },
        "fingeringNumber": {
            "20": {
                "pages": [*range(1,3)],
            },
            "32": {
                "pages": [*range(1,150)],
            },
            "40": {
                "pages": [*range(150,180),*range(317347)],
            },
            "28": {
                "pages": [*range(180,317)],
            }
        },
        "chordNumber": {
            "32": {
                "pages": [*range(1,347)],
            }
        },
        "headerNumber": {
            "32": {
                "pages": [*range(1,347)],
            }
        },
        "headerExistence": {
            True: {
                "pages": [*range(1,347)],
            }#,
            #False : {
                #"pages": [*range(3,6)],
            #}
        },
        "noteStringExistence": {
            True: {
                "pages": [*range(1,347)],
            }#,
            #False : {
                #"pages": [*range(3,6)],
            #}
        },
        "noteStrings": {
            "1": {
                "pages": [*range(1,347)],
            }#,
            #"2" : {
            #    "pages": [*range(3,6)],
            #}
        }
    }

    # 2. Headery Repeater Values
    headerRepeaterValues = {
        "wholePageRepeat" : [], # Put the pages that we want to use as a template for the next ones. Ie if we want to copy page 1 to 2,3,4 then put [1] 
        "firstRowRepeat" : [*range(1,347)],
        "columnRepeat" : [],
        "partialHeaderRepeat" : {
            #"Pattern1" : {
            #    "pages" : [*range(1,347)],
            #    "headerElementsToRepeat" : [*range(4,9)],
            #}#,
            #"Pattern2" : {
            #    "pages" :[3, 4],
            #    "headerElementsToRepeat" : [1,2,3]
            #}
        },
        "patternRepeat" : {
            "Pattern1" : {
                "pages" : [*range(1,347)],
                "elementIndex" : [*range(4,9)],
                "fingeringPattern" : ["p", "p", "p", "p", "p"]
            }#,
            #"Pattern2" : {
            #    "pages" : [3],
            #    "elementIndex" : [9,10,11,12,13],
            #    "fingeringPattern" : ["t", "t", "t", "t", "t"]
            #},
            #"Pattern3" : {
            #    "pages" : [4,5,6],
            #    "elementIndex" : [14,15,16],
            #    "fingeringPattern" : ["q", "q", "q", "q", "q"]
            #}
        }
    }

    # 3. Book Parser Values
    measureValues = {
        "valueSet1" : {
            "pages": [*range(1,150), *range(180, 317)],
            'chordDurationInteger': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'triplet': [1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0],
            'articulation': [None, None, None, None, None, None, "up", "down", None, None, None, None, None, None, "up", "down", None, None, None, None, None, None, "up", "down", None, None, None, None, None, None, "up", "down"],
            'slur': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasBox': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasAccent': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        },
        "valueSet2" : {
            "pages": [*range(150,180),*range(317,347)],
            'chordDurationInteger': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'triplet': [1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0, 1, 2, 3, 1, 2, 3, 0, 0],
            'articulation': [None, None, None, "up", "down", "up", "up", "down", None, None, None, "up", "down", "up", "up", "down", None, None, None, "up", "down", "up", "up", "down", None, None, None, "up", "down", "up", "up", "down"],
            'slur': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasBox': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'hasAccent': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
        # "valueSet3" : {
        #     "pages": [*range(4,6)],
        #     'chordDurationInteger': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        #     'triplet': [1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0, 1, 2, 3, 0, 0],
        #     'articulation': ["up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down", "up", "down"],
        #     'slur': [0, 1, 2, 0, 0, 0, 1, 0, 2, 0, 0, 0, 1, 2, 0, 0, 1, 0, 2, 0],
        #     'hasBox': [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        #     'hasAccent': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]
        # }
    } 

    # 4. Book Renderer Values
    bookValues = {
        "timeSignature" : {
            #"fourFour": {       
            #    "pages": [*range(1,6)],
            #    "numerator": 4,
            #    "denominator": 4
            #}
            "twelveEighths": {       
               "pages": [*range(1,347)],
               "numerator": 12,
               "denominator": 8
            }
        },
        "measures" : {
            "Horizontal": 2,
            "Vertical" : 6
        },
        "paragraphs" : {
            "IA": [1,31, 60, 90, 120, 150, 180, 209, 235, 263, 290, 317],
            "IIA": [4, 63, 93, 123, 153, 183, 212, 238, 266, 293, 320],
            "IIIA": [7, 37, 66, 96, 126, 156, 213, 241, 269, 296, 323],
            "IVA": [10, 39, 69, 99, 129, 159, 216, 243, 273, 299, 326],
            "VA": [1, 42, 72, 102, 132, 162, 192, 219, 246, 302, 329],
            "IB": [16, 45, 75, 105, 135, 165, 195, 222, 249, 276, 305, 332],
            "IIB": [19, 48, 78, 108, 137, 168, 197, 225, 251, 279, 308, 335],
            "IIIB": [22, 51, 81, 111, 141, 171, 200, 226, 255, 282, 310, 338],
            "IVB": [25, 54, 84, 114, 144, 173, 203, 229, 257, 313, 341],
            "VB": [28, 57, 87, 117, 147, 177, 206, 232, 260, 287, 316, 344],
        },
        "headings" : {
            "singleHeading": [*range(1,347)],
            "doubleHeading": []
        },
        "sideFrameTextExistence" : {
            "sideFrameTextExistencePages" : [*range(1,347)],
            "sameFrameTextInMultiMeasuredRow" : [],
            "sideFrameLetter" : {
                "F" : [*range(1,347)]
                #"B" : [3,4,5,6,7]
            }
        },
        "headerLetter" : {
            "VARIATION 1" : [1,2,3, 16, 17, 18, 31, 33, 45, 46, 47],
            #"VARIATION 2" : [],
            #"VARIATION 3" : [],
            #"VARIATION 4" : [],
            #"VARIATION 5" : [],
        }
    }
    doubleBeamBreaks  = {
        "pattern1" : {
            "pages" : [*range(1,347)],
            "beamBreaks" : [16]
        }#,
        # "pattern2" : {
        #     "pages" : [range(2,3)],
        #     "beamBreaks" : [16]
        # },
        # "pattern3" : {
        #     "pages" : [range(3,200)],
        #     "beamBreaks" : [9]
        # }
    }
    singleBeamBreaks  = {
        "pattern1" : {
            "pages" : [*range(1,347)],
            "beamBreaks" : [8, 24]
        }# ,
        # "pattern2" : {
        #     "pages" : [range(2,3)],
        #     "beamBreaks" : [9,11]
        # },
        # "pattern3" : {
        #     "pages" : [range(3,200)],
        #     "beamBreaks" : [15]
        # }
    }


    # 1st Step - Exctract Measures
    bookDirectory = os.path.join(r"../books_to_analyze/",  bookFile)
    measureDetectionAndExtraction(bookDirectory)

    # 2nd Step - Analyze measures and create dfs for each one
    model_path = r"../model/model5Merged.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = os.path.join(r"../../extracted_measures/",  bookFile)
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings, pageValues)

    # 3rd Step - Header Repeater
    #print("Header Repeating Process Starting...")
    headerRepeater(extractedBookDirectory, headerRepeaterValues, bookValues["measures"])

    # 4th Step - Parse Book
    bookDirectoryForParsing = os.path.join(r"../extracted_measures", bookFile)
    parseBook(bookDirectoryForParsing, numberOfStrings, measureValues)

    # 5th Step - Render Book
    JSON_book_directory = os.path.join(r"../../JSON_book_outputs/",  bookFile)
    renderBook(JSON_book_directory, bookValues, doubleBeamBreaks, singleBeamBreaks)

    
    print("Book Done!")
    
    
