import os
import pandas as pd
from pathlib import Path
from domain_model import *

def pathToFile(mainDirectory, rootOfDirectory, measureCSV):
    chapterDir = os.path.basename(Path(rootOfDirectory).parents[1])
    unitDir = os.path.basename(Path(rootOfDirectory).parents[0])
    pageFolder = (os.path.basename(rootOfDirectory))
    path_to_df = os.path.join(mainDirectory,chapterDir, unitDir, pageFolder, measureCSV)
    return path_to_df


def readMeasureDF(file):
    df = pd.read_csv(file)
    return df


def incorectResponse():
    print("That's not a correct response, try again")


def findChordNumber(mdf):
    max_value = mdf["Position"].max() + 1
    #print("max value: ", max_value, " type: ", type(max_value))
    return max_value


def AskToUsePreviousData():
    while True:
        try:
            usePreviousData = str(input("Use previous data? Y/N "))
            if usePreviousData == 'y' or usePreviousData == 'n':
                break
            else:
                raise ValueError()
        except ValueError:
            incorectResponse()
    return usePreviousData


def takeUserInput(amountOfChords):
    chordDurationInteger = []
    triplet = []
    articulation = []
    slur = []
    hasBox = []
    hasAccent = []
    inputDataList = [chordDurationInteger, triplet, articulation, slur, hasBox, hasAccent]
    messageForChordDuration = f"Chord Duration List of #{amountOfChords} integers: (0.SIXTEENTH, 1.EIGHTH, 2.QUARTER, 3.HALF, 4.DOUBLE) "
    messageForTriplets = f"Triplet List of #{amountOfChords} integers: "
    messageForArticulation =f"Articulation List of #{amountOfChords} integers: "
    messageForSlur = f"Slur List of #{amountOfChords} integers: "
    messageForhasBox = f"Has box List of #{amountOfChords} integers: "
    messageForhasAccent = f"Has Accent List of #{amountOfChords} integers: "
    inputMessages = [messageForChordDuration, messageForTriplets, messageForArticulation, messageForSlur, messageForhasBox, messageForhasAccent]
    for index, inputDataElement in enumerate(inputDataList):
        while True:
            try:
                inputDataList[index] = list(map(int,input(inputMessages[index]).strip().split()))
                if len(inputDataList[index]) !=amountOfChords:
                    raise ValueError()
                break
            except ValueError:
                incorectResponse()
    # Transform the list to dictionary for better representation           
    inputData = {"chordDurationInteger": inputDataList[0],
                 "triplet": inputDataList[1],
                 "articulation": inputDataList[2],
                 "slur": inputDataList[3],
                 "hasBox": inputDataList[4],
                 "hasAccent": inputDataList[5]}
    return inputData


def askUserForInput(pageIndex, amountOfChords, userInputData):
    if pageIndex == 0:
        chordDurationInteger = list(0 for i in range(0,20))
        triplet = list([ 1, 2, 3, 0, 0 ] * 4)
        articulation = list([1, 0, 1, 0, 0] * 4)
        slur = list([0]* 20)
        hasBox = list([0] * 20)
        hasAccent = list([0] * 20)
        userInputData = {"chordDurationInteger": chordDurationInteger, "triplet":triplet , "articulation": articulation, "slur":slur , "hasBox": hasBox, "hasAccent": hasAccent}
    else:
        previousDataAnswer = AskToUsePreviousData()
        if previousDataAnswer == "n":
            userInputData = takeUserInput(amountOfChords)
    return userInputData


def durationDecoding(durationInteger):
    if durationInteger == 0:
        duration = ChordDuration.SIXTEENTH
    elif durationInteger == 1:
        duration = ChordDuration.EIGHTH
    elif durationInteger == 2:
        duration = ChordDuration.QUARTER
    elif durationInteger == 3:
        duration = ChordDuration.HALF
    elif durationInteger == 4:
        duration = ChordDuration.DOUBLE
    return duration


def noteDecoding(mdf, idx):
    note = mdf[(mdf["Label"].str.isdigit()) & (mdf["Position"]==idx)]
    note = note["Label"].to_numpy()
    note = note.astype(int)
    if note.size != 0:
        finalNote = note.item(0)
    else:
        finalNote = None
    return finalNote
    

def noteStringDecoding(mdf, idx):
    noteString = mdf[(mdf["Label"].str.isdigit()) & (mdf["Position"]==idx)]
    noteString = noteString["String"].to_numpy()
    noteString = noteString.astype(int)
    if noteString.size != 0:
        finalNoteString = noteString.item(0)
    else:
        finalNoteString = None
    return finalNoteString


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
        fingering = FingeringType.NO_FINGERING
    return fingering


def articulationDecoding(articulationInput):
    if articulationInput == 0:
        articulation = Articulation.UP
    else:
        articulation = Articulation.DOWN
    return articulation


def hasBoxDecoding(hasBoxInput):
    if hasBoxInput == 0:
        hasBox = False
    else:
        hasBox = True
    return hasBox    


def hasBoxOrAccentDecoding(hasBoxOrAccentInput):
    if hasBoxOrAccentInput == 0:
        hasBoxOrAccent = False
    else:
        hasBoxOrAccent = True
    return hasBoxOrAccent 


def stringFingeringDecoding(mdf, idx):
    stringFingering = mdf[(mdf["Position"]==idx) & (mdf["String"]!=0) & (~mdf["Label"].str.isdigit())]
    stringFingering = stringFingering["String"].to_numpy().astype(str)
    if stringFingering.size != 0:
        return stringFingering[0]


def parseMeasure(mdf, UserInputData, amountOfChords):
    measure = []
    for chordIndex in range(amountOfChords):

        # For each chordIndex/Position (in df), it must create a chord object
        chord = Chord(duration = durationDecoding(UserInputData["chordDurationInteger"][chordIndex]),
                       hasBox = hasBoxOrAccentDecoding(UserInputData["hasBox"][chordIndex]),
                       hasAccent = hasBoxOrAccentDecoding(UserInputData["hasAccent"][chordIndex]),
                       articulation = articulationDecoding(UserInputData["articulation"][chordIndex]),
                       slur = UserInputData["slur"][chordIndex],
                       triplet = UserInputData["triplet"][chordIndex],
                       note = Note(noteOnString=noteDecoding(mdf,chordIndex), string=noteStringDecoding(mdf,chordIndex)),
                       headerFingering = FingeringType(fingeringDecoding(mdf, chordIndex, headerOrNot=True)),
                       stringFingering = StringFingering(string=stringFingeringDecoding(mdf, chordIndex),
                                                        typeFingering=FingeringType(fingeringDecoding(mdf, chordIndex, headerOrNot=False))))
        
        measure.append(chord)
    return measure
        


def parseBook(directory):
    dataInput = {}
    fileNumber = 0
    # Iterate over the csv DFs
    for root, dirs, measures in os.walk(directory):
        for measure in measures:
            if measure.endswith('.csv'):
                filePath = pathToFile(directory, root, measure)                
                print(f"Parsing file: {filePath}")
                df = readMeasureDF(filePath)
                chordNumber = findChordNumber(df).astype(int)
                dataInput = askUserForInput(fileNumber, chordNumber, dataInput)
                print(dataInput)
                
                
                book = parseMeasure(df, dataInput, chordNumber)
                
                print(json.dumps(book, indent=3, default=vars))
                # OUTPUT SHOULD BE A JSON

                
                
                fileNumber+=1




    print("Parsing Done!")
            
            

if __name__ == '__main__':

    bookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    parseBook(bookDirectory)