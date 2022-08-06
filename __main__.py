import sys
sys.path.append('modules')
from measure_detection_and_extraction import *
from domain_model import *
from measure_analysis import *

from detecto import core, utils, visualize
from detecto.visualize import show_labeled_image, plot_prediction_grid
from torchvision import transforms
import torch
import os


if __name__ == '__main__':
    # 1st Step - Exctract Measures
    bookDirectory = r"../books_to_analyze/book1"
    #measureDetectionAndExtraction(bookDirectory)
    
    
    # 2nd Step - Analyze measures and create dfs for each one
    model_path = r"../model/model2.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings)






    # 1ST TASK - 3rd Step - Parse the extracted dfs in csv format
    # 2ND TASK -  4th Step Add Section Pages
    parseBook(bookDirectory)
    
    # 3RD TASK - 5th Step - Render in xml
    # 4TH TASK - 6th Step - Retrain
    

    


    
    print("Book Done!")
