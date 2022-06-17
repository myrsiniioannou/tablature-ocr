import os
import cv2
import matplotlib.pyplot as plt

def subpart_analysis(path_to_img, denoise, templateWindowSize = 15):
    print(f"Analysing File: {path_to_img}")
    image = cv2.imread(path_to_img)
    new_image = image.copy()
    if denoise:
        print("Adding fast denoising...")
        fast_denoise = cv2.fastNlMeansDenoisingColored(new_image,None,200,100,50,templateWindowSize)
        gray = cv2.cvtColor(fast_denoise, cv2.COLOR_BGR2GRAY)
    else:
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
    image = cv2.resize(img, (int(width*scaleDown), int(height*scaleDown)))
    return image


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
    
def find_tablature_coordinates(img):
    tablatureCoordinates = subpart_analysis(img, False)
    response = keyResponse()
    # If the image's contours are not good enough, try fast denoise
    if response == ord('n'):
        tablatureCoordinates = retryWithFastDenoise(response, img)
    sortedTabCoords = sort_tablature_coordinates(tablatureCoordinates)
    return sortedTabCoords

def sort_tablature_coordinates(tabCoordinates):
    sorted_tablature_coords = sorted(tabCoordinates, key=lambda d: d['y'])
    for i in range(0, len(sorted_tablature_coords), 2):
        if sorted_tablature_coords[i]['x']>sorted_tablature_coords[i+1]['x']:
            sorted_tablature_coords[i], sorted_tablature_coords[i+1]  = sorted_tablature_coords[i+1], sorted_tablature_coords[i]
    return sorted_tablature_coords





def plot_the_tablature_coordinates_found_for_verification(tabs, path_to_img):
    marginConfirmation = "y"
    margin = 0
    while marginConfirmation == "y":
        img = cv2.imread(path_to_img)
        contrast = 5 # Contrast control (1.0-3.0)
        brightness = -600 # Brightness control (0-100)
        image = cv2.addWeighted(img, contrast, img, 0, brightness)
        fig = plt.figure(figsize=(10, 20))
        tab = []
        for index, i in enumerate(tabs):
            tab.append(image[i["y"] - margin : i["y"] + i["h"] + margin, i["x"] - margin : i["x"] + i["w"] + margin])
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
                break
            except:
                print("Incorrect input. Try again")
        if marginConfirmation == "y":
            while True:
                try:
                    margin = int(input("Provide Margin:"))
                    break
                except:
                    print("That's not an integer. Try again")
    return tab







if __name__ == '__main__':
    directory = r"C:\Users\merse\Desktop\Tablature OCR\code\books_to_analyze\book1"
    for root, dirs, files in os.walk(directory):
        folderName = os.path.basename(os.path.normpath(root))
        if folderName.startswith('chapter'):
            #print("Chapter")
            pass
        elif folderName.startswith('unit'):
            #print("Unit")
            pass
        # Iterate through your pages
        for filename in files:
            print("Are you satisfied with the detected contours? (y/n):")
            imagePath = os.path.join(root, filename)
            # Find subparts' coordinates
            tabCoords = find_tablature_coordinates(imagePath)
            print(tabCoords)
            # Verify the findings and add potential margin if needed
            tabsWithPotentialMargin = plot_the_tablature_coordinates_found_for_verification(tabCoords, imagePath)
            print(tabsWithPotentialMargin)






            ############## TRYING TO ADD MARGINS TO TABLATURE COORDS
            #### SAVE MEASURES
            #### SKEW MEASURES
            #### SAVE MEASURES
            
            # Analyse each measure
            # Add it to page/book
            