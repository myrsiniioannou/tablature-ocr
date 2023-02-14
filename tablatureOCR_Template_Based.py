import shutup; shutup.please()
import sys
import os
sys.path.append('modules')
import os
import numpy as np
import cv2
import pandas as pd
from scipy.ndimage import rotate
from detecto import core
from pathlib import Path
import pickle
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass, field, InitVar
from typing import List
import copy


# 1. Analysis ###########################################################################################
def detectSubparts(path_to_img):
    image = cv2.imread(path_to_img)
    new_image = image.copy()
    fast_denoise = cv2.fastNlMeansDenoisingColored(new_image,None,80,200,50,21)
    gray = cv2.cvtColor(fast_denoise, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray, 225, 255, cv2.THRESH_OTSU)
    threshold = ~binary
    contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    with_contours = cv2.drawContours(new_image, contours, -1,(255,0,200),10)
    tablature_coords = []
    # Draw a bounding box around all contours
    for index, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        # Make sure contour area is large enough
        if (cv2.contourArea(c)) > 50000:
            cv2.rectangle(with_contours,(x,y), (x+w,y+h), (255,0,0), 5)
            tablature_coords.append({"x":x, "y":y, "w":w, "h":h})
    return tablature_coords


def sortSubpartCoordinates(tablature_coords):
    sorted_tablature_coords = sorted(tablature_coords, key=lambda x: (x["y"]))
    for idx, i in enumerate(range(0, len(sorted_tablature_coords)-1)):
        denominator = 6
        if abs(sorted_tablature_coords[i]['y']-sorted_tablature_coords[i+1]['y'])<= (sorted_tablature_coords[i]['h']/denominator):
            if sorted_tablature_coords[i]['x']>sorted_tablature_coords[i+1]['x']:
                sorted_tablature_coords[i], sorted_tablature_coords[i+1]  = sorted_tablature_coords[i+1], sorted_tablature_coords[i]
    return sorted_tablature_coords


def correctSkew(image, delta=0.2, limit=10):
    def determine_score(arr, angle):
        data = rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return histogram, score
    thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 
    scores = []
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)
    best_angle = angles[scores.index(max(scores))]
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, \
          borderMode=cv2.BORDER_REPLICATE)
    return best_angle, rotated


def predictNotation(path_to_img, sorted_tablature_coords, model):
    image = cv2.imread(path_to_img)
    contrast = 5
    brightness = -600
    thresh = 0.30
    image = cv2.addWeighted(image, contrast, image, 0, brightness)
    totalLabels = []
    totalBoxes = []
    totalScores = []
    for index, i in enumerate(sorted_tablature_coords):
        cropped_img = image[i["y"] : i["y"] + i["h"], i["x"] : i["x"] + i["w"]]
        gray_cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        angle, rotatedIMG = correctSkew(gray_cropped_img)
        RGB_img = cv2.cvtColor(rotatedIMG, cv2.COLOR_BGR2RGB)    
        predictions = model.predict(RGB_img)
        labels, boxes, scores = predictions
        filtered_indices = np.where(scores > thresh)
        filtered_scores = scores[filtered_indices]
        filtered_boxes = boxes[filtered_indices]
        num_list = filtered_indices[0].tolist()
        filtered_labels = [labels[i] for i in num_list]
        totalLabels.append(filtered_labels)
        totalScores.append(filtered_scores)
        totalBoxes.append(filtered_boxes)
    return totalBoxes, totalLabels, totalScores


def dataframeCreationForEachMeasure(totalBoxes, totalLabels, totalScores):
    allMeasureDFs = []
    for i in range(len(totalBoxes)):
        mdf = pd.DataFrame(totalBoxes[i].numpy(), columns = ["x1", "y1", "x2", "y2"])
        mdf['Label'] = pd.Series(totalLabels[i])
        mdf['Score'] = pd.Series(totalScores[i])
        col = mdf.pop("Label")
        mdf.insert(0, col.name, col)
        mdf['Centroid x'] = abs(mdf['x2'] - mdf['x1'])/2 + mdf['x1']
        mdf['Centroid y'] = abs(mdf['y2'] - mdf['y1'])/2 + mdf['y1']
        df = mdf[mdf[['Label']].apply(lambda x: x[0].isdigit(), axis=1)].sort_values(by=['Centroid x']).reset_index(drop=True)
        allMeasureDFs.append(df)
    return allMeasureDFs


