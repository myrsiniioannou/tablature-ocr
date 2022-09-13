import json

with open(r"C:\Users\merse\Desktop\Tablature OCR\book_outputs\book1.json", 'r') as fcc_file:
    fcc_data = json.load(fcc_file)

print(fcc_data)