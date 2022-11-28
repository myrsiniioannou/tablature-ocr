from dataclasses import dataclass, replace
import copy

# @dataclass
# class wholePageRepeater:
#     dfList: list
#     def updateList(self, value):
#         self.dfList.append(value)
#     def eraseList(self):
#         self.dfList = []

# list0fHeadersToRepeat = wholePageRepeater([1])
# print(list0fHeadersToRepeat.dfList)
# list0fHeadersToRepeat = wholePageRepeater([])
# print(list0fHeadersToRepeat.dfList)

# def callIt():
#     for i in range(4,10):
#         list0fHeadersToRepeat.updateList(i)
#     print("CALL IT")
#     print(list0fHeadersToRepeat.dfList)

# list0fHeadersToRepeat.eraseList()
# print(list0fHeadersToRepeat.dfList)

# for i in range(1,20):
#     list0fHeadersToRepeat.updateList(i)
# print(list0fHeadersToRepeat.dfList)
# print(list0fHeadersToRepeat.dfList[8])
# callIt()



class wholePageDFlist:
    dfList = list
    def updateList(self, value):
        self.dfList.append(value)
    def eraseList(self):
        self.dfList = []


list0fWholePageHeadersToRepeat =  wholePageDFlist()
print(list0fWholePageHeadersToRepeat.dfList)
list0fWholePageHeadersToRepeat.dfList=[1]
print(list0fWholePageHeadersToRepeat.dfList)
list0fWholePageHeadersToRepeat.updateList(4)
print(list0fWholePageHeadersToRepeat.dfList)