def DFresultOptimization(allDFs, numberOfMeasuresPerPage):
    optimizedDFs = []
    for df in allDFs:
        #Eliminate very close elements
        meanWidth = abs(df['x2'].sub(df['x1'], axis = 0)).mean()
        index = 0
        indexesToDrop = []
        dfLength = len(list(df.index))
        while index <= (dfLength - 2):
            difference = abs(df["Centroid x"][index] - df["Centroid x"][index+1])
            if difference < meanWidth/3:
                indexesToDrop.append(index+1 if df["Score"][index] > df["Score"][index+1] else index)
            index += 1
        if indexesToDrop:
            df = df.drop(indexesToDrop, axis=0).reset_index(drop=True)
        # If there are extra elements as rows, delete the ones with the lowest score
        extraElements = len(df) - numberOfMeasuresPerPage
        if extraElements>0:
            df = df.sort_values(by=['Score'], ascending=False).reset_index(drop=True)
            df.drop(df.tail(extraElements).index, inplace=True)
            df = df.sort_values(by=['Centroid x']).reset_index(drop=True)
        optimizedDFs.append(df)
    return optimizedDFs


def measureDFtoList(allDFs):
    pageListOfMeasureListsOfIntegers = []
    for df in allDFs:
        pageListOfMeasureListsOfIntegers.append(df['Label'].tolist())
    return pageListOfMeasureListsOfIntegers


def exportFileForPageMeasures(listOfMeasures, imagePath):
    pickleNamePath = imagePath[:-4]+".pkl"
    with open(pickleNamePath, 'wb') as f:
        pickle.dump(listOfMeasures, f)


def checkIfFileIsAnalyzedAlready(imagePath):
    return os.path.isfile(imagePath[:-4]+".pkl")
    

def findNumberOfJPGsInPercentages(folder):
    JPGnumberOfFiles = 0
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".jpg"):
                JPGnumberOfFiles += 1
    percentageFileIntegers = [round(i*JPGnumberOfFiles/10) for i in range(1,11)]
    return percentageFileIntegers


def checkAndNotifyOnPercentageOfAnalyzedFiles(root, percentagesOfFilesDone):
    directory = Path(root).parents[1]
    PKLnumberOfFiles = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".pkl"):
                PKLnumberOfFiles += 1
    if PKLnumberOfFiles in percentagesOfFilesDone:
        idx = percentagesOfFilesDone.index(PKLnumberOfFiles)
        print(f"{(idx+1)*10}% of Pages Analyzed.")



def iterateOverBookPages(root, files, elementNumberPerMeasure, percentagesOfFilesDone, model):
    for filename in files:
        imagePath = os.path.join(Path(root), filename)
        if not checkIfFileIsAnalyzedAlready(imagePath):
            checkAndNotifyOnPercentageOfAnalyzedFiles(root, percentagesOfFilesDone)
            pageSubpartCoordinates = detectSubparts(imagePath)
            sortedPageSubpartCoordinates = sortSubpartCoordinates(pageSubpartCoordinates)
            boxes, labels, scores = predictNotation(imagePath, sortedPageSubpartCoordinates, model)
            pageMeasureDFs = dataframeCreationForEachMeasure(boxes, labels, scores)
            finalPageMeasureDFs = DFresultOptimization(pageMeasureDFs, elementNumberPerMeasure)
            finalPageMeasureElementsAsList = measureDFtoList(finalPageMeasureDFs)
            print(finalPageMeasureElementsAsList)
            exportFileForPageMeasures(finalPageMeasureElementsAsList, imagePath)
        

def analysis(elementNumberPerMeasure, bookDirectory):
    model_path = r"C:\Users\merse\Desktop\Tablature OCR\model\model5Merged.pth"
    model = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    print("Starting Template-Based Tablature OCR...")
    percentagesOfFilesDone = findNumberOfJPGsInPercentages(bookDirectory)
    for root, dirs, files in os.walk(bookDirectory):
        iterateOverBookPages(root, files, elementNumberPerMeasure, percentagesOfFilesDone, model)
    print("Analysis Done!")



# 2. Rendering ###########################################################################################
@dataclass
class Chapter:
    number : int
    cover : bool = False
    def increment(self):
        self.number += 1
        return self.number

