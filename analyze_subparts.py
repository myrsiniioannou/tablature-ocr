import os
import cv2


def load_model():
    model_path = r"C:\Users\merse\Desktop\Tablature OCR\model\model2.pth"
    model = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    return model

def keyResponse():
    while True:
        k = cv2.waitKey(0) & 0xFF
        if k == ord('y') or k == ord('n'):
            cv2.destroyAllWindows()
            break
    return k

def subpart_analysis(path_to_img, denoise, templateWindowSize = 21):
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
    scaleDown = 0.35
    height, width = with_contours.shape[:2]
    imS = cv2.resize(with_contours, (int(width*scaleDown), int(height*scaleDown)))
    cv2.imshow('', imS)
    key = keyResponse()
    return key, tablature_coords


def templateWindowSizeInput():
    while True:
        try:
            tempWindowSize = int(input("Provide Template Window Size (~=21):"))
            break
        except:
            print("That's not an integer. Try again")
    return tempWindowSize
    

def retryWithFastDenoise(keyboardResponse, img):
    fistIteration = True
    templateWindowSize = 21
    while keyboardResponse == ord('n'):
        if fistIteration:
            fistIteration = False
        else:
            templateWindowSize = templateWindowSizeInput()
        keyboardResponse, tabCoords = subpart_analysis(img, True, templateWindowSize)
    return keyboardResponse, tabCoords





#if __name__ == '__main__':
#    directory = r"C:\Users\merse\Desktop\Tablature OCR\code\books_to_analyze\book1"
#    for root, dirs, files in os.walk(directory):
#        folderName = os.path.basename(os.path.normpath(root))
#        if folderName.startswith('chapter'):
#            #print("Chapter")
#            pass
#        elif folderName.startswith('unit'):
#            #print("Unit")
#            pass
#        # Iterate through your pages
#        for filename in files:
#            imagePath = os.path.join(root, filename)
#            response, tablatureCoordinates = subpart_analysis(imagePath, False)
#            # If image's boundaries are not good enough, try fast denoise
#            if response == ord('n'):
#                response, tablatureCoordinates = retryWithFastDenoise(response, imagePath)