import pandas as pd
from dataclasses import dataclass

#obj = pd.read_pickle(r'C:\Users\merse\Desktop\Tablature OCR\books_to_analyze\firstBookTEST\chapter01\unit01\01.pkl')
#print(obj)


# @dataclass
# class Chapter:
#     number : int
#     def increment(self):
#         self.number += 1
#         return self.number

# @dataclass
# class Unit:
#     number : int    
#     def increment(self):
#         self.number += 1
#         return self.number



# currentUnit = Unit(0)
# currentChapter = Chapter(0)

# currentUnit.increment()
# currentChapter.increment()
# print(currentUnit.number)
# print(currentChapter.number)


# @dataclass
# class InventoryItem:
#     name: str
#     unit_price: float
#     quantity_on_hand: int = 0

#     def total_cost(self) -> float:
#         return self.unit_price * self.quantity_on_hand

# item = InventoryItem("Skato", 10.00 , 200)

# print(item.total_cost())


first_name = "Emma"
second_name = "Watson"

print ("The first name: " + str(first_name))
print ("The second name: " + str(second_name))

list = [first_name, second_name]
string = " ".join(list)

print ("The appended string: " + string)