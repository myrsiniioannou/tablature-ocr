import sys
sys.path.append('modules')
from find_subparts import *
from domain_model import *


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
            print("Are you satisfied with the detected contours? (y/n):")
            imagePath = os.path.join(root, filename)
            # Find subparts' coordinates
            tabCoords = find_tablature_coordinates(imagePath)
            # Verify the findings and add potential margin if needed
            tabsWithPotentialMargin = plot_the_tablature_coordinates_found_for_verification(tabCoords, imagePath)

            
if __name__ == '__main__':
    main()