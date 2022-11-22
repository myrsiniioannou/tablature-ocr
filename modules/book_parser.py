import os
import pandas as pd
from pathlib import Path
import json
from domain_model import *
import copy


def pageData(pageIdx, measureValues):
    setValueKey = ""
    for key, value in measureValues.items():
        if pageIdx in value["pages"]:
            setValueKey = copy.deepcopy(key)
            break
    if setValueKey:
        data = {
        'chordDurationInteger': measureValues[setValueKey]["chordDurationInteger"],
        'triplet': measureValues[setValueKey]["triplet"],
        'articulation': measureValues[setValueKey]["articulation"],
        'slur': measureValues[setValueKey]["slur"],
        'hasBox': measureValues[setValueKey]["hasBox"],
        'hasAccent': measureValues[setValueKey]["hasAccent"]
        }
    else:
        data = {}
    return data


def pathToFile(mainDirectory, rootOfDirectory, measureCSV):
    chapterDir = os.path.basename(Path(rootOfDirectory).parents[1])
    unitDir = os.path.basename(Path(rootOfDirectory).parents[0])
    pageFolder = (os.path.basename(rootOfDirectory))
    path_to_df = os.path.join(mainDirectory,chapterDir, unitDir, pageFolder, measureCSV)
    return path_to_df


def findDuration(durationInteger):
    if durationInteger == 0:
        duration = ChordDuration.SIXTEENTH
    elif durationInteger == 1:
        duration = ChordDuration.EIGHTH
    elif durationInteger == 2:
        duration = ChordDuration.QUARTER
    elif durationInteger == 3:
        duration = ChordDuration.HALF
    elif durationInteger == 4:
        duration = ChordDuration.WHOLE
    return duration


def findNote(mdf, idx):
    note = mdf[(mdf["Label"].str.isdigit()) & (mdf["Position"]==idx)]
    note = note["Label"].to_numpy()
    note = note.astype(int)
    return note.item(0) if note.size != 0 else None
    

def findNoteString(mdf, idx):
    noteString = mdf[(mdf["Label"].str.isdigit()) & (mdf["Position"]==idx)]
    noteString = noteString["String"].to_numpy()
    noteString = noteString.astype(int)
    return noteString.item(0) if noteString.size != 0 else None


def fingeringDecoding(mdf,idx, headerOrNot):
    if headerOrNot:
        fingeringList = mdf[(mdf["Position"]==idx) & (mdf["String"]==0) & (~mdf["Label"].str.isdigit())]["Label"]
    else:
        fingeringList = mdf[(mdf["Position"]==idx) & (mdf["String"]!=0) & (~mdf["Label"].str.isdigit())]["Label"]
    fingeringList = fingeringList.to_numpy()
    if fingeringList.size != 0:
        if fingeringList[0]=="p":
            fingering = FingeringType.P
        elif fingeringList[0]=="i":
            fingering = FingeringType.I
        elif fingeringList[0]=="m":
            fingering = FingeringType.M
        elif fingeringList[0]=="a":
            fingering = FingeringType.A
        elif fingeringList[0]=="dot":
            fingering = FingeringType.DOT
    else:
        fingering = None
    return fingering


def findStringFingering(mdf, idx):
    stringFingering = mdf[(mdf["Position"]==idx) & (mdf["String"]!=0) & (~mdf["Label"].str.isdigit())]
    stringFingering = stringFingering["String"].to_numpy().astype(int)
    return int(stringFingering[0]) if stringFingering.size != 0 else None


def findArticulation(inputData):
    if inputData == "up":
        articulation = Articulation.UP
    elif inputData == "down":
        articulation = Articulation.DOWN
    else:
        articulation = None
    return articulation


def parseMeasure(mdf, UserInputData):
    measure = []
    amountOfChords = int(mdf["Position"].max() + 1)
    for chordIndex in range(amountOfChords):
        headerFingeringType = fingeringDecoding(mdf, chordIndex, headerOrNot=True)
        stringFingeringTypeFingering = fingeringDecoding(mdf, chordIndex, headerOrNot=False)
        # Create a chord object for each chordIndex/Position (in df)
        chord = Chord(
            duration = findDuration(UserInputData["chordDurationInteger"][chordIndex]),
            hasBox = False if UserInputData["hasBox"][chordIndex] == 0 else True, 
            hasAccent = False if UserInputData["hasAccent"][chordIndex] == 0 else True,
            articulation = findArticulation(UserInputData["articulation"][chordIndex]),
            slur = UserInputData["slur"][chordIndex],
            triplet = UserInputData["triplet"][chordIndex],
            note = Note(noteOnString = findNote(mdf,chordIndex), string = findNoteString(mdf,chordIndex)),
            headerFingering = FingeringType(headerFingeringType) if headerFingeringType else None,
            stringFingering = StringFingering(string = findStringFingering(mdf, chordIndex),
            typeFingering = FingeringType(stringFingeringTypeFingering) if stringFingeringTypeFingering else None)
            )
        measure.append(chord)
    return measure


