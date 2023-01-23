import shutup; shutup.please()
import sys
import os
sys.path.append('modules')
from PIL import Image
import os
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
import numpy as np
import cv2
import pandas as pd
from scipy.ndimage import rotate
import tqdm as notebook_tqdm
from detecto import core, utils, visualize
from detecto.visualize import show_labeled_image, plot_prediction_grid
from torchvision import transforms
import copy
from pathlib import Path
import pickle


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


def DFresultOptimization(allDFs, elementsOnMeasure):
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
        extraElements = len(df) - elementsOnMeasure
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



def iterateOverBookPages(root, files, elementNumberPerMeasure, percentagesOfFilesDone):
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
        

def analysis(elementNumberPerMeasure, bookDirectory, model):
    print("Starting Template-Based Tablature OCR...")
    percentagesOfFilesDone = findNumberOfJPGsInPercentages(bookDirectory)
    for root, dirs, files in os.walk(bookDirectory):
        iterateOverBookPages(root, files, elementNumberPerMeasure, percentagesOfFilesDone)
    print("Book Done!")


def rendering(directory):

    return None



# 3 ama teleionei to vlivio na diagrafei ola ta pickle file kai na ta kanei save se ena arxeio vivliou (mallon ana selida?)


if __name__ == '__main__':
    bookFolder = r'C:\Users\merse\Desktop\Tablature OCR\books_to_analyze\firstBookTEST'
    model_path = r"C:\Users\merse\Desktop\Tablature OCR\model\model5Merged.pth"
    model = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    elementsOnMeasure = 12
    analysis(elementsOnMeasure, bookFolder, model)

    rendering(bookFolder)