from analyze_subparts import *



"""
MAKE DIRECTORY LIKE THIS:
area_finder
|   readme.md
|   __main__.py
|   
+---src
|   |   circle.py
|   |   rectangle.py
|   |   square.py
|   |   __init__.py
|   |   
"""



def main ():
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
            imagePath = os.path.join(root, filename)
            response, tablatureCoordinates = subpart_analysis(imagePath, False)
            # If image's boundaries are not good enough, try fast denoise
            if response == ord('n'):
                response, tablatureCoordinates = retryWithFastDenoise(response, imagePath)
            
            
if __name__ == '__main__':
    main()