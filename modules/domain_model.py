from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
import json

@dataclass
class ChordDuration(str, Enum):
    SIXTEENTH = "16th"
    EIGHTH = "eighth"
    QUARTER = "quarter"
    HALF = "half"
    DOUBLE = "double"
      

@dataclass
class Slur(Enum):
    NO_SLUR = 0
    START = 1
    END = 2


@dataclass
class Triplet(Enum):
    NO_TRIPLET = 0
    FIRST_POSITION = 1
    SECOND_POSITION = 2
    THIRD_POSITION = 3


@dataclass
class Articulation(str, Enum):
    UP = "up"
    DOWN = "down"


@dataclass
class FingeringType(str, Enum):
    P = "p"
    I = "i"
    M = "m"
    A = "a"
    DOT = "dot"
    

@dataclass
class StringFingering:
    string: int
    typeFingering: Optional[FingeringType] = None


@dataclass
class Note:
    noteOnString: Optional[int] = None
    string: Optional[int] = None


@dataclass
class Chord:
    #positionInMeasure: int
    duration: ChordDuration
    hasBox: bool = False
    hasAccent: bool = False
    articulation: Optional[Articulation] = None
    slur: Optional[Slur] = None
    triplet: Optional[Triplet] = None
    note: Optional[Note] = None # Detected
    headerFingering: Optional[FingeringType] = None # Detected
    stringFingering: Optional[StringFingering] = None # Detected

     
@dataclass
class Measure:
    chords: Chord = field(default_factory=list)
    

@dataclass
class NotationPage:
    measures: Measure = field(default_factory=list)


@dataclass
class SectionPage:
    sectionpagetitle: str


@dataclass
class Page:
    sectionpage: Optional[SectionPage] = None
    notationpage: Optional[NotationPage] = None


@dataclass
class Book:
    numberofstrings: int
    pages: Page = field(default_factory=list)


if __name__ == '__main__':
    
    # Testing
    chord1 = Chord(duration=ChordDuration.SIXTEENTH, note=1, articulation= "Up", stringFingering= StringFingering(string=1, typeFingering=FingeringType("p")))


    chord2 = Chord(duration=ChordDuration.QUARTER, note=2, headerFingering=FingeringType.I, articulation= Articulation.DOWN, hasBox=True, hasAccent=True, stringFingering=StringFingering(string=1, typeFingering=FingeringType("m")))
    chord3 = Chord(duration=ChordDuration.EIGHTH, note=3, headerFingering='m', slur=1, hasBox=False, hasAccent=False, triplet=1, stringFingering= StringFingering(string=2, typeFingering=FingeringType("i")))
    measure1 = Measure([chord1, chord2, chord3])
    measure2 = Measure([chord2, chord3 ,chord1, chord3])
    measure3 = Measure([chord2, chord3 ,chord1, chord3, chord2, chord1])
    measure4 = Measure([chord2, chord1])
    notationpage1 = NotationPage([measure1, measure2, measure3, measure4])
    notationpage2 = NotationPage([measure3, measure2, measure3, measure1, measure4])

    sectionpage1 = SectionPage("Chapter 1")
    sectionpage2 = SectionPage("Unit 2")

    page1 = Page(notationpage=notationpage1)
    page2 = Page(notationpage=notationpage2)
    page3 = Page(sectionpage=sectionpage1)
    page4 = Page(sectionpage=sectionpage2)

    book1 = Book(numberOfStrings=6, pages = [page1, page2, page3, page4])

    #print(book1)
    print(json.dumps(book1, indent=3, default=vars))