@dataclass
class Unit:
    number : int    
    def increment(self):
        self.number += 1
        return self.number
    def reset(self):
        self.number = 0
        return self.number


def templateLoading(bookName):
    templatesPath = r"..\book_musescore_templates"
    environmentPath = os.path.join(templatesPath, os.path.basename(bookName))
    file_loader = FileSystemLoader(environmentPath)
    env = Environment(loader = file_loader)
    return env


def renderBookBase(env, bookContent):
    book = env.get_template("bookBase.mscx").render(
    content = bookContent)
    return book


def findPagesInUnitDirectories(root):
    for files in os.walk(root):
        return list(sorted(set([os.path.splitext(x)[0] for x in files[2]])))


def renderChapterCover(env, currentChapterNumber):
    chapterCover = env.get_template("chapter.mscx").render(
        number = currentChapterNumber)
    return chapterCover


def renderUnitCover(env, currentUnitNumber):
    unitCover = env.get_template("unit.mscx").render(
        number = currentUnitNumber)
    return unitCover


def renderPageHeader(env, pageNumber, paragraphPages, headingPages):
    paragraph = paragraphPages[pageNumber] if pageNumber in paragraphPages else None
    heading1 = headingPages[pageNumber]["heading1"] if pageNumber in headingPages else None
    subHeading1 = headingPages[pageNumber]["subHeading1"] if pageNumber in headingPages else None
    heading2 = headingPages[pageNumber]["heading2"] if pageNumber in headingPages else None
    subHeading2 = headingPages[pageNumber]["subHeading2"] if pageNumber in headingPages else None
    pageHeader = env.get_template("pageHeader.mscx").render(
        paragraph = paragraph,
        heading1 = heading1,
        subHeading1 = subHeading1,
        heading2 = heading2,
        subHeading2 = subHeading2
    )
    return pageHeader


