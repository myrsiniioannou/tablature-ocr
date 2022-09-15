from pathlib import Path
import os
from book_parser import splitFolderName


def headerRepeater(directory, headerPages: dict):

    # Iterate through files and folders
    for root, dirs, measures in os.walk(directory):
        pagesWithHeaderCounter = 0
        
        for measure in measures:
            if measure.endswith('.csv'):

                
                print("measure: ", measure)
                measureNumber = measure[:2]
                print("root: ", root)
                chapter = os.path.basename(Path(root).parents[1])
                unit = os.path.basename(Path(root).parents[0])
                page = os.path.basename(root)

                sectionList = [chapter, unit, page]
                sectionListWithoutText = []
                for section in sectionList:
                    sectionTitle, sectionNumber = splitFolderName(section)
                    
                    if sectionNumber[0] == "0":
                        sectionNumber = sectionNumber[1:]
                    sectionNumber = int(sectionNumber)
                    sectionListWithoutText.append(sectionNumber)


                print("chapter: ", chapter)
                print("chapter number:", sectionListWithoutText[0]) # chapter
                print("unit: ", sectionListWithoutText[1]) # unit 
                print("page: ", sectionListWithoutText[2]) # page
                


                if ((headerPages[pagesWithHeaderCounter]["chapter"] == sectionListWithoutText[0]) and
                    (headerPages[pagesWithHeaderCounter]["unit"] == sectionListWithoutText[1]) and
                    (headerPages[pagesWithHeaderCounter]["page"] == sectionListWithoutText[2])):
                    print("--->PAGE WITH HEADER<---")
                                    
                    pagesWithHeaderCounter+=1

                print('headerPages[pagesWithHeaderCounter]["chapter"]: ', headerPages[pagesWithHeaderCounter]["chapter"])
                print('headerPages[pagesWithHeaderCounter]["unit"]: ', headerPages[pagesWithHeaderCounter]["unit"])
                print('headerPages[pagesWithHeaderCounter]["page"]: ', headerPages[pagesWithHeaderCounter]["page"])
                print("sectionListWithoutText: ", sectionListWithoutText)
                print("-------------------")
                #TO MEASURE DEN TO THELOUME STO DICTIONARY ALLA TO THELOUME ENTOS GIA THN APOTHIKEYSH



    
            # ta measures pou ginontai copies prepei na exoun to idio noumero (giati mporei na exoume error)
            # opote na to tsekarei auto h malakia

if __name__ == '__main__':

    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    
    pagesWithHeader = [
        {"chapter": 1, "unit": 1, "page": 1},
        {"chapter": 1, "unit": 1, "page": 2}
    ]



    headerRepeater(extractedBookDirectory, pagesWithHeader)
