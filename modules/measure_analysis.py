from PIL import Image
import os
import matplotlib.pyplot as plt
import numpy as np
import cv2
from IPython.display import Image
from sklearn.cluster import KMeans
import pandas as pd
import tqdm
from detecto import core, utils, visualize
from detecto.visualize import show_labeled_image, plot_prediction_grid
from torchvision import transforms
import torch
from pathlib import Path


def userInput(data):
    # NOTES = 1,2,3,4,5,6.. = labels with integers
    # FINGERING = p,i,m,a   = labels with strings

    while True:
        try:
            usePreviousData = str(input("Use previous data? Y/N "))
            if usePreviousData == 'y' or usePreviousData == 'n':
                break
            else:
                raise ValueError()
        except ValueError:
            print("That's not a correct response, try again")
            
    if usePreviousData == "n":
        while True:
            try:
                data["stringNumber"], data["noteNumber"], data["fingeringNumber"], data["chordNumber"], data["headerNumber"] = map (int, input("Enter: String Number, Note Number, Fingering Number, Chord Number, Header Number: \n").split())
                break
            except ValueError:
                print("That's not a correct response, try again")
        
        while True:
            try:
                data["noteStringExistence"] =  bool(input("Note String Existence (y or ENTER): "))
                if data["noteStringExistence"]:
                    data["noteStrings"] = list(map(int,input("Note Strings: ").strip().split()))
                else:
                    data["noteStrings"] = 0
                break
            except ValueError:
                print("That's not a correct response, try again")  
    return data

def horizontalLineDetection(imgInit):
    # Load image, convert to grayscale, Otsu's threshold
    img = imgInit.copy()
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18,1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontalContours = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    horizontalContours = horizontalContours[0] if len(horizontalContours) == 2 else horizontalContours[1]
    for hc in horizontalContours:
        cv2.drawContours(img, [hc], -1, (36,255,12), 2)
    """
    cv2.imshow('', img)
    cv2.waitKey(0) & 0xFF"""
    plt.figure(figsize=(20, 20))
    plt.imshow(img)
    plt.show()
    return horizontalContours


def sortContoursAndCreateDF(horizontalContours):
    df = pd.DataFrame(np.vstack(np.concatenate(horizontalContours)), columns=['x', 'y'])
    sortedContoursdDF = df.sort_values('y',ignore_index=True)
    return sortedContoursdDF


def removeExtraLines(df):
    while True:
        try:
            key = str(input("Are there upper lines, lower lines, both or none? (u, l, b, n): \n"))
            if key == 'u' or key == 'l' or key == 'b' or key == 'n':
                break
            else:
                raise ValueError()
        except ValueError:
            print("That's not a correct response, try again")
    
    if key == "u":
        #REMOVE UPPER LINE
        df = df[df["y"]>20]
    elif key == "l":
        # REMOVE LOWER LINE
        df = df[df["y"]< 280] 
    elif key == "b":
        df = df[df["y"]>20]
        df = df[df["y"]< 280]
    
    return df



def findStringCentroids(stringNumber, df):
    cluster_number = stringNumber + 2
    X = df[["y"]]
    kmeans = KMeans(n_clusters=cluster_number, random_state = 0).fit(X)
    centroids = np.copy(kmeans.cluster_centers_)
    sorted_centroids = np.sort(centroids, axis = 0)

    classes = sorted_centroids.flatten().tolist()
    # If the number of centroides is 8 then remove the second one because it's the beam.
    # Keep header and strings
    if len(classes) == cluster_number:
        classes.pop(1)
    return classes

def detectNotation(model, img):
    thresh = 0
    predictions = model.predict(img)
    labels, boxes, scores = predictions
    filtered_indices = np.where(scores > thresh)
    filtered_scores = scores[filtered_indices]
    filtered_boxes = boxes[filtered_indices]
    num_list = filtered_indices[0].tolist()
    filtered_labels = [labels[i] for i in num_list]
    show_labeled_image(img, filtered_boxes, filtered_labels)
    return filtered_boxes, filtered_labels, filtered_scores

    
def dataframeCreation(filtered_boxes, filtered_labels, filtered_scores):
    mdf = pd.DataFrame(filtered_boxes.numpy(), columns = ["x1", "y1", "x2", "y2"])
    mdf['Label'] = pd.Series(filtered_labels)
    mdf['Score'] = pd.Series(filtered_scores)
    # Bring label to the front
    col = mdf.pop("Label")
    mdf.insert(0, col.name, col)
    # Find the centroids
    mdf['Centroid x'] = abs(mdf['x2'] - mdf['x1'])/2 + mdf['x1']
    mdf['Centroid y'] = abs(mdf['y2'] - mdf['y1'])/2 + mdf['y1']
    # If the label is p then the centroid of Y is higher to 2/3 of the main cetroid
    mdf.loc[mdf['Label'] == "p", 'Centroid y'] = abs(mdf['y2'] - mdf['y1'])/3 + mdf['y1']    
    return mdf

    
def detectStringsOrHeader(mdf, classes):
    for element, row in mdf.iterrows():
        found = min(classes, key = lambda x:abs(x-mdf.loc[element, "Centroid y"]))    
        mdf.loc[element, "String"] = int(classes.index(found))   
    mdf["String"] = mdf["String"].astype(int)
    return mdf



