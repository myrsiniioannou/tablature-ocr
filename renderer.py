
import matplotlib.pyplot as plt
import numpy as np
import cv2
import pandas as pd
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader, Template
from domain_model import *
# stem
# beam
file_loader = FileSystemLoader("templates")
env = Environment(loader = file_loader)

header_load = env.get_template("header.xml")
header = header_load.render()


# Measure
measure_load = env.get_template("measure.xml")
measure = measure_load.render(time_signature = timeSignature)



# Horizontal Box
hbox_load = env.get_template("hbox.xml")
hbox = hbox_load.render()
# Vertical Box
vbox_load = env.get_template("vbox.xml")
vbox = vbox_load.render()
# FINAL CONTENT


total_content = header + measure + hbox + measure +vbox
output = base.render(content = total_content)







if __name__ == '__main__':
    chord1 = Chord(positionInMeasure=0, duration='16th', note=60, articulation= "Up", stringFingering='i',)
    chord2 = Chord(positionInMeasure=1, duration='16th', note=62, headerFingering='i', articulation= "Down", hasBox=True, hasAccent=True)
    chord3 = Chord(positionInMeasure=2, duration='eighth', note=66, headerFingering='m', stringFingering='p', slur=1, hasBox=False, hasAccent=False, triplet=1)
    measure1 = Measure(3, [chord1, chord2, chord3])
    measure2 = Measure(4, [chord2, chord3 ,chord1, chord3])
    measure3 = Measure(6, [chord2, chord3 ,chord1, chord3, chord2, chord1])
    measure4 = Measure(2, [chord2, chord1])
    notationpage1 = NotationPage(4, [measure1, measure2, measure3, measure4])
    notationpage2 = NotationPage(5, [measure3, measure2, measure3, measure1, measure4])

    sectionpage1 = SectionPage("Chapter")
    sectionpage2 = SectionPage("Unit")

    page1 = Page(notationpage=notationpage1)
    page2 = Page(notationpage=notationpage2)
    page3 = Page(sectionpage=sectionpage1)
    page4 = Page(sectionpage=sectionpage2)

    book1 = Book(numberOfStrings=6, page = [page1, page2, page3, page4])

    print(json.dumps(book1, indent=3, default=vars))

