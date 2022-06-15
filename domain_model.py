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
    START = 1
    END = 2

@dataclass
class Triplet(Enum):
    FIRST_POSITION = 1
    SECOND_POSITION = 2
    THIRD_POSITION = 3

@dataclass
class Articulation(str, Enum):
    UP = "Up"
    DOWN = "Down"

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
    typeFingering: FingeringType

@dataclass
class Chord:
    #positionInMeasure: int
    duration: ChordDuration
    hasBox: bool = False
    hasAccent: bool = False
    note: Optional[int] = None
    headerFingering: Optional[FingeringType] = None
    articulation: Optional[Articulation] = None
    stringFingering: Optional[StringFingering] = None
    slur: Optional[Slur] = None
    triplet: Optional[Triplet] = None      

@dataclass
class Measure:
    chords: Chord = field(default_factory=list)
    
@dataclass
class NotationPage:
    measures: Measure = field(default_factory=list)

@dataclass
class SectionPageTitle(str, Enum):
    CHAPTER = "Chapter"
    UNIT = "Unit"

@dataclass
class SectionPage:
    sectionpagetitle: SectionPageTitle

@dataclass
class Page:
    sectionpage: Optional[SectionPage] = None
    notationpage: Optional[NotationPage] = None

@dataclass
class Book:
    numberOfStrings: int
    pages: Page = field(default_factory=list)


if __name__ == '__main__':
    chord1 = Chord(duration='16th', note=1, articulation= "Up", stringFingering='i',)
    chord2 = Chord(duration='16th', note=2, headerFingering=FingeringType.I, articulation= "Down", hasBox=True, hasAccent=True)
    chord3 = Chord(duration='eighth', note=3, headerFingering='m', stringFingering='p', slur=1, hasBox=False, hasAccent=False, triplet=1)
    measure1 = Measure([chord1, chord2, chord3])
    measure2 = Measure([chord2, chord3 ,chord1, chord3])
    measure3 = Measure([chord2, chord3 ,chord1, chord3, chord2, chord1])
    measure4 = Measure([chord2, chord1])
    notationpage1 = NotationPage([measure1, measure2, measure3, measure4])
    notationpage2 = NotationPage([measure3, measure2, measure3, measure1, measure4])

    sectionpage1 = SectionPage("Chapter")
    sectionpage2 = SectionPage("Unit")

    page1 = Page(notationpage=notationpage1)
    page2 = Page(notationpage=notationpage2)
    page3 = Page(sectionpage=sectionpage1)
    page4 = Page(sectionpage=sectionpage2)

    book1 = Book(numberOfStrings=6, pages = [page1, page2, page3, page4])

    print(json.dumps(book1, indent=3, default=vars))

