import shutup; shutup.please()
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2
from sklearn.cluster import KMeans,DBSCAN
import pandas as pd
from detecto import core
from detecto.visualize import show_labeled_image
from pathlib import Path
from scipy import ndimage
import copy
import math

def measureDataFromInput(pageFolder, values):
    measureData = {
    "stringNumber":values["stringNumber"],
    "noteNumber": int([key for key, value in values["noteNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "fingeringNumber" : int([key for key, value in values["fingeringNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "chordNumber" : int([key for key, value in values["chordNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "headerNumber" : int([key for key, value in values["headerNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "noteStrings" : [int(key) for key, value in values["noteStrings"].items() if (int(pageFolder) in value["pages"])]
    }
    return measureData


def horizontalLineDetection(imgInit, stringNumber):
    detectionVariable = 18 if int(stringNumber) == 6 else 50
    img = imgInit.copy()
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (detectionVariable,1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontalContours = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    horizontalContours = horizontalContours[0] if len(horizontalContours) == 2 else horizontalContours[1]
    for hc in horizontalContours:
        cv2.drawContours(img, [hc], -1, (36,255,12), 2)
    # Uncomment to show Horizontal Line Detection
    #plt.figure(figsize=(10, 10))
    #plt.imshow(img)
    #plt.show()
    return horizontalContours


def sortContoursAndCreateDF(horizontalContours):
    df = pd.DataFrame(np.vstack(np.concatenate(horizontalContours)), columns=['x', 'y'])
    sortedContoursdDF = df.sort_values('y',ignore_index=True)
    return sortedContoursdDF


def eliminateExtraClasses(stringNumber, classes):
    if len(classes) == stringNumber + 3:
        classes.pop(0)
        classes.pop()
    elif len(classes) == stringNumber + 2:
        differences = []
        for idx,el in enumerate(classes[:-1]):
            differences.append(abs(classes[idx+1]-classes[idx]))
        if differences.index(sorted(differences)[-2]) == 0:
            classes.pop(0)
        elif differences.index(sorted(differences)[-2]) == 6:
            classes.pop()
    return classes


def findStringCentroidsWithDBSCAN(stringNumber, df):
    X = df[["y"]]
    clusters = DBSCAN(eps=10, min_samples=3).fit(X)
    classNumber = np.unique(clusters.labels_)
    classStringNumber = list(classNumber)
    lengthOfEachClassInList = []
    for classString in classStringNumber:
        lengthOfEachClassInList.append(len(clusters.labels_[clusters.labels_==classString]))
    listOfSameClassElements = []
    for idx,i in enumerate(lengthOfEachClassInList):
        sumOfSameCluster = 0
        for j in range(idx+1):
            sumOfSameCluster += lengthOfEachClassInList[j]
        listOfSameClassElements.append(sumOfSameCluster)
    listOfSameClassElementsStart = [0]
    listOfSameClassElementsStart.extend(listOfSameClassElements[:-1])
    listOfSameClassElementsEnd = [x-1 for idx, x in enumerate(listOfSameClassElements)]
    list0fCentroids = []
    for idx,i in enumerate(listOfSameClassElementsStart):
        mean = ndimage.mean(clusters.components_[listOfSameClassElementsStart[idx]:listOfSameClassElementsEnd[idx]])
        list0fCentroids.append(mean)
    classes = sorted(list0fCentroids)
    finalListOfClasses = eliminateExtraClasses(stringNumber, classes)
    return finalListOfClasses


def findStringCentroidsWithKMEANS(stringNumber, df):
    cluster_number = stringNumber + 2 # BECAUSE OF THE TWO LINES DETECTED BELOW HEADER
    X = df[["y"]]
    kmeans = KMeans(n_clusters=cluster_number, random_state = 0).fit(X)
    centroids = np.copy(kmeans.cluster_centers_)
    sorted_centroids = np.sort(centroids, axis = 0)
    classes = sorted_centroids.flatten().tolist()
    classes.pop(1)
    return classes


def detectNotation(model, img):
    thresh = 0.15
    predictions = model.predict(img)
    labels, boxes, scores = predictions
    filtered_indices = np.where(scores > thresh)
    filtered_scores = scores[filtered_indices]
    filtered_boxes = boxes[filtered_indices]
    num_list = filtered_indices[0].tolist()
    filtered_labels = [labels[i] for i in num_list]
    # Uncomment to show detected letter in image
    #show_labeled_image(img, filtered_boxes, filtered_labels)
    return filtered_boxes, filtered_labels, filtered_scores

    
def dataframeCreation(filtered_boxes, filtered_labels, filtered_scores):
    df = pd.DataFrame(filtered_boxes.numpy(), columns = ["x1", "y1", "x2", "y2"])
    df['Label'] = pd.Series(filtered_labels)
    df['Score'] = pd.Series(filtered_scores)
    col = df.pop("Label")
    df.insert(0, col.name, col)
    df['Centroid x'] = abs(df['x2'] - df['x1'])/2 + df['x1']
    df['Centroid y'] = abs(df['y2'] - df['y1'])/2 + df['y1']
    # If the label is p then the centroid of Y is higher to 2/3 of the main cetroid
    df.loc[df['Label'] == "p", 'Centroid y'] = abs(df['y2'] - df['y1'])/3 + df['y1']    
    return df


def adjustPcentroids(df):
    # Centroid Y of p is higher to 2/3 of the main cetroid
    df.loc[df['Label'] == "p", 'Centroid y'] = abs(df['y2'] - df['y1'])/3 + df['y1']
    ## Reduce the X centroid of p because it's leaning to the right
    df.loc[df['Label'] == "p", 'Centroid x'] = df["Centroid x"] - abs(df["x1"]-df["x2"])/3
    return df


def detectAndAssignStringClasses(df, classes):
    for element, row in df.iterrows():
        found = min(classes, key = lambda x:abs(x-df.loc[element, "Centroid y"]))    
        df.loc[element, "String"] = int(classes.index(found))   
    df["String"] = df["String"].astype(int)
    return df


def eliminateVeryCloseElements(df, meanChordDistance):
    df = df.sort_values(by='Centroid x', ascending=True).reset_index(drop=True)
    Strings = df['String'].unique().tolist()
    Strings.sort()
    closeCentroidIdxToDelete = []
    for currentString in Strings:
        currentDF = df[df["String"] == currentString]
        if len(currentDF) != 0:
            previousIdx = currentDF.iloc[0].name
            previousElement = currentDF.iloc[0]
            for idx, row in currentDF[1:].iterrows():
                diff = abs(previousElement["Centroid x"] - row["Centroid x"])
                if (diff< meanChordDistance*0.5) and (previousIdx not in closeCentroidIdxToDelete):
                    if previousElement["Score"] > row["Score"]:
                        closeCentroidIdxToDelete.append(idx)
                    else:
                        closeCentroidIdxToDelete.append(previousIdx)
                previousIdx = copy.copy(idx)
                previousElement = row.copy()
    closeCentroidIdxToDelete = list(set(closeCentroidIdxToDelete))
    closeCentroidIdxToDelete.sort()
    df.drop(closeCentroidIdxToDelete).reset_index(drop=True)
    return df


def eliminateDuplicateElements(df):
    Strings = df['String'].unique().tolist()
    Strings.sort()
    idxsToDelete = []
    for currentString in Strings:
        dfWithDuplicateHeaderPositions = df.loc[df["String"] == currentString]
        dfDuplicateHeaderPositions = dfWithDuplicateHeaderPositions[dfWithDuplicateHeaderPositions['Position'].duplicated(keep=False)]
        if len(dfDuplicateHeaderPositions.columns) != 0:
            positionsWithDuplicates = dfDuplicateHeaderPositions["Position"].unique().tolist()
            for position in positionsWithDuplicates:
                subsetDF1 = dfDuplicateHeaderPositions[dfDuplicateHeaderPositions["Position"] == position]
                idxOfMax = subsetDF1["Score"].idxmax().item()
                dfOfDuplicatesWithoutTheMaxValue = subsetDF1.drop(idxOfMax)
                idxsToDelete.extend(dfOfDuplicatesWithoutTheMaxValue.index.values.tolist())
    if idxsToDelete:
        df = df.drop(index=idxsToDelete).reset_index(drop=True).sort_values(by=['Position'])
    return df


def removeRowsByLowestScore(df, subsetToClear, IndexRangeToDelete):
    # IndexRangeToDelete is basically the limit/number of elements of the measure
    delete_indexes = subsetToClear.iloc[IndexRangeToDelete:].index.tolist()
    if delete_indexes:
        df.drop(delete_indexes).reset_index(drop=True) 
    return df


def eliminateRedundantElements(df, noteNumber, fingeringNumber, headerNumber, noteStrings): 
    df.sort_values(by='Score', ascending=False)
    # Clear Header
    if headerNumber == 0:
        df = df[df["String"] != 0].reset_index(drop=True)
    else:
        intInHeaderRows = df.index[(df['String'] == 0) & (df["Label"].astype(str).str.isdigit())].tolist()
        if intInHeaderRows:
            df = df.drop(df.index[intInHeaderRows]).reset_index(drop=True)   
        header_notes_df = df[df["String"] == 0]
        df = removeRowsByLowestScore(df, header_notes_df, headerNumber)
    #Clear Notes (False Fingering on note strings)
    if noteStrings:
        for noteString in noteStrings:
            fingeringOnNoteString = df[(df["String"]== 1) & (~df["Label"].astype(str).str.isdigit())].index.tolist()
            if fingeringOnNoteString:
                df.drop(index=fingeringOnNoteString, inplace = True)
                df.reset_index(drop=True, inplace = True)
    # Clear Notes
    notes_df = df[df["Label"].astype(str).str.isdigit()]
    df = removeRowsByLowestScore(df, notes_df, noteNumber)
    # Clear Fingering
    fingering_df = df[~df["Label"].astype(str).str.isdigit() & (df['String'] != 0)]
    df = removeRowsByLowestScore(df, fingering_df, fingeringNumber)
    df = df.sort_values(by='Centroid x', ascending = True).reset_index(drop=True)
    return df

  
def findChordCentroidsAndMeanDistance(df, chordNumber):
    chordClusters = len(df.index) if chordNumber >=len(df.index) else chordNumber
    X_chords = df[["Centroid x"]]
    kmeans_chords = KMeans(n_clusters=chordClusters, random_state = 0).fit(X_chords)
    centroids_chords = np.copy(kmeans_chords.cluster_centers_)
    sorted_centroids_chords = np.sort(centroids_chords, axis = 0)
    chord_positions = sorted_centroids_chords.flatten().tolist()
    meanChordDistance = np.mean(np.diff(np.array(chord_positions))).astype(float)
    return chord_positions, meanChordDistance


def findChordPositions(df, chord_positions, centroid_df):
    for item, row in df.iterrows():
        item_found = min(chord_positions, key = lambda x:abs(x-df.loc[item, "Centroid x"]))
        df.loc[item, "Position"] = int(chord_positions.index(item_found))
    df["Position"] = df["Position"].astype(int)
    return df


def checkIfResumed(measures):
    listOfAnalyzedFiles = []
    for measure in measures:
        if measure.endswith(".csv"):
            listOfAnalyzedFiles.append(measure[:-4])
    return listOfAnalyzedFiles


def findNumberOfFilesNotAnalyzed(path):
    os.chdir(path)
    JPGfiles = 0
    CSVfiles = 0
    for p,n,f in os.walk(os.getcwd()):
        for a in f:
            if a.endswith('.jpg'):
                JPGfiles+=1
            elif a.endswith('.csv'):
                CSVfiles+=1
    notAnalyzedFiles = abs(JPGfiles - CSVfiles)
    return notAnalyzedFiles


def calculatePercentageOfAnalyzedFiles(dir):
    fileNumberToAnalyze = findNumberOfFilesNotAnalyzed(dir)
    percentaces = [x for x in range(0, fileNumberToAnalyze, round(fileNumberToAnalyze/10))]
    percentaces.pop(0)
    return  percentaces, fileNumberToAnalyze


def findPathtoIMGandPageFolder(root, directory, measure):
    chapterDir = os.path.basename(Path(root).parents[1])
    unitDir = os.path.basename(Path(root).parents[0])            
    pageFolder = (os.path.basename(root))
    path_to_img =os.path.join(directory, chapterDir, unitDir, pageFolder, measure)
    return path_to_img, pageFolder


def printPercentageOfAnalyzedFiles(fileNumber, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze):
    if fileNumber in percentagesOfFilestoGetAnalyzed:
        print("{:.0%}".format(int(fileNumber*100/numberOfFilesToAnalyze)/100),'of files done..')


def analyzeMeasure(measure, root, directory, stringNum, model, pageValues):
    path_to_img, pageFolder = findPathtoIMGandPageFolder(root, directory, measure)
    measureData = measureDataFromInput(pageFolder, pageValues)
    image = cv2.imread(path_to_img)
    horizContours = horizontalLineDetection(image, measureData["stringNumber"])
    sortedContoursDF = sortContoursAndCreateDF(horizContours)
    centroidClasses = findStringCentroidsWithKMEANS(stringNum, sortedContoursDF)
    boxes, labels, scores = detectNotation(model, image)
    measureInfoDF = dataframeCreation(boxes, labels, scores)
    measureWithAdjustedPcentroids = adjustPcentroids(measureInfoDF)
    dfWithDetectedStrings = detectAndAssignStringClasses(measureWithAdjustedPcentroids, centroidClasses)
    # Next line doesn't return a df - It's the only one
    chord_positions, meanChordDistance = findChordCentroidsAndMeanDistance(dfWithDetectedStrings, measureData["chordNumber"])
    dfwithVeryCloseElementsEliminated = eliminateVeryCloseElements(dfWithDetectedStrings, meanChordDistance)
    measureDfWithPositions = findChordPositions(dfwithVeryCloseElementsEliminated, chord_positions, dfwithVeryCloseElementsEliminated)
    dfWithoutDuplicateElements = eliminateDuplicateElements(measureDfWithPositions)
    DFwithProperNumberOfElements = eliminateRedundantElements(dfWithoutDuplicateElements, measureData["noteNumber"], measureData["fingeringNumber"], measureData["headerNumber"], measureData["noteStrings"])
    finalMeasureDF = DFwithProperNumberOfElements[["Label", "String", "Position"]]
    finalMeasureDF.to_csv(f"{path_to_img[:-4]}.csv", encoding='utf-8', index=False)


def iterateOverMeasuresOfCurrentPage(root, measures, listWithAlreadyAnalyzedFiles, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze, model, fileNumber, directory, stringNum, pageValues):
    for measure in measures:
        if measure[:-4] not in listWithAlreadyAnalyzedFiles:
            analyzeMeasure(measure, root, directory, stringNum, model, pageValues)
            printPercentageOfAnalyzedFiles(fileNumber, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze)
            fileNumber+=1
    return fileNumber


def measureAnalysis(directory, model, stringNum, pageValues):
    print("Measure Analysis process starting..")
    fileNumber = 1
    percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze = calculatePercentageOfAnalyzedFiles(directory)
    for root, dirs, measures in os.walk(directory):
        listWithAlreadyAnalyzedFiles = checkIfResumed(measures)
        fileNumber = iterateOverMeasuresOfCurrentPage(
                                            root,
                                            measures,
                                            listWithAlreadyAnalyzedFiles,
                                            percentagesOfFilestoGetAnalyzed,
                                            numberOfFilesToAnalyze,
                                            model,
                                            fileNumber,
                                            directory,
                                            stringNum,
                                            pageValues
                                            )
    print("Measure Analysis done!")



if __name__ == '__main__':
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
        "noteStrings": {
            "1": {
                "pages": [*range(1,347)],
            }
        }
    }



    dirname = os.path.dirname(__file__)
    model_path = os.path.join(dirname, '../../model/model5Merged.pth')
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\firstBook"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings, pageValues)