def splitFolderName(directoryName):
    head = directoryName.rstrip('0123456789')
    tail = directoryName[len(head):]
    return head, tail 


def parseSectionPage(rootFolder):
    baseName = os.path.basename(Path(rootFolder))
    if baseName.startswith("chapter") or baseName.startswith("unit"):
        folderName, folderNumber = splitFolderName(baseName)
        folderName = folderName[0].upper() + folderName[1:]
        if folderNumber[0]=="0":
            folderNumber = folderNumber[1:]
        sectionPageTitle = ' '.join([folderName, folderNumber])
    else:
        sectionPageTitle = None
    return sectionPageTitle


def parseNotationPage(directory, root, measures, notationPageNumber, measureValues):
    notationPageContent = []
    dataInput = {}
    dataInput = pageData(notationPageNumber, measureValues)
    for measure in measures:
        if measure.endswith('.csv') and dataInput:
            filePath = pathToFile(directory, root, measure)                
            #print(f"Parsing file: {filePath}")
            df = pd.read_csv(filePath)
            measureOutput = Measure(parseMeasure(df, dataInput))
            notationPageContent.append(measureOutput)
    return notationPageContent


def parseBook(directory, stringNumber, measureValues):
    print("Starting the parsing process..")
    bookPages = []
    notationPageNumber = 1
    for root, dirs, measures in os.walk(directory):
        # Section Page
        sectionPageTitle = parseSectionPage(root)
        if sectionPageTitle:
            sectionPage = SectionPage(sectionpagetitle = sectionPageTitle)
            page = Page(sectionpage = sectionPage)
            bookPages.append(page)
        # Notation Page
        notationPageContent = parseNotationPage(directory, root, measures, notationPageNumber, measureValues)
        if notationPageContent:
            notationPage = NotationPage(measures = notationPageContent)
            page = Page(notationpage = notationPage)
            bookPages.append(page)
            notationPageNumber += 1

    book = Book(numberofstrings = stringNumber, pages = bookPages)
    bookDict = vars(book)
    jsonFileName = os.path.basename(Path(directory)) +'.json'
    outputDirectory = os.path.join(r"C:\Users\merse\Desktop\Tablature OCR\JSON_book_outputs", jsonFileName)
    with open(outputDirectory, 'w', encoding='utf-8') as f:
        json.dump(bookDict, f, indent=3, default=vars, ensure_ascii=False)
    print("Parsing Done!")

              

if __name__ == '__main__':

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


    bookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book3"
    numberOfStrings = 6
    parseBook(bookDirectory, numberOfStrings, measureValues)






    """
    chord1 = Chord(positionInMeasure=0, duration='16th', note=60, articulation= "up", stringFingering='i',)
    chord2 = Chord(positionInMeasure=1, duration='16th', note=62, headerFingering='i', articulation= "down", hasBox=True, hasAccent=True)
    chord3 = Chord(positionInMeasure=2, duration='eighth', note=66, headerFingering='m', stringFingering='p', slur=1, hasBox=False, hasAccent=False, triplet=1)
    measure1 = Measure(3, [chord1, chord2, chord3])
    measure2 = Measure(4, [chord2, chord3 ,chord1, chord3])
    measure3 = Measure(6, [chord2, chord3 ,chord1, chord3, chord2, chord1])
    measure4 = Measure(2, [chord2, chord1])
    notationpage1 = NotationPage(4, [measure1, measure2, measure3, measure4])
    notationpage2 = NotationPage(5, [measure3, measure2, measure3, measure1, measure4])

    sectionpage1 = SectionPage("Chapter")
    sectionpage2 = SectionPage("Unit")

    page1 = Page(notationpage=notationpage1)
    page2 = Page(notationpage=notationpage2)
    page3 = Page(sectionpage=sectionpage1)
    page4 = Page(sectionpage=sectionpage2)

    book1 = Book(numberOfStrings=6, page = [page1, page2, page3, page4])

    print(json.dumps(book1, indent=3, default=vars))
    """