def findCaptionForHorizontalBox(pageNumber, measure, captions, numberOfMeasuresPerRow):
    measureCaption = None
    for caption in captions:
        if (captions[caption] and ((type(captions[caption]["pages"]) == list and pageNumber in captions[caption]["pages"]) or captions[caption]["pages"] == "all") and captions[caption]["number"]):
            if (caption == "left" and (measure%numberOfMeasuresPerRow == 1) 
                or (caption == "leftRight" and captions[caption]["sameNumberInRow"]
                and measure%numberOfMeasuresPerRow == 1)):
                measureCaption = captions[caption]["symbol"] + str((measure+1)//2)
            if (caption == "leftRight" and captions[caption]["sameNumberInRow"] and measure%numberOfMeasuresPerRow == 0):
                measureCaption = captions[caption]["symbol"] + str((measure)//2)
            if caption == "leftRight" and not captions[caption]["sameNumberInRow"]:
                measureCaption = captions[caption]["symbol"] + str(measure)
        if (captions[caption] and ((type(captions[caption]["pages"]) == list and pageNumber in captions[caption]["pages"]) or captions[caption]["pages"] == "all") and not captions[caption]["number"]):
            measureCaption = captions[caption]["symbol"]
    return measureCaption


def renderHorizontalBox(env, caption):
    horizontalBox = env.get_template("horizontalBox.mscx").render(
        caption = caption)
    return horizontalBox


def renderPage(env, pageNumber, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions):
    renderedPage = ""
    pageHeader = renderPageHeader(env, int(pageNumber), paragraphPages, headingPages)
    renderedPage += pageHeader
    for measure in range(1, numberOfMeasuresPerPage+1):
        caption = findCaptionForHorizontalBox(pageNumber, measure, captions, numberOfMeasuresPerRow)
        horizontalBox = renderHorizontalBox(env, caption)

        print("measure:", measure)
        # measure
            #header
            #pickle
                #if THERE IS file + ".pkl":
                #    pageAllMeasureNotes = pd.read_pickle(os.path.join(root, file))
                #    print(pageAllMeasureNotes)
                #    print("----------------")



        # section break or page break (sto last measure ths selidas)
        # RENDERARE TA MESA STO MESAURE BASE
        #renderedPage += horizontalBox + measure

    return ""



def exportMCSXFile(render):
    pass


def renderUnits(env, pageDirectory, pages, currentChapter, currentUnit, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions):
    # Render the Chapter Cover
    if currentChapter.cover:
        chapterCoverContent = renderChapterCover(env, currentChapter.number)
        currentChapter.cover = False
    else:
        chapterCoverContent = ""
    # Render the Unit Cover
    currentUnit.increment()
    unitCoverContent = renderUnitCover(env, currentUnit.number)
    
    # Render All Pages in Unit
    pagesContent = ""
    for page in pages:
        print("page:", int(page))
        pagesContent += renderPage(env, int(page), paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions)
        print("-------------------------------------------------------")

    # Join the all the content
    #unitContentReadyToRenderInsideBookBase = " ".join([chapterCoverContent, unitCoverContent, pagesContent])
    #unitOutputRender = renderBookBase(env, unitContentReadyToRenderInsideBookBase)

    # Export the musescore file
    #exportMCSXFile(unitOutputRender)






def renderBook(env, bookDirectory, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions):
    currentChapter = Chapter(0)
    currentUnit = Unit(0)
    for root, dirs, files in os.walk(bookDirectory):
        if os.path.basename(root).startswith("chapter"):
            currentChapter.increment()
            currentUnit.reset()
            currentChapter.cover = True
        if os.path.basename(root).startswith("unit"):
            pagesInUnitDirectories = findPagesInUnitDirectories(root)
            renderUnits(env, root, pagesInUnitDirectories, currentChapter, currentUnit, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions)
        print("*********************************************************************************")




def findParagraphPages(bookDirectory, userInput, numberOfPagesInBook):
    pageCounter = 0
    paragraphPages = {}
    while pageCounter <= numberOfPagesInBook:
        for paragraph in userInput["paragraphs"]:
            numberOfParagraphPages = len(userInput["paragraphs"][paragraph]["letters"])* userInput["paragraphs"][paragraph]["pageFrequency"]
            letterIncrement = 0
            for page in range(1, numberOfParagraphPages+1):
                if page % userInput["paragraphs"][paragraph]["pageFrequency"] == 1 or userInput["paragraphs"][paragraph]["pageFrequency"] == 1:
                    paragraphPages[page+pageCounter] = userInput["paragraphs"][paragraph]["letters"][letterIncrement] + paragraph
                    letterIncrement += 1
                if page+pageCounter>=numberOfPagesInBook:
                    break
            pageCounter += numberOfParagraphPages
            if pageCounter>=numberOfPagesInBook:
                break
    keysToRemove = []
    for key in paragraphPages.keys():
        if key > numberOfPagesInBook:
            keysToRemove.append(key)
    if keysToRemove:
        for key in keysToRemove:
            del paragraphPages[key]
    return paragraphPages


def addThePageToHeadingDirectory(heading, headingPageCurrentNumber, singleHeading, subheading):
    heading1 = copy.copy(heading)
    heading2 = copy.copy(heading) if not singleHeading else None
    subHeading1 = copy.copy(subheading)
    subHeading2 = None
    if subheading:
        if headingPageCurrentNumber and singleHeading:
            subHeading1 = str(headingPageCurrentNumber)+ str(subheading)
        elif headingPageCurrentNumber and not singleHeading:
            subHeading1 = str(headingPageCurrentNumber*2-1)+ str(subheading)
            subHeading2 = str(headingPageCurrentNumber*2)+ str(subheading)
    else:
        if headingPageCurrentNumber:
            if len(heading1)>3:
                heading1 +=" " + str(headingPageCurrentNumber)
            else:
                heading1 +="" + str(headingPageCurrentNumber)
    heading = {
        "heading1": heading1,
        "subHeading1" : subHeading1,
        "heading2": heading2,
        "subHeading2" : subHeading2,
    }
    return heading


def findHeadingPages(userInput):
    headingPages = {}
    for heading in userInput["headings"].keys():
        headingPageRepetition = userInput["headings"][heading]["headingPageRepetition"]
        singleHeading = userInput["headings"][heading]["singleHeading"]
        subheading = userInput["headings"][heading]["subheading"]
        headingPageRepetitionCounter = 1
        if headingPageRepetition:
            headingPageCurrentNumber = 1
        for page in userInput["headings"][heading]["pages"]:
            if headingPageRepetition and headingPageRepetitionCounter < headingPageRepetition:
                headingPages[page] = addThePageToHeadingDirectory(heading, headingPageCurrentNumber, singleHeading, subheading)
                headingPageRepetitionCounter += 1
            elif headingPageRepetitionCounter == headingPageRepetition:
                headingPages[page] = addThePageToHeadingDirectory(heading, headingPageCurrentNumber, singleHeading, subheading)
                headingPageRepetitionCounter = 1
                headingPageCurrentNumber += 1
            else:
                headingPages[page] = addThePageToHeadingDirectory(heading, None, singleHeading, subheading)
    return headingPages


def rendering(bookDirectory, userInput):
    environment = templateLoading(bookDirectory)
    numberOfPagesInBook = sum([len(files) for r, d, files in os.walk(bookDirectory)])
    paragraphPages = findParagraphPages(bookDirectory, userInput, numberOfPagesInBook)
    headingPages = findHeadingPages(userInput)
    renderBook(environment, bookDirectory, paragraphPages, headingPages, userInput["numberOfMeasuresPerPage"], userInput["numberOfMeasuresPerRow"], userInput["captions"])





def runApp():
    pass



if __name__ == '__main__':

    bookFolder = r'C:\Users\merse\Desktop\Tablature OCR\books_to_analyze\firstBookTEST'

    input = {
        "numberOfMeasuresPerPage" : 12,
        "numberOfMeasuresPerRow" : 2,
        "headers" : {
            1:  ["i", "m", "i"],
            2:  ["m", "i", "m"],
            3:  ["m", "a", "m"],
            4:  ["a", "m", "a"],
            5:  ["i", "a", "i"],
            6:  ["a", "i", "a"],
            7:  ["i", "m", "a"],
            8:  ["i", "a", "m"],
            9:  ["m", "i", "a"],
            10: ["m", "a", "i"],
            11: ["a", "m", "i"],
            12: ["a", "i", "m"],
        },
        "headerPaterns": {
            "pattern1" : {
                "sequence" : [[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4],[5,5,5,5],[6,6,6,6]],
                "sequenceRepetition" : 5,
                "headerRepetition" : "vertical" # or horizontal or none
            },
            "pattern2" : {
                "sequence" : [[7,7,7,7], [8,8,8,8],[9,9,9,9],[10,10,10,10],[11,11,11,11],[12,12,12,12]],
                "sequenceRepetition" : 5,
                "headerRepetition" : "vertical" # or horizontal or none
            }
        },







        # Paragraphs are always in sequence.
        "paragraphs": {
            "A" : {
                "letters" : ["I", "II", "III", "IV", "V"],
                "pageFrequency" : 3
            },
            "B" : {
                "letters" : ["I", "II", "III", "IV", "V"],
                "pageFrequency" : 3
            }
        },
        # HEADINGS - TITLES (VARIATION - F)
        "headings" : {
            "VARIATION" : {
                "pages" : range(1,16), #[*range(0,350)]
                "singleHeading" : True, #1 ή 2 ΣΤΗΛΕΣ
                "headingPageRepetition" : 3, # or None # 1 otan theloume na emfanizontai ta noumera mia fora
                "subheading" : None
            },
            "F" : {
                "pages" : [16,17,18,19],
                "singleHeading" : False, #1 ή 2 ΣΤΗΛΕΣ
                "headingPageRepetition" : 1, 
                "subheading" : "A"
            },
            "A" : {
                "pages" : [20,21,22,23,24],
                "singleHeading" : True, #1 ή 2 ΣΤΗΛΕΣ
                "headingPageRepetition" : None, 
                "subheading" : "B"
            },
            "B" : {
                "pages" : [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
                "singleHeading" : False, #1 ή 2 ΣΤΗΛΕΣ
                "headingPageRepetition" : 1, 
                "subheading" : "C"
            }
        },
        # CAPTIONS - F on the sides
        "captions" : {
            # IF THERE ARE NO CAPTIONS, DELETE EVERYTHING ABOVE 
            # AND LEAVE THE CAPTIONS DICT EMPTY
            "left": {
                "pages" : [1,2,3,4,5], #or "all"
                "symbol" : "F",
                "number" : True,
                "sameNumberInRow" : False # peritto alla what ever
            },
            "leftRight" : {
                "pages" : [*range(6,17)],
                "symbol" : "Z",
                "number" : False,
                "sameNumberInRow" : False # peritto alla what ever
            }
        }   
    }

    
    #analysis(input["numberOfMeasuresPerPage"], bookFolder)
    rendering(bookFolder, input)



    #detectInBetweenChapterInstructions()


    # diorthosh kai meta

    # auto extract pdf apo to musescore