def eliminateVeryCloseElements(mdf):
    # Copy df to avoid destroying the main one
    mdf = mdf.sort_values(by='Centroid x', ascending=True).reset_index(drop=True)
    # Find the mean distance between detected (and possibly wrong) items
    distances = []
    for item, row in mdf.iloc[1:].iterrows():
        distances.append(abs(mdf.loc[item,"Centroid x"] - mdf.loc[item - 1,"Centroid x"]))
    mean_distance = sum(distances)/len(distances)
    #print("mean dist:", mean_distance)

    # Erase close elements
    item = 1
    previous_item =[0]
    try:
        while item <= mdf.shape[0]:
            diff = abs(mdf.loc[item,"Centroid x"] - mdf.loc[previous_item[-1],"Centroid x"])

            if (diff < (mean_distance/2)) and (mdf.loc[item,"String"] == mdf.loc[previous_item[-1],"String"]):
                #print("diff: ", diff, " mean dist / 2 : ", mean_distance/2)
                if mdf.iloc[item,5] >= mdf.iloc[previous_item[-1],5]:
                    mdf = mdf.drop(previous_item[-1]).reset_index(drop=True)
                else:
                    mdf = mdf.drop(item).reset_index(drop=True)
            else:
                previous_item.append(item)
                item += 1
    except:
        pass
    
    return mdf


def eliminateUnessescaryElementsAccordingToInput(mdf, stringNumber, noteNumber, fingeringNumber, chordNumber, headerNumber, headerExistence, noteStringExistence, noteStrings): 
    def remove_rows(main_df, rows_to_keep, index_start):
        delete_indexes = rows_to_keep.iloc[index_start:].index.tolist()
        main_df = main_df.drop(delete_indexes).reset_index(drop=True) 
        return main_df  
    # sort values by score
    mdf.sort_values(by='Score', ascending=False)

    try:
        # If no header, remove header items (string = 0)
        if not headerExistence:
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
    

        
def chordPositionDetection(mdf, chordNumber):
    # copy the main df to change the centroids temporary because of p positioning
    centroid_df = mdf.copy()
    ## Reduce the X centroid of p because it's leaning to the right
    centroid_df.loc[centroid_df['Label'] == "p", 'Centroid x']= centroid_df["Centroid x"] - abs(centroid_df["x1"]-centroid_df["x2"])/4
    
    X_chords = centroid_df[["Centroid x"]]
    kmeans_chords = KMeans(n_clusters=chordNumber, random_state = 0).fit(X_chords)
    centroids_chords = np.copy(kmeans_chords.cluster_centers_)
    sorted_centroids_chords = np.sort(centroids_chords, axis = 0)

    chord_positions = sorted_centroids_chords.flatten().tolist()
    
    for item, row in centroid_df.iterrows():
        item_found = min(chord_positions, key = lambda x:abs(x-centroid_df.loc[item, "Centroid x"]))
        # Assign the position in the main df, not the temporary one
        mdf.loc[item, "Position"] = int(chord_positions.index(item_found))

    mdf["Position"] = mdf["Position"].astype(int)
    measureDF = mdf[["Label", "String", "Position"]]
    
    return measureDF


def correction(df, img):
    print(df)
    show_labeled_image(img)
    while True:
        try:
            isDFcorredt = str(input("Is the measure's dataframe correct?: Y/N "))
            if isDFcorredt == 'y' or isDFcorredt == 'n':
                break
            else:
                raise ValueError()
        except ValueError:
            print("That's not a correct response, try again")
    
    return correctedDF


def measureAnalysis(directory, model, stringNum):
    firstFile = True
    for root, dirs, files in os.walk(directory):
        for filename in files:
            chapterDir = os.path.basename(Path(root).parents[1])
            unitDir = os.path.basename(Path(root).parents[0])
            pageFolder = (os.path.basename(root))
            path_to_img =os.path.join(directory,chapterDir, unitDir, pageFolder, filename)
            image = cv2.imread(path_to_img)
            print("Analyzing image:", path_to_img)
            horizContours = horizontalLineDetection(image)
            sortedContoursDF = sortContoursAndCreateDF(horizContours)
            contourDF = removeExtraLines(sortedContoursDF)
            centroidClasses = findStringCentroids(stringNum, contourDF)
            
            # Print the input data before showing the detected notation in order to compare
            if firstFile:
                measureData = {"stringNumber":stringNum, "noteNumber":8,"fingeringNumber" : 20, "chordNumber" : 20, "headerNumber" : 8, "headerExistence" : True, "noteStringExistence" : True, "noteStrings" : [1]}
                firstFile = False
            print(measureData)
            
            
            boxes, labels, scores = detectNotation(model, image)
            measureInfoDF = dataframeCreation(boxes, labels, scores)
            DFwithStringsDetected = detectStringsOrHeader(measureInfoDF, centroidClasses)
            DFwithVeryCloseElementsEliminated = eliminateVeryCloseElements(DFwithStringsDetected)
            # NOTES = 1,2,3,4,5,6.. = labels with integers
            # FINGERING = p,i,m,a   = labels with strings

            measureData = userInput(measureData)
            
            DFwithProperNumberOfElements = eliminateUnessescaryElementsAccordingToInput(DFwithVeryCloseElementsEliminated, **measureData)

            
            measureDFcleared = chordPositionDetection(DFwithProperNumberOfElements, measureData["chordNumber"])            
            correctedDF = correction(measureDFcleared, image)
    

            

if __name__ == '__main__':
    
    dirname = os.path.dirname(__file__)
    model_path = os.path.join(dirname, '../../model/model2.pth')
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings)