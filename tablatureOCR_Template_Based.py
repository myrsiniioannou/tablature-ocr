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
from PyPDF2 import PdfFileMerger
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
import time


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
    for caption in captions:
        measureCaption = None
        alignment = None
        if pageNumber in captions[caption]["pages"]:
            if captions[caption]["number"]:
                if caption == "onlyLeft" and measure % numberOfMeasuresPerRow == 0:
                    measureCaption = captions[caption]["symbol"] + str((measure//numberOfMeasuresPerRow)+1)
                    alignment = "left"
                    break
                if caption == "everywhere":
                    if captions[caption]["sameNumberInRow"]:
                        measureCaption = captions[caption]["symbol"] + str((measure//numberOfMeasuresPerRow)+1)
                    else:
                        measureCaption = captions[caption]["symbol"] + str(measure+1)
                    alignment = "left" if measure % numberOfMeasuresPerRow == 0 else "center"
                    break
            else:
                if measure % numberOfMeasuresPerRow == 0:
                    measureCaption = captions[caption]["symbol"]
                    break
    return measureCaption, alignment


def renderHorizontalBox(env, caption, alignment):
    horizontalBox = env.get_template("horizontalBox.mscx").render(
        caption = caption,
        alignment = alignment)
    return horizontalBox


def readPagePiklFiles(pageDirectory, pageNumber):
    pagePiklFiles = None
    for root, dirs, files in os.walk(pageDirectory):
        for file in files:
            if file.endswith(".pkl") and int(pageNumber) == int(file[:-4]):
                #print(root,file)
                pagePiklFiles = pd.read_pickle(os.path.join(root, file))
                break                
    return pagePiklFiles


def findTemplateMSCXname(templateNumber):
    if len(str(templateNumber)) == 1:
        templateMSCXname = "00" + str(templateNumber) + ".mscx"
    elif len(str(templateNumber)) == 2:
        templateMSCXname = "0" + str(templateNumber) + ".mscx"
    else:
        templateMSCXname = str(templateNumber) + ".mscx"
    return templateMSCXname


def findLayoutBreak(measure, numberOfMeasuresPerPage, numberOfMeasuresPerRow):
    moduloMeasureRow =   (measure + 1) % numberOfMeasuresPerRow
    layoutBreak = "Section" if moduloMeasureRow == 0 else None
    if (measure + 1) == numberOfMeasuresPerPage:
        layoutBreak = "Page"
    return layoutBreak


def findNumberOfMeasureNotesOnCurrentPage(pageNumber, numberOfNotesOnEachMeasure):
    for number in numberOfNotesOnEachMeasure.keys():
        if pageNumber in numberOfNotesOnEachMeasure[number]["pages"]:
            measureNotesOnCurrentPage = copy.copy(number)
            break
    return measureNotesOnCurrentPage


def checkAndFixTheLengthOfPklFiles(pageNumber, pklFiles, numberOfMeasuresPerPage, numberOfNotesOnEachMeasure):
    numberOfMeasureNotesOnCurrentPage = findNumberOfMeasureNotesOnCurrentPage(pageNumber, numberOfNotesOnEachMeasure)
    if len(pklFiles) != 0:
        while len(pklFiles) < numberOfMeasuresPerPage:
            pklFiles.append(pklFiles[-1])
        for pklMeasure in pklFiles:
            while len(pklMeasure) < numberOfMeasureNotesOnCurrentPage:
                pklMeasure.append(pklMeasure[-1])
    return pklFiles


def renderPage(env, 
                pageDirectory, 
                pageNumber,
                paragraphPages, 
                headingPages, 
                numberOfMeasuresPerPage, 
                numberOfMeasuresPerRow, 
                captions,
                currentPageMeasureTemplates, 
                headers,
                numberOfNotesOnEachMeasure):
    renderedPage = ""
    pageHeader = renderPageHeader(env, int(pageNumber), paragraphPages, headingPages)
    renderedPage += pageHeader
    pklFiles = readPagePiklFiles(pageDirectory, pageNumber)
    pklFilesLengthChecked = checkAndFixTheLengthOfPklFiles(pageNumber, pklFiles, numberOfMeasuresPerPage, numberOfNotesOnEachMeasure)
    for measure in range(0, numberOfMeasuresPerPage):
        caption, alignment = findCaptionForHorizontalBox(pageNumber, measure, captions, numberOfMeasuresPerRow)
        horizontalBox = renderHorizontalBox(env, caption, alignment)
        pageHeaders = headers[pageNumber][measure]
        templateNumber = currentPageMeasureTemplates[measure]
        templateMSCXname = findTemplateMSCXname(templateNumber)
        layoutBreak = findLayoutBreak(measure, numberOfMeasuresPerPage, numberOfMeasuresPerRow)
        finalPklFiles = [int(x) for x in pklFilesLengthChecked[measure]]
        measureWithouBase = env.get_template(templateMSCXname).render(
            headers = pageHeaders,
            notes =  finalPklFiles)
        finalMeasure = env.get_template("measureBase.mscx").render(
            layoutBreak = layoutBreak,
            measureContent = measureWithouBase)
        renderedPage += (horizontalBox + finalMeasure)
    return renderedPage


def exportMCSXFile(pageDirectory, fileToExport, bookDirectory):
    dirPath = os.path.join(r'C:\Users\merse\Desktop\Tablature OCR\musescore_outputs', os.path.basename(bookDirectory))
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
    chapter = os.path.basename(Path(pageDirectory).parents[0])
    unit = os.path.basename(pageDirectory)
    name = chapter + unit + ".mscx"
    museScoreOutputFile = os.path.join(dirPath, name)
    with open(f"{museScoreOutputFile}", "w") as f:
        f.write(fileToExport)


def numberToLatinNumeral(number):
    if int(number) == 1:
        latinNumeral = "I"
    elif int(number) == 2:
        latinNumeral = "II"
    elif int(number) == 3:
        latinNumeral = "III"
    elif int(number) == 4:
        latinNumeral = "IV"
    elif int(number) == 5:
        latinNumeral = "V"
    elif int(number) == 6:
        latinNumeral = "VI"
    elif int(number) == 7:
        latinNumeral = "VII"
    elif int(number) == 8:
        latinNumeral = "VIII"
    elif int(number) == 9:
        latinNumeral = "IX"
    elif int(number) == 10:
        latinNumeral = "X"
    else:
        latinNumeral = None
    return latinNumeral



def renderUnits(env, bookDirectory, pageDirectory, pages, currentChapter, currentUnit, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions, numberOfNotesOnEachMeasure, pageMeasureTemplates, headers):
    chapterCover = ""
    if currentChapter.cover:
        chapterLatinNumeral = numberToLatinNumeral(currentChapter.number)
        chapterCover = renderChapterCover(env, chapterLatinNumeral)
        currentChapter.cover = False
    currentUnit.increment()
    unitLatinNumeral = numberToLatinNumeral(currentUnit.number)
    unitCover = renderUnitCover(env, unitLatinNumeral)
    # Render All Pages in each unit
    unitContent = ""
    for page in pages:
        renderedPage = renderPage(env, 
                                pageDirectory, 
                                int(page), 
                                paragraphPages, 
                                headingPages, 
                                numberOfMeasuresPerPage, 
                                numberOfMeasuresPerRow, 
                                captions,
                                pageMeasureTemplates[int(page)],
                                headers,
                                numberOfNotesOnEachMeasure)
        unitContent += renderedPage

    # Join all, covers and content
    unitWithoutBase = " ".join([chapterCover, unitCover, unitContent])
    finalUnitOutput = renderBookBase(env, unitWithoutBase)
    exportMCSXFile(pageDirectory, finalUnitOutput, bookDirectory)


def renderBook(env, bookDirectory, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions, numberOfNotesOnEachMeasure, pageMeasureTemplates, headers):
    currentChapter = Chapter(0)
    currentUnit = Unit(0)
    for root, dirs, files in os.walk(bookDirectory):
        if os.path.basename(root).startswith("chapter"):
            currentChapter.increment()
            currentUnit.reset()
            currentChapter.cover = True
        if os.path.basename(root).startswith("unit"):
            pagesInUnitDirectories = findPagesInUnitDirectories(root)
            renderUnits(env, bookDirectory, root, pagesInUnitDirectories, currentChapter, currentUnit, paragraphPages, headingPages, numberOfMeasuresPerPage, numberOfMeasuresPerRow, captions, numberOfNotesOnEachMeasure, pageMeasureTemplates, headers)



# 3. Find Values for each Page ###########################################################################################
def findParagraphPages(userInput, numberOfPagesInBook):
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
            subNum1 = headingPageCurrentNumber*2-1
            subNum2 = headingPageCurrentNumber*2
            subHeading1 = subNum1+ str(subheading)
            subHeading2 = subNum2+ str(subheading)
    else:
        if headingPageCurrentNumber:
            if len(heading1)>3:
                heading1 +=" " + headingPageCurrentNumber
            else:
                heading1 +="" + headingPageCurrentNumber
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
            print("page: ", page)
            if headingPageRepetition and headingPageRepetitionCounter < headingPageRepetition:
                headingPages[page] = addThePageToHeadingDirectory(heading, headingPageCurrentNumber, singleHeading, subheading)
                headingPageRepetitionCounter += 1
            elif headingPageRepetitionCounter == headingPageRepetition:
                headingPages[page] = addThePageToHeadingDirectory(heading, headingPageCurrentNumber, singleHeading, subheading)
                headingPageRepetitionCounter = 1
                headingPageCurrentNumber += 1
            else:
                headingPages[page] = addThePageToHeadingDirectory(heading, None, singleHeading, subheading)
            if headingPageCurrentNumber > userInput["headings"][heading]["sectionNumberLimit"]:
                headingPageCurrentNumber = 1
            print(headingPages[page])
            print("------------------------------------------------")
    return headingPages


def appendTemplateOnList(times, templateList, template):
    for t in range(0, times):
        templateList.append(template)
    return templateList


def findPageMeasureTemplates(templatePatterns, numberOfMeasuresPerPage, numberOfMeasuresPerRow):
    pageMeasureTemplates = {}
    for pattern in templatePatterns.keys():
        pages = templatePatterns[pattern]["pages"]
        templates = templatePatterns[pattern]["templates"]
        templateList = []
        measuresInUnit = len(pages) * numberOfMeasuresPerPage
        rows = numberOfMeasuresPerPage//numberOfMeasuresPerRow
        while len(templateList) <= measuresInUnit:
            if templatePatterns[pattern]["measurePageRepetition"] == "horizontal":
                    for template in templates:
                        templateList = appendTemplateOnList(numberOfMeasuresPerRow, templateList, template)
            elif templatePatterns[pattern]["measurePageRepetition"] == "vertical":
                    templateStart = 0
                    templateEnd = copy.copy(numberOfMeasuresPerRow)
                    for page in pages:
                        templateList.extend(rows * templates[templateStart:templateEnd])
                        templateStart += numberOfMeasuresPerRow
                        templateEnd += numberOfMeasuresPerRow
            elif templatePatterns[pattern]["measurePageRepetition"] == "page":
                    currentTemplate = 0
                    for page in pages:
                        templateList = appendTemplateOnList(numberOfMeasuresPerPage, templateList, templates[currentTemplate])
                        currentTemplate += 1
            elif templatePatterns[pattern]["measurePageRepetition"] == None:
                    for template in templates:
                        templateList.append(template)
        templateList = templateList[:measuresInUnit]        
        currentPageMeasuresStart = 0
        currentPageMeasuresEnd = copy.copy(numberOfMeasuresPerPage)
        for page in pages:
            pageMeasureTemplates[page] = templateList[currentPageMeasuresStart:currentPageMeasuresEnd]
            currentPageMeasuresStart += numberOfMeasuresPerPage
            currentPageMeasuresEnd += numberOfMeasuresPerPage
    return pageMeasureTemplates


def extendHeaderList(times, headerList, template):
    for t in range(0, times):
        headerList.extend(template)
    return headerList


def findHeaders(userInput ):
    bookHeaders = {}
    for pattern in userInput["headerPaterns"].keys():
        pages = userInput["headerPaterns"][pattern]["pages"]
        headers = userInput["headers"]
        headerRepetition = userInput["headerPaterns"][pattern]["headerPageRepetition"]
        pageMeasureHeaderSequence = userInput["headerPaterns"][pattern]["pageMeasureHeaderSequence"]
        numberOfMeasuresPerPage = userInput["numberOfMeasuresPerPage"]
        numberOfMeasuresPerRow = userInput["numberOfMeasuresPerRow"]
        rows = numberOfMeasuresPerPage//numberOfMeasuresPerRow
        headerStart = 0
        headerEnd = copy.copy(numberOfMeasuresPerRow)
        for page in pages:
            headerList = []
            if headerRepetition == "horizontal":
                while len(headerList) <= numberOfMeasuresPerPage:
                    for headerSeq in pageMeasureHeaderSequence:
                        headerList = appendTemplateOnList(numberOfMeasuresPerRow, headerList, headerSeq)
            elif headerRepetition == "vertical":
                headerList.extend(rows * pageMeasureHeaderSequence[headerStart:headerEnd])
                headerStart += numberOfMeasuresPerRow
                headerEnd += numberOfMeasuresPerRow
                if headerEnd>len(pageMeasureHeaderSequence):
                    headerStart = 0
                    headerEnd = copy.copy(numberOfMeasuresPerRow)
            elif headerRepetition == None:
                while len(headerList) <= numberOfMeasuresPerPage:
                    for headerSeq in pageMeasureHeaderSequence:
                        headerList.append(headerSeq)
            headerList = headerList[:numberOfMeasuresPerPage] 
            fingeringHeaderList = []
            for headerMeasure in headerList:
                measureHeaderList = []
                for headerNumber in headerMeasure:
                    measureHeaderList.extend(headers[headerNumber])
                fingeringHeaderList.append(measureHeaderList)
            bookHeaders[page] = fingeringHeaderList
    return bookHeaders


def rendering(bookDirectory, userInput):
    # environment = templateLoading(bookDirectory)
    #numberOfPagesInBook = sum([len(files) for r, d, files in os.walk(bookDirectory)])
    #paragraphPages = findParagraphPages(userInput, numberOfPagesInBook)
    headingPages = findHeadingPages(userInput)



    # pageMeasureTemplates = findPageMeasureTemplates(userInput["templatePatterns"], userInput["numberOfMeasuresPerPage"], userInput["numberOfMeasuresPerRow"])
    # headers = findHeaders(userInput)
    # renderBook(environment, bookDirectory, paragraphPages, headingPages, userInput["numberOfMeasuresPerPage"], userInput["numberOfMeasuresPerRow"], userInput["captions"], userInput["numberOfNotesOnEachMeasure"], pageMeasureTemplates, headers)
    # print("Rendering Done!")


def detectTextAndExportEachPage(img, path):
    img = cv2.imread(os.path.join(path, img))
    text = pytesseract.image_to_string(img)
    return text


def detectIntroductoryText(bookFolder):
    bookName = os.path.basename(bookFolder)
    textBasePath = r"C:\Users\merse\Desktop\Tablature OCR\introductoryText"
    introductoryTextPath = os.path.join(textBasePath, bookName)
    text = ""
    if os.path.exists(introductoryTextPath):
        for root, dirs, imgs in os.walk(introductoryTextPath):
            for img in imgs:
                text += detectTextAndExportEachPage(img, introductoryTextPath)
    textPath = os.path.join(introductoryTextPath, "introductoryText.txt")
    with open(f"{textPath}", "w") as f:
        f.write(text)
    print("Introductory Text Saved!")


def pauseForCorrectionAndFilePreparation():
    input(" **********************************************************************\n \
1. Correct musescore files.\n \
2. Create Introdutory Text's Musescore file named '00' and put it musescore_outputs/book. \n \
3. Prepare everything. \n \
4. Press Enter to export the final book.\n \
**********************************************************************")


def extractPDFs(bookFolder):
    pathForMusescoreFiles = os.path.join(r"C:\Users\merse\Desktop\Tablature OCR\musescore_outputs", os.path.basename(bookFolder))
    pdfPath = r"C:\Users\merse\Desktop\Tablature OCR\pdfs"
    pdfCurrentBookPath = os.path.join(pdfPath, os.path.basename(bookFolder))
    if not os.path.exists(pdfCurrentBookPath):
        os.mkdir(pdfCurrentBookPath)
    for root, dirs, files in os.walk(pathForMusescoreFiles):
        for idx, file in enumerate(files):
            PDFfileName = "0"+ str(idx) + ".pdf" if len(str(idx)) == 1 else str(idx) + ".pdf"
            mscxFile = os.path.join(pathForMusescoreFiles, file)
            PDFfile = os.path.join(pdfCurrentBookPath, PDFfileName)
            command = "MuseScore3.exe -o" + ' "' + PDFfile +  '" "' + mscxFile + '"'
            os.system(command)
    print("PDF exctraction Done!")


def mergePDFs(bookFolder):
    finalBookPath = r"C:\Users\merse\Desktop\Tablature OCR\final_Books"
    bookName = os.path.basename(bookFolder)
    pdfFolderPath = os.path.join(r"C:\Users\merse\Desktop\Tablature OCR\pdfs", bookName)
    pdfList = os.listdir(pdfFolderPath)
    pdfList.sort()
    merger = PdfFileMerger()
    for pdfFile in pdfList:
        pdfFileWithPath = os.path.join(pdfFolderPath, pdfFile)
        merger.append(pdfFileWithPath)
    finalBookNamePath = os.path.join(finalBookPath, bookName + ".pdf")
    merger.write(finalBookNamePath)
    merger.close()
    print("Merging PDF files Done!")


def runApp(bookFolder, userInput):
    start = time.time()
    # analysis(userInput["numberOfMeasuresPerPage"], bookFolder)
    # rendering(bookFolder, userInput)
    # renderingTime = time.time()
    # analysisAndRenderingTime = (renderingTime - start)/60
    # print("Finished Analysis and Rendering in: ", analysisAndRenderingTime, "m")
    # detectIntroductoryText(bookFolder)
    # pauseForCorrectionAndFilePreparation()
    
    extractPDFs(bookFolder)
    mergePDFs(bookFolder)
    # print(f"{os.path.basename(bookFolder)} Done!")
    end = time.time()
    totalTime = (end - start)/60
    print("Finished the whole process in: ", totalTime, "m")




if __name__ == '__main__':

    bookFolder = r'C:\Users\merse\Desktop\Tablature OCR\books_to_analyze\firstBook'

    ##############################################
    #                 PATTERNS
    ##############################################
    #   HORIZONTAL       VERTICAL         PAGE
    #   [ 1   1 ]       [ 1   2 ]       [ 1   1 ]
    #   [ 2   2 ]       [ 1   2 ]       [ 1   1 ]
    #   [ 3   3 ]       [ 1   2 ]       [ 1   1 ]
    #   [ 4   4 ]       [ 1   2 ]       [ 1   1 ]
    #   [ 5   5 ]       [ 1   2 ]       [ 1   1 ]
    #   [ 6   6 ]       [ 1   2 ]       [ 1   1 ]

    userInput = {
        "numberOfMeasuresPerPage" : 12,
        "numberOfMeasuresPerRow" : 2,
        "numberOfNotesOnEachMeasure" : {
            12: {
                "pages" : [*range(1,361)]
            }
        },
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
                "pages": [*range(1,16),*range(31,46),*range(61,76),*range(91,106),*range(121,136),*range(151,166), *range(181, 196), *range(211, 226), *range(241, 256), *range(271, 286), *range(301, 316),*range(331, 346)],
                "sequenceRepetition" : 5,
                "pageMeasureHeaderSequence" : [[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4],[5,5,5,5],[6,6,6,6]],
                "headerPageRepetition" : "vertical" # horizontal vertical or none
            },
            "pattern2" : {
                "pages": [*range(16,31),*range(46,61),*range(76,91),*range(106,121),*range(136,151),*range(166,181), *range(196, 211), *range(226,241), *range(256, 271), *range(286, 301),*range(316, 331), *range(346,361)],
                "sequenceRepetition" : 5,
                "pageMeasureHeaderSequence" : [[7,7,7,7],[8,8,8,8],[9,9,9,9],[10,10,10,10], [11,11,11,11], [12,12,12,12]],
                "headerPageRepetition" : "vertical" # horizontal vertical or none
            }
            # "pattern2" : {
            #     "pages": [*range(10,15)],
            #     "sequenceRepetition" : 5,
            #     "pageMeasureHeaderSequence" : [[7,7,7,7], [8,8,8,8],[9,9,9,9],[10,10,10,10],[11,11,11,11],[12,12,12,12]],
            #     "headerPageRepetition" : "vertical" # horizontal vertical or none
            # },
            # "pattern3" : {
            #     "pages": [*range(15,18)],
            #     "sequenceRepetition" : 2,
            #     "pageMeasureHeaderSequence" : [[1,1,1,1],[2,2,2,2],[3,3,3,3],[4,4,4,4], [5,5,5,5], [6,6,6,6], [7,7,7,7], [8,8,8,8],[9,9,9,9],[10,10,10,10],[11,11,11,11],[12,12,12,12]],
            #     "headerPageRepetition" : None # or horizontal or none
            # }
        },
        "templatePatterns": {
            1 : {
                "pages" : [*range(1,31)],
                "templates" : [1,2,3,4,5,6],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            2 : {
                "pages" : [*range(31,61)],
                "templates" : [7,8,9,10,11,12], 
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            3 : {
                "pages" : [*range(61,91)],
                "templates" : [13,14,15,16,17,18],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            4 : {
                "pages" : [*range(91,121)],
                "templates" : [19,20,21,22,23,24],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            5 : {
                "pages" : [*range(121,151)],
                "templates" : [25,26,27,28,29,30],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            6 : {
                "pages" : [*range(151,181)],
                "templates" : [31,32,33,34,35,36],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            7 : {
                "pages" : [*range(181,211)],
                "templates" : [37,38,39,40,41,42],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            8 : {
                "pages" : [*range(211,241)],
                "templates" : [43,44,45,46,47,48],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            9 : {
                "pages" : [*range(241,271)],
                "templates" : [49,50,51,52,53,54],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            10 : {
                "pages" : [*range(271,301)],
                "templates" : [55,56,57,58,59,60],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            11 : {
                "pages" : [*range(301,331)],
                "templates" : [61,62,63,64,65,66],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            },
            12 : {
                "pages" : [*range(331,361)],
                "templates" : [67,68,69,70,71,72],
                "measurePageRepetition" : "horizontal" # horizontal, vertical, page, None
            } # ,
            # 2 : {
            #     "pages" : [*range(4,8)],
            #     "templates" : [8,9,10,11,12,13],  # if there is only 1 template for every measure of every page of each unit,
                                                    #then put the number of the template as many times as the number of pages in the unit
                                                    # for example [1]*10,
            #     "measurePageRepetition" : "vertical", # horizontal, vertical, page, None
            # },
            # 3 : {
            #     "pages" : [*range(8,10)],
            #     "templates" : [15,16,17],
            #     "measurePageRepetition" : "page", # horizontal, vertical, page, None
            # },
            # 4 : {
            #     "pages" : [*range(10,15)],
            #     "templates" : [18,19,20,21,22,23,24,25,26],
            #     "measurePageRepetition" : None, # horizontal, vertical, page, None
            # }
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
            },

        },
        # HEADINGS - TITLES (VARIATION - F)
        "headings" : {
            "VARIATION" : {
                "pages" : [*range(1,361)], #[*range(0,350)]
                "singleHeading" : True, #1 ή 2 ΣΤΗΛΕΣ
                "sectionNumberLimit": 5,
                "headingPageRepetition" : 3, # or None # 1 otan theloume na emfanizontai ta noumera mia fora
                "subheading" : None
            } ,
            # "A" : {
            #     "pages" : [20,21,22,23,24],
            #     "singleHeading" : True, #1 ή 2 ΣΤΗΛΕΣ
            #     "headingPageRepetition" : None, 
            #     "subheading" : "B"
            # },
            # "B" : {
            #     "pages" : [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43],
            #     "singleHeading" : False, #1 ή 2 ΣΤΗΛΕΣ
            #     "headingPageRepetition" : 1, 
            #     "subheading" : "C"
            # }
        },
        # CAPTIONS - F on the sides
        "captions" : {
            # IF THERE ARE NO CAPTIONS, DELETE EVERYTHING ABOVE 
            # AND LEAVE THE CAPTIONS DICT EMPTY
            "onlyLeft": {
                "pages" : [*range(1,361)],
                "symbol" : "F",
                "number" : True # peritto alla what ever
            }# ,
            # "everywhere" : {
            #     "pages" : [*range(6,17)],
            #     "symbol" : "Z",
            #     "number" : True,
            #     "sameNumberInRow" : False # peritto alla what ever
            # }
        }   
    }

    runApp(bookFolder, userInput)