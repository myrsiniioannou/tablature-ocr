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

def measureDataFromInput(pageFolder, values):
    measureData = {
    "stringNumber":values["stringNumber"],
    "noteNumber": int([key for key, value in values["noteNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "fingeringNumber" : int([key for key, value in values["fingeringNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "chordNumber" : int([key for key, value in values["chordNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    "headerNumber" : int([key for key, value in values["headerNumber"].items() if (int(pageFolder) in value["pages"])][0]),
    #"headerExistence" : bool([key for key, value in values["headerExistence"].items() if (int(pageFolder) in value["pages"])][0]),
    "noteStringExistence" : bool([key for key, value in values["noteStringExistence"].items() if (int(pageFolder) in value["pages"])][0]),
    "noteStrings" : [int(key) for key, value in values["noteStrings"].items() if (int(pageFolder) in value["pages"])],
    }
    return measureData


def horizontalLineDetection(imgInit):
    img = imgInit.copy()
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18,1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontalContours = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    horizontalContours = horizontalContours[0] if len(horizontalContours) == 2 else horizontalContours[1]
    for hc in horizontalContours:
        cv2.drawContours(img, [hc], -1, (36,255,12), 2)
    plt.figure(figsize=(10, 10))
    plt.imshow(img)
    plt.show()
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
    show_labeled_image(img, filtered_boxes, filtered_labels)
    return filtered_boxes, filtered_labels, filtered_scores

    
def dataframeCreation(filtered_boxes, filtered_labels, filtered_scores):
    mdf = pd.DataFrame(filtered_boxes.numpy(), columns = ["x1", "y1", "x2", "y2"])
    mdf['Label'] = pd.Series(filtered_labels)
    mdf['Score'] = pd.Series(filtered_scores)
    col = mdf.pop("Label")
    mdf.insert(0, col.name, col)
    mdf['Centroid x'] = abs(mdf['x2'] - mdf['x1'])/2 + mdf['x1']
    mdf['Centroid y'] = abs(mdf['y2'] - mdf['y1'])/2 + mdf['y1']
    # If the label is p then the centroid of Y is higher to 2/3 of the main cetroid
    mdf.loc[mdf['Label'] == "p", 'Centroid y'] = abs(mdf['y2'] - mdf['y1'])/3 + mdf['y1']    
    return mdf

    
def detectStringClasses(mdf, classes):
    for element, row in mdf.iterrows():
        found = min(classes, key = lambda x:abs(x-mdf.loc[element, "Centroid y"]))    
        mdf.loc[element, "String"] = int(classes.index(found))   
    mdf["String"] = mdf["String"].astype(int)
    return mdf


def eliminateVeryCloseElements(mdf, meanChordDistance):
    mdf = mdf.sort_values(by='Centroid x', ascending=True).reset_index(drop=True)
    Strings = mdf['String'].unique().tolist()
    Strings.sort()
    closeCentroidIdxToDelete = []
    for currentString in Strings:
        currentDF = mdf[mdf["String"] == currentString]
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
    mdf.drop(closeCentroidIdxToDelete).reset_index(drop=True)
    return mdf


def eliminateUnessescaryElementsAccordingToInput(mdf, noteNumber, fingeringNumber, headerNumber, noteStringExistence, noteStrings): 
    def remove_rows(main_df, rows_to_keep, index_start):
        delete_indexes = rows_to_keep.iloc[index_start:].index.tolist()
        main_df = main_df.drop(delete_indexes).reset_index(drop=True) 
        return main_df  
    # sort values by score
    mdf.sort_values(by='Score', ascending=False)
    try:
        # If no header, remove header items (string = 0)
        if headerNumber==0:
            mdf = mdf[mdf["String"] != 0].reset_index(drop=True)
        else:
            # If header exists:
            # Header notations includes only letters, therefore delete possible integers
            rows_with_int_at_header = mdf.index[(mdf['String'] == 0) & (mdf["Label"].astype(str).str.isdigit())].tolist()
            mdf = mdf.drop(mdf.index[rows_with_int_at_header]).reset_index(drop=True)
            # Remove extra header notes based on the given header number
            header_notes_df = mdf[mdf["String"] == 0]
            mdf = remove_rows(mdf, header_notes_df, headerNumber)
        # Remove extra notes
        notes_df = mdf[mdf["Label"].astype(str).str.isdigit()]
        mdf = remove_rows(mdf, notes_df, noteNumber)
        # FINGERING
        ### If there's a note string(s), keep only the notes there and delete the fingering
        if noteStringExistence:
            for fs in noteStrings:
                # Select the fingering string and all the labels that are not integers, meaning string symbols
                strings_on_fingering = mdf[(mdf["String"]== fs) & (~mdf["Label"].astype(str).str.isdigit())].index.tolist()
                # Drop them
                mdf = mdf.drop(mdf.index[strings_on_fingering]).reset_index(drop=True)
        # Remove extra fingering
        fingering_df = mdf[~mdf["Label"].astype(str).str.isdigit() & (mdf['String'] != 0)]
        mdf = remove_rows(mdf, fingering_df, fingeringNumber)
    except:
        pass
    # Sort according to Centroid x
    mdf = mdf.sort_values(by='Centroid x', ascending = True).reset_index(drop=True)
    return mdf
    
  
def findChordCentroidsAndMeanDistance(mdf, chordNumber):
    centroid_df = mdf.copy()
    ## Reduce the X centroid of p because it's leaning to the right
    centroid_df.loc[centroid_df['Label'] == "p", 'Centroid x']= centroid_df["Centroid x"] - abs(centroid_df["x1"]-centroid_df["x2"])/3
    chordClusters = len(mdf.index) if chordNumber >=len(mdf.index) else chordNumber
    X_chords = centroid_df[["Centroid x"]]
    kmeans_chords = KMeans(n_clusters=chordClusters, random_state = 0).fit(X_chords)
    centroids_chords = np.copy(kmeans_chords.cluster_centers_)
    sorted_centroids_chords = np.sort(centroids_chords, axis = 0)
    chord_positions = sorted_centroids_chords.flatten().tolist()
    meanChordDistance = np.mean(np.diff(np.array(chord_positions))).astype(float)
    return centroid_df, chord_positions, meanChordDistance


def findChordPositions(mdf, chord_positions, centroid_df):
    for item, row in centroid_df.iterrows():
        item_found = min(chord_positions, key = lambda x:abs(x-centroid_df.loc[item, "Centroid x"]))
        # Assign the position in the main df, not the temporary one
        mdf.loc[item, "Position"] = int(chord_positions.index(item_found))
    mdf["Position"] = mdf["Position"].astype(int)
    measureDF = mdf[["Label", "String", "Position"]]
    return measureDF


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
        print("{0:.0%}".format(int(fileNumber/(numberOfFilesToAnalyze/10))*0.1),'of files done..')


def analyzeMeasure(measure, root, directory, stringNum, model):
    path_to_img, pageFolder = findPathtoIMGandPageFolder(root, directory, measure)
    measureData = measureDataFromInput(pageFolder, pageValues)
    image = cv2.imread(path_to_img)
    horizContours = horizontalLineDetection(image)
    sortedContoursDF = sortContoursAndCreateDF(horizContours)
    centroidClasses = findStringCentroidsWithDBSCAN(stringNum, sortedContoursDF)
    boxes, labels, scores = detectNotation(model, image)
    measureInfoDF = dataframeCreation(boxes, labels, scores)
    dfWithDetectedStrings = detectStringClasses(measureInfoDF, centroidClasses)


    centroid_df, chord_positions, meanChordDistance = findChordCentroidsAndMeanDistance(dfWithDetectedStrings, measureData["chordNumber"])


    dfwithVeryCloseElementsEliminated = eliminateVeryCloseElements(centroid_df, meanChordDistance)

    measureDFcleared = findChordPositions(dfwithVeryCloseElementsEliminated, chord_positions, dfwithVeryCloseElementsEliminated)
    #
    # DFwithProperNumberOfElements = eliminateUnessescaryElementsAccordingToInput(dfwithVeryCloseElementsEliminated, **measureData)


    # #############   REPEATED  ###########################measureDFcleared = findChordPositions(DFwithProperNumberOfElements, measureData["chordNumber"])


    # measureDFcleared.to_csv(f"{path_to_img[:-4]}.csv", encoding='utf-8', index=False)


def iterateOverMeasuresOfCurrentPage(root, measures, listWithAlreadyAnalyzedFiles, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze, model, fileNumber, directory, stringNum):
    for measure in measures:
        if measure[:-4] not in listWithAlreadyAnalyzedFiles:
            analyzeMeasure(measure, root, directory, stringNum, model)
            printPercentageOfAnalyzedFiles(fileNumber, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze)
            fileNumber+=1
    return fileNumber




def measureAnalysis(directory, model, stringNum, pageValues):
    print("Measure Analysis process starting..")
    fileNumber = 1
    percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze = calculatePercentageOfAnalyzedFiles(directory)  
    for root, dirs, measures in os.walk(directory):
        listWithAlreadyAnalyzedFiles = checkIfResumed(measures)
        fileNumber = iterateOverMeasuresOfCurrentPage(root, measures, listWithAlreadyAnalyzedFiles, percentagesOfFilestoGetAnalyzed, numberOfFilesToAnalyze, model, fileNumber, directory, stringNum)
    print("Measure Analysis done!")




            
if __name__ == '__main__':
    pageValues = {
        "stringNumber" : 6, 
        "noteNumber": {
            "12": {
                "pages": [*range(1,3)],
            },
            "10" : {
                "pages": [*range(3,4)],
            },
            "8" : {
                "pages": [*range(4,200)]
            }
        },
        "fingeringNumber": {
            "28": {
                "pages": [*range(1,3)],
            },
            "16" : {
                "pages": [*range(3,4)],
            },
            "17" : {
                "pages": [*range(4,200)]
            }
        },
        "chordNumber": {
            "15": {
                "pages": [*range(4,6)],
            },
            "32" : {
                "pages": [*range(1,4)],
            },
            "17" : {
                "pages": [*range(6,200)]
            }
        },
        "headerNumber": {
            "0": {
                "pages": [*range(1,3)],
            },
            "16" : {
                "pages": [*range(3,4)],
            },
            "17" : {
                "pages": [*range(4,200)]
            }
        },
        "noteStringExistence": {
            True: {
                "pages": [*range(1,3)],
            },
            False : {
                "pages": [*range(4,200)],
            }
        },
        "noteStrings": {
            "1": {
                "pages": [*range(1,3)],
            },
            "2" : {
                "pages": [*range(4,200)],
            }
        }
    }

    dirname = os.path.dirname(__file__)
    model_path = os.path.join(dirname, '../../model/model5Merged.pth')
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\firstBook"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings, pageValues)
