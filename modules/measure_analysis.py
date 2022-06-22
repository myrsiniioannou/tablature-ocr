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


def userInput():
    # NOTES = 1,2,3,4,5,6.. = labels with integers
    # FINGERING = p,i,m,a   = labels with strings

    stringNumber = 6
    noteNumber = 8
    fingeringNumber = 20
    chord_number = 20

    headerNumber = 8
    headerExistence = True
    noteStringExistence = True
    noteStrings = [1]

def horizontalLineDetection():
    # Load image, convert to grayscale, Otsu's threshold
    image = cv2.imread(path_to_img)
    imgCp = image.copy()
    gray = cv2.cvtColor(imgCp,cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (18,1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    horizontalContours = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    horizontalContours = horizontalContours[0] if len(horizontalContours) == 2 else horizontalContours[1]
    for hc in horizontalContours:
        cv2.drawContours(imgCp, [hc], -1, (36,255,12), 2)
    plt.figure(figsize=(20, 20))
    plt.imshow(imgCp)



def sortContours():
    df = pd.DataFrame(np.vstack(np.concatenate(horizontalContours)), columns=['x', 'y'])
    sorted_df = df.sort_values('y',ignore_index=True)


def removeExtraLines():
    # REMOVE UPPER LINE
    #sorted_df = sorted_df[sorted_df["y"]>20]

    # REMOVE LOWER LINE
    #sorted_df = sorted_df[sorted_df["y"]< 280]
    pass


def findStringCentroids(stringNumber):
    cluster_number = stringNumber + 2
    X = sorted_df[["y"]]
    kmeans = KMeans(n_clusters=cluster_number, random_state = 0).fit(X)
    centroids = np.copy(kmeans.cluster_centers_)
    sorted_centroids = np.sort(centroids, axis = 0)

    classes = sorted_centroids.flatten().tolist()
    # If the number of centroides is 8 then remove the second one because it's the beam.
    # Keep header and strings
    if len(classes) == cluster_number:
        classes.pop(1)
    classes

def detectNotation(model, image):
    thresh = 0
    predictions = model.predict(image)
    labels, boxes, scores = predictions
    filtered_indices = np.where(scores > thresh)
    filtered_scores = scores[filtered_indices]
    filtered_boxes = boxes[filtered_indices]
    num_list = filtered_indices[0].tolist()
    filtered_labels = [labels[i] for i in num_list]
    show_labeled_image(image, filtered_boxes, filtered_labels)

    
def dataframeCreation(mdf):
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
    
    
def detectStrings(mdf):
    for element, row in mdf.iterrows():
        found = min(classes, key = lambda x:abs(x-mdf.loc[element, "Centroid y"]))    
        mdf.loc[element, "String"] = int(classes.index(found))   
    mdf["String"] = mdf["String"].astype(int)



def eliminateVeryCloseElements(mdf):
    # Copy df to avoid destroying the main one
    mdf = mdf.sort_values(by='Centroid x', ascending=True).reset_index(drop=True)
    # Find the mean distance between detected (and possibly wrong) items
    distances = []
    for item, row in mdf.iloc[1:].iterrows():
        distances.append(abs(mdf.loc[item,"Centroid x"] - mdf.loc[item - 1,"Centroid x"]))
    mean_distance = sum(distances)/len(distances)
    print("mean dist:", mean_distance)

    # Erase close elements
    item = 1
    previous_item =[0]
    try:
        while item <= mdf.shape[0]:
            diff = abs(mdf.loc[item,"Centroid x"] - mdf.loc[previous_item[-1],"Centroid x"])

            if (diff < (mean_distance/2)) and (mdf.loc[item,"String"] == mdf.loc[previous_item[-1],"String"]):
                print("diff: ", diff, " mean dist / 2 : ", mean_distance/2)
                if mdf.iloc[item,5] >= mdf.iloc[previous_item[-1],5]:
                    mdf = mdf.drop(previous_item[-1]).reset_index(drop=True)
                else:
                    mdf = mdf.drop(item).reset_index(drop=True)

            else:
                previous_item.append(item)
                item += 1
    except:
        pass



def eliminateUnessescaryElements(mdf): 
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
    
    
def findThePositionInTheChordSequence():
    # copy the main df to change the centroids temporary because of p positioning
    centroid_df = mdf.copy()
    ## Reduce the X centroid of p because it's leaning to the right
    centroid_df.loc[centroid_df['Label'] == "p", 'Centroid x']= centroid_df["Centroid x"] - abs(centroid_df["x1"]-centroid_df["x2"])/4
        
def chordPositionDetection():
    
    X_chords = centroid_df[["Centroid x"]]
    kmeans_chords = KMeans(n_clusters=chord_number, random_state = 0).fit(X_chords)
    centroids_chords = np.copy(kmeans_chords.cluster_centers_)
    sorted_centroids_chords = np.sort(centroids_chords, axis = 0)

    chord_positions = sorted_centroids_chords.flatten().tolist()
    
    for item, row in centroid_df.iterrows():
        item_found = min(chord_positions, key = lambda x:abs(x-centroid_df.loc[item, "Centroid x"]))
        # Assign the position in the main df, not the temporary one
        mdf.loc[item, "Position"] = int(chord_positions.index(item_found))

    mdf["Position"] = mdf["Position"].astype(int)
    measureDF = mdf[["Label", "String", "Position"]]



def measureAnalysis(directory, model):

    for root, dirs, files in os.walk(directory):
        for filename in files:
            baseDirectory = Path(directory).parents[3]
            print(baseDirectory)
            path_to_img =os.path.join(directory, filename)
            print(path_to_img)
            #image = cv2.imread(path_to_img)
    



if __name__ == '__main__':
    
    dirname = os.path.dirname(__file__)
    model_path = os.path.join(dirname, '../../model/model2.pth')
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = os.path.join(dirname, "../../extracted_measures/book1")
    measureAnalysis(extractedBookDirectory, trainedModel)