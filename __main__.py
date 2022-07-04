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
    #bookDirectory = r"../books_to_analyze/book1"
    #measureDetectionAndExtraction(bookDirectory)
    
    model_path = r"../model/model2.pth"
    trainedModel = core.Model.load(model_path, ["p", "i", "m", "a", "1", "2", "3", "4"])
    extractedBookDirectory = r"C:\Users\merse\Desktop\Tablature OCR\extracted_measures\book1"
    numberOfStrings = 6
    measureAnalysis(extractedBookDirectory, trainedModel, numberOfStrings)

    # RENDER TO TEMPLATES

    
    print("Book Done!")
