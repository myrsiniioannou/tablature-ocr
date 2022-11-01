
col = 5


for idx in range(0,20):
    print(idx, abs(idx%col - idx)//col + 1)