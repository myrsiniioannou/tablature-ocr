        For each chordIndex/Position (in df), it must create a chord object
        chord = Chord(duration = durationDecoding(UserInputData["chordDurationInteger"][chordIndex]),
                       hasBox = hasBoxOrAccentDecoding(UserInputData["hasBox"][chordIndex]),
                       hasAccent = hasBoxOrAccentDecoding(UserInputData["hasAccent"][chordIndex]),
                       articulation = articulationDecoding(UserInputData["articulation"][chordIndex]),
                       slur = UserInputData["slur"][chordIndex],
                       triplet = UserInputData["triplet"][chordIndex],
                       note = Note(noteOnString=noteDecoding(mdf,chordIndex), string=noteStringDecoding(mdf,chordIndex)),
                       headerFingering = FingeringType(fingeringDecoding(mdf, chordIndex, headerOrNot=True)),
                       stringFingering = StringFingering(string=stringFingeringDecoding(mdf, chordIndex),
                                                        typeFingering=FingeringType(fingeringDecoding(mdf, chordIndex, headerOrNot=False))))
        
        measure.append(chord)
        print(FingeringType(FingeringType.NO_FINGERING))