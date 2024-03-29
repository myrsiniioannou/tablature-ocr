import os
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
from scipy.ndimage import rotate


def subpart_analysis(img, denoise, templateWindowSize = 4):
    new_image = img.copy()
    if denoise:
        print("Adding fast denoising...")
        new_image = cv2.fastNlMeansDenoisingColored(new_image,None,100,0,0,templateWindowSize)
    gray = cv2.cvtColor(new_image, cv2.COLOR_BGR2GRAY)
    ret, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_OTSU)
    threshold = ~binary
    contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    with_contours = cv2.drawContours(new_image, contours, -1,(255,0,200),10)
    tablature_coords = []
    # Draw a bounding box around all contours
    for index, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        # Make sure contour area is large enough
        if (cv2.contourArea(c)) > 40000:
            cv2.rectangle(with_contours,(x,y), (x+w,y+h), (255,0,0), 5)
            tablature_coords.append({"x":x, "y":y, "w":w, "h":h})
            #print("Coordinates:",x,y,w,h)
    imS = resizeImage(with_contours)
    cv2.imshow('', imS)
    return tablature_coords


def retryWithFastDenoise(keyboardResponse, img):
    fistIteration = True
    templateWindowSize = 15
    while keyboardResponse == ord('n'):
        if fistIteration:
            fistIteration = False
        else:
            templateWindowSize = templateWindowSizeInput()
        tabCoords = subpart_analysis(img, True, templateWindowSize)
        keyboardResponse = keyResponse()
    return tabCoords


def resizeImage(img):
    scaleDown = 0.35
    height, width = img.shape[:2]
    imge = cv2.resize(img, (int(width*scaleDown), int(height*scaleDown)))
    return imge


def keyResponse():
    while True:
        k = cv2.waitKey(0) & 0xFF
        if k == ord('y') or k == ord('n'):
                cv2.destroyAllWindows()
                break
    return k


def templateWindowSizeInput():
    while True:
        try:
            tempWindowSize = int(input("Provide Template Window Size (~=21):"))
            break
        except:
            print("That's not an integer. Try again")
    return tempWindowSize


def sort_tablature_coordinates(tabCoordinates):
    sorted_tablature_coords = sorted(tabCoordinates, key=lambda x: (x["y"], x["x"]))
    for i in range(0, len(sorted_tablature_coords)-1):
        denominator = 6
        if abs(sorted_tablature_coords[i]['y']-sorted_tablature_coords[i+1]['y'])<= (sorted_tablature_coords[i]['h']/denominator):
            if sorted_tablature_coords[i]['x']>sorted_tablature_coords[i+1]['x']:
                sorted_tablature_coords[i], sorted_tablature_coords[i+1]  = sorted_tablature_coords[i+1], sorted_tablature_coords[i]
    return sorted_tablature_coords


def find_tablature_coordinates(img):
    tablatureCoordinates = subpart_analysis(img, False)
    response = keyResponse()
    # If the image's contours are not good enough, try fast denoise
    if response == ord('n'):
        tablatureCoordinates = retryWithFastDenoise(response, img)
    sortedTabCoords = sort_tablature_coordinates(tablatureCoordinates)
    return sortedTabCoords


def plot_the_tablature_coordinates_found_for_verification(tabs, img):
    marginConfirmation = "y"
    margin = 0
    while marginConfirmation == "y":
        contrast = 5 # Contrast control (1.0-3.0)
        brightness = -600 # Brightness control (0-100)
        imge = cv2.addWeighted(img, contrast, img, 0, brightness)
        fig = plt.figure(figsize=(10, 20))
        tab = []
        for index, i in enumerate(tabs):
            tab.append(imge[i["y"] - margin : i["y"] + i["h"] + margin, i["x"] - margin : i["x"] + i["w"] + margin])
            number_of_rows = int(len(tabs)/2)
            fig.add_subplot(number_of_rows, 3, index+1)
            plt.gca().set_title(index+1, fontsize=10)
            plt.gca().axes.xaxis.set_visible(False)
            plt.gca().axes.yaxis.set_visible(False)
            plt.imshow(tab[index])
            fig.tight_layout()
        plt.show()
        
        while True:
            try:
                marginConfirmation = str(input("Margin addition? (y/n):"))
                if marginConfirmation =="y" or marginConfirmation =="n":
                    break
                else:
                    raise ValueError()
            except ValueError:
                print("Incorrect input. Try again")
                
                
        if marginConfirmation == "y":
            while True:
                try:
                    margin = int(input("Provide Margin (-20 to 30):"))
                    if margin < -20 or margin > 30:
                        raise ValueError
                    break
                except ValueError:
                    print("Invalid integer. The number must be an integer and in the range of -20 to 50.")

            for dic in tabs:
                for key, value in dic.items():
                    marginValue = 0
                    if key=="x" or key=="y":
                        marginValue = int(-margin/2)
                    else:
                        marginValue = margin
                    dic[key] = dic[key] + marginValue
        else:
            break
    return tabs


