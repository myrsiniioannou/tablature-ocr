

def loadValues():
    # Set Values on paragraphs, headings, measures, and side frame text
    # PAGE NUMBERS HERE ARE THE SAME AS IN THE BOOK. Don't deduct 1 to start from 0.
    values = {
        "timeSignature" : {
            "twoFour": {       
                "pages": [*range(1,3)],
                "numerator": 2 ,
                "denominator": 4
            },
            "fourFour": {       
                "pages": [*range(3,5)],
                "numerator": 4 ,
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
            "singleHeading": [*range(4,18), *range(30,40)],
            "doubleHeading": [*range(1,4), *range(18,30)]
        },
        "sideFrameTextExistence" : {
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
        "beamBreaks" : [*range(4,18), *range(30,40)],
    }

    pageBreakPatterns  = {
        "pattern1" : {
            "pages" : [range(1,2)],
            "pageBreaks" : [5,8]
        },
        "pattern2" : {
            "pages" : [range(2,3)],
            "pageBreaks" : [7,16]
        },
        "pattern3" : {
            "pages" : [range(3,50)],
            "pageBreaks" : [9]
        }
    }


    
    values["pageBreaksRanges"] = findPageBreaks(pageBreakPatterns)
    return values

def findPageBreaks(patterns):
    pageBreaksRanges = dict()
    for pattern, vals in patterns.items():
        for pageRange in vals["pages"]:
            for page in pageRange:
                pageBreaksRanges[page] = vals["pageBreaks"]
    return pageBreaksRanges



diction = loadValues()
print(diction['pageBreaksRanges'])