def saveMeasures(img, tabs, bookFolder, unitFolder, currentFile):
    contrast = 5 # Contrast control (1.0-3.0)
    brightness = -600 # Brightness control (0-100)
    img = cv2.addWeighted(img, contrast, img, 0, brightness)
    chapterfolder=  os.path.basename(Path(unitFolder).parents[0])
    subPartsPath = os.path.join(Path(unitFolder).parents[3],"extracted_measures", bookFolder, chapterfolder, os.path.basename(unitFolder), currentFile )
    if not os.path.exists(subPartsPath):
        os.makedirs(subPartsPath)
    for index, i in enumerate(tabs):
        cropped_img = img[i["y"] : i["y"] + i["h"] , i["x"]: i["x"] + i["w"]]
        gray_cropped_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f"{subPartsPath}/{index}.jpg", gray_cropped_img)


def correct_skew(image, delta=0.2, limit=10):
    def determine_score(arr, angle):
        data = rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return histogram, score
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 
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


def skewMeasures(pathToFile, filename):
    image = cv2.imread(pathToFile)
    angle, rotated = correct_skew(image)
    # Save rotated images to directory. Add a zero in case there's one integer in the file name, for better future sorting.
    if len(str(filename[:-4])) == 1:
        cv2.imwrite(f"{Path(pathToFile).parent}/0{filename[:-4]}_rotated.jpg", rotated)
    else:
        cv2.imwrite(f"{Path(pathToFile).parent}/{filename[:-4]}_rotated.jpg", rotated)


def findMeasureDirectory(root, directory, filename):
    baseDirectory = Path(root).parents[3]
    exctractedImgsDirectory = "extracted_measures"
    bookDirectory = os.path.basename(os.path.normpath(directory))
    chapterDirectory = os.path.basename(os.path.normpath(Path(root).parents[0]))
    unitDirectory = os.path.basename(os.path.normpath(root))
    fileDirectory = filename[:-4]
    measuresDirectoryPath = os.path.join(baseDirectory ,exctractedImgsDirectory, bookDirectory, chapterDirectory, unitDirectory,fileDirectory)
    return measuresDirectoryPath


def calculatePercentageOfFiles(directory, dir_path):
    totalNumberOfFiles = 0
    for root, dirs, files in os.walk(dir_path):
       totalNumberOfFiles += len(files)
    percentagesOfFiles = [x for x in range(0, totalNumberOfFiles, round(totalNumberOfFiles/10))]
    return totalNumberOfFiles, percentagesOfFiles


def deleteOldNotRotatedMeasures(dir_path):
    for root, dirs, files in os.walk(dir_path):
        for index, filename in enumerate(files, 1):
            path_to_img = os.path.join(root, filename)
            if path_to_img.endswith('.jpg') and not path_to_img.endswith('rotated.jpg'):
                os.remove(path_to_img)


def startSkewingProcess(directory):
    print("Skewing process starting..")
    dir_path = os.path.join("../extracted_measures", os.path.basename(directory))
    totalNumberOfFiles, percentagesOfFiles = calculatePercentageOfFiles(directory, dir_path)
    fileNumber = 1
    for root, dirs, files in os.walk(dir_path):
        for index, filename in enumerate(files, 1):
            path_to_img = os.path.join(root, filename)
            skewMeasures(path_to_img, filename)
            if fileNumber in percentagesOfFiles:
                print("{0:.0%}".format(int(fileNumber/(totalNumberOfFiles/10))*0.1),'of files done..')
            fileNumber+=1
    deleteOldNotRotatedMeasures(dir_path)



def measureDetectionAndExtraction(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            baseDirectory = Path(root).parents[3]
            exctractedImgsDirectory = "extracted_measures"
            bookDirectory = os.path.basename(os.path.normpath(directory))
            chapterDirectory = os.path.basename(os.path.normpath(Path(root).parents[0]))
            unitDirectory = os.path.basename(os.path.normpath(root))
            fileDirectory = filename[:-4]
            measuresDirectoryPath = os.path.join(baseDirectory ,exctractedImgsDirectory, bookDirectory, chapterDirectory, unitDirectory,fileDirectory)
 
            if not os.path.exists(measuresDirectoryPath):
                imagePath = os.path.join(root, filename)
                image = cv2.imread(imagePath)
                print(f"Analysing File: {imagePath}")
                print("Are you satisfied with the detected contours? (y/n):")
                tabCoords = find_tablature_coordinates(image)
                tabsWithPotentialMargin = plot_the_tablature_coordinates_found_for_verification(tabCoords, image)
                saveMeasures(image, tabsWithPotentialMargin, os.path.basename(os.path.normpath(directory)), root, filename[:-4])
    print("Skew correction process starting..")
    startSkewingProcess(directory)
    print("Measure detection and extraction done!")



if __name__ == '__main__':
    dirname = os.path.dirname(__file__)
    bookDirectory = os.path.join(dirname, '../../books_to_analyze/firstBook')
    measureDetectionAndExtraction(bookDirectory)